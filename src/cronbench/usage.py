"""Conservative, credential-free normalization of exported token usage.

Canonical input includes cache reads/writes; canonical output includes reasoning.
Those breakdowns are subsets, never additional tokens. Unknown values stay None.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "cache_write_tokens",
    "reasoning_output_tokens",
)
USAGE_FIELDS = (*TOKEN_FIELDS, "request_count")
PROVENANCES = {"measured", "estimated", "unavailable"}


def normalize_usage(usage: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate canonical usage without replacing missing counters with zero.

    This accepts *canonical* counters. Provider-native usage must first go through
    an adapter, because (for example) Anthropic input excludes cache counters.
    """
    raw = dict(usage or {})
    result: dict[str, Any] = {}
    for key in USAGE_FIELDS:
        value = raw.get(key)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{key} must be a nonnegative integer or null")
        result[key] = value
    known = any(result[key] is not None for key in USAGE_FIELDS)
    provenance = raw.get("provenance", "measured" if known else "unavailable")
    if provenance not in PROVENANCES:
        raise ValueError("usage provenance must be measured, estimated, or unavailable")
    if not known:
        provenance = "unavailable"
    result.update(
        provenance=provenance,
        source=raw.get("source"),
        semantics="input_includes_cache;output_includes_reasoning",
        pricing_scope=raw.get("pricing_scope"),
        notes=list(raw.get("notes") or []),
    )
    inp = result["input_tokens"]
    out = result["output_tokens"]
    read = result["cached_input_tokens"]
    write = result["cache_write_tokens"]
    reasoning = result["reasoning_output_tokens"]
    if inp is not None:
        if any(value is not None and value > inp for value in (read, write)):
            raise ValueError("cache counters cannot exceed canonical input_tokens")
        if read is not None and write is not None and read + write > inp:
            raise ValueError("cache read and write counters cannot exceed input_tokens")
    if out is not None and reasoning is not None and reasoning > out:
        raise ValueError("reasoning_output_tokens cannot exceed output_tokens")
    result["total_tokens"] = inp + out if inp is not None and out is not None else None
    return result


def _events(text: str) -> list[dict[str, Any]]:
    """Read JSON or JSONL; ignore diagnostic/non-JSON lines without guessing."""
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    events = []
    for line in text.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def _counter(raw: Mapping[str, Any], key: str) -> int | None:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _sum_known(values: list[int | None]) -> int | None:
    return sum(values) if values and all(v is not None for v in values) else None


def _codex(events: list[dict[str, Any]], source: str) -> dict[str, Any]:
    usages = [
        event["usage"]
        for event in events
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict)
    ]
    if not usages:
        return normalize_usage({"source": source, "notes": ["No documented turn.completed usage found."]})
    fields = {
        key: _sum_known([_counter(usage, key) for usage in usages])
        for key in TOKEN_FIELDS
    }
    return normalize_usage(
        {
            **fields,
            "source": source,
            "provenance": "measured",
            "notes": [
                f"Summed {len(usages)} documented turn.completed usage event(s).",
                "A completed turn is not a known count of model requests.",
                "Unexported cache-write and reasoning counters remain unknown.",
            ],
        }
    )


def _amp_native(raw: Mapping[str, Any]) -> dict[str, Any]:
    read = _counter(raw, "cache_read_input_tokens")
    write = _counter(raw, "cache_creation_input_tokens")
    creation = raw.get("cache_creation")
    if write is None and isinstance(creation, dict):
        write = _sum_known(
            [_counter(creation, "ephemeral_5m_input_tokens"), _counter(creation, "ephemeral_1h_input_tokens")]
        )
    # Amp documents Anthropic-shaped field names, but does not guarantee the
    # inclusive/exclusive meaning across its routed models. Do not infer that
    # semantic guarantee from compatible field names.
    return {
        "input_tokens": None,
        "output_tokens": _counter(raw, "output_tokens"),
        "cached_input_tokens": read,
        "cache_write_tokens": write,
        "reasoning_output_tokens": None,
    }


def _amp(events: list[dict[str, Any]], source: str) -> dict[str, Any]:
    # The terminal result is aggregate usage. Summing it with assistant usage
    # would bill the same tokens twice. Prefer it when available.
    terminal = [
        event["usage"]
        for event in events
        if event.get("type") == "result" and isinstance(event.get("usage"), dict)
    ]
    if terminal:
        native = [_amp_native(terminal[-1])]
        note = "Used terminal result aggregate; did not add assistant usage again."
    else:
        native = []
        for event in events:
            message = event.get("message")
            if event.get("type") == "assistant" and isinstance(message, dict):
                if isinstance(message.get("usage"), dict):
                    native.append(_amp_native(message["usage"]))
        note = f"Summed {len(native)} documented assistant.message.usage event(s)."
    if not native:
        return normalize_usage({"source": source, "notes": ["No documented Amp usage found."]})
    return normalize_usage(
        {
            **{key: _sum_known([item[key] for item in native]) for key in TOKEN_FIELDS},
            "source": source,
            "provenance": "measured",
            "notes": [
                note,
                "Amp input/cache inclusion semantics are not documented across routed models; canonical input remains unknown. Supply a verified canonical import to use an input total.",
                "Amp cache creation TTL breakdown is retained in the original artifact; a single write rate may be insufficient.",
                "Native message count is not a known count of model requests.",
            ],
        }
    )


def _cursor_native(raw: Mapping[str, Any]) -> dict[str, int | None]:
    """Map Cursor CLI camelCase counters to canonical inclusive input.

    Observed `agent --print --output-format stream-json` result.usage fields treat
    `inputTokens` as uncached input alongside separate cache read/write counters.
    Canonical input therefore sums the three disjoint parts when all are present.
    """
    uncached = _counter(raw, "inputTokens")
    read = _counter(raw, "cacheReadTokens")
    write = _counter(raw, "cacheWriteTokens")
    output = _counter(raw, "outputTokens")
    if uncached is not None and read is not None and write is not None:
        inp: int | None = uncached + read + write
    else:
        inp = None
    return {
        "input_tokens": inp,
        "output_tokens": output,
        "cached_input_tokens": read,
        "cache_write_tokens": write,
        "reasoning_output_tokens": None,
    }


def _cursor(events: list[dict[str, Any]], source: str) -> dict[str, Any]:
    # Prefer the terminal result aggregate. Intermediate events may repeat or
    # omit usage; summing them would risk double-counting.
    terminal = [
        event["usage"]
        for event in events
        if event.get("type") == "result" and isinstance(event.get("usage"), dict)
    ]
    if not terminal:
        return normalize_usage(
            {
                "source": source,
                "notes": [
                    "No documented Cursor type=result usage object found.",
                    "Cursor stream schemas vary by CLI version; leave counters unknown rather than inferring.",
                ],
            }
        )
    native = _cursor_native(terminal[-1])
    if all(native[key] is None for key in TOKEN_FIELDS):
        return normalize_usage(
            {
                "source": source,
                "notes": [
                    "Cursor result.usage lacked recognized camelCase token counters.",
                ],
            }
        )
    return normalize_usage(
        {
            **native,
            "source": source,
            "provenance": "measured",
            "notes": [
                f"Used terminal result.usage aggregate from {len(terminal)} result event(s); did not sum intermediate events.",
                "Mapped inputTokens+cacheReadTokens+cacheWriteTokens to canonical input (cache counters are subsets).",
                "Cursor does not export reasoning_output_tokens or request_count in this stream shape.",
                "A display-name model field is not a provider model ID.",
            ],
        }
    )


def extract_cursor_display_model(text: str) -> str | None:
    """Return the first non-empty Cursor stream model display name, if any."""
    for event in _events(text):
        model = event.get("model")
        if isinstance(model, str) and model.strip():
            return model.strip()
    return None


def parse_usage_artifact(text: str, host: str, source: str | None = None) -> dict[str, Any]:
    """Parse only documented shapes, never private sessions or credentials.

    The caller must supply an exported artifact. Unknown host/shape returns
    unavailable usage. A model display name is deliberately not a model ID.
    """
    label = source or f"{host}:exported-artifact"
    events = _events(text)
    name = host.casefold()
    if name in {"codex", "openai-codex"}:
        return _codex(events, label)
    if name == "amp":
        return _amp(events, label)
    if name == "cursor":
        return _cursor(events, label)
    return normalize_usage(
        {
            "source": label,
            "notes": [
                "No documented automatic usage mapping for this host; import canonical measured usage with provenance if available."
            ],
        }
    )
