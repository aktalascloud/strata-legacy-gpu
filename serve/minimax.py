"""MiniMax-M3.1 native stream over Strata's declared-tool and quoting boundaries.

Wire/schema reference: Project Maya26aacb6b (MIT), MiniMax's own template. Plain text is
never fed back into a different model's tag parser. Truncated invokes remain unfinished.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from serve.frontend import Event, OutputParser, ToolCall

NS = "]<]minimax[>["
THINK, THINK_END = "<mm:think>", "</mm:think>"
LEVELS = ("low", "medium", "high", "xhigh", "max")
MAX_DEPTH, NAME_LIMIT = 64, 600


def template_kwargs(kwargs):
    """MiniMax's own template controls; author presets remain exclusive to their qualified models."""
    out = dict(kwargs)
    if out.pop("author_mode", None) not in (None, "", "default"):
        raise ValueError("author modes require a qualified DavidAU model")
    off = out.pop("enable_thinking", None) is False
    if off:
        out["thinking_mode"] = "disabled"
        out.pop("reasoning_effort", None)
    elif out.get("reasoning_effort") is not None and out["reasoning_effort"] not in LEVELS:
        raise ValueError("MiniMax reasoning_effort must be low, medium, high, xhigh or max")
    if out.get("thinking_mode") not in (None, "adaptive", "enabled", "disabled"):
        raise ValueError("unknown native MiniMax thinking mode")
    return out


def to_minimax_force(force):
    if not force:
        return force
    head = NS + "<tool_call>"
    marker = "<function="
    if marker not in force:
        return head
    name = force.split(marker, 1)[1]
    complete = name.endswith(">\n")
    if complete:
        name = name[:-2]
    if len(name) > NAME_LIMIT or any(c in name for c in '<>"'):
        raise ValueError("MiniMax forced tool name cannot be represented")
    return head + NS + '<invoke name="' + name + ('">' if complete else '')


def resolve(schema, defs, seen=()):
    while isinstance(schema, dict) and isinstance(schema.get("$ref"), str):
        ref = schema["$ref"]
        if ref in seen or len(seen) >= MAX_DEPTH or not ref.startswith(("#/$defs/", "#/definitions/")):
            return {}
        seen = (*seen, ref)
        schema = defs.get(ref.rsplit("/", 1)[-1], {})
    return schema if isinstance(schema, dict) else {}


def may_be_string(schema, defs=None, depth=0):
    if depth >= MAX_DEPTH:
        return False
    schema = resolve(schema, defs or {})
    typ = schema.get("type")
    if typ == "string" or isinstance(typ, list) and "string" in typ:
        return True
    if any(isinstance(x, str) for x in schema.get("enum", []) or []) or isinstance(schema.get("const"), str):
        return True
    for name in ("anyOf", "oneOf"):
        if any(may_be_string(s, defs, depth + 1) for s in schema.get(name, []) or []):
            return True
    parts = schema.get("allOf") or []
    return bool(parts) and all(may_be_string(s, defs, depth + 1) for s in parts)


def scalar(text):
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return text
    # Reject non-standard numbers rather than emitting invalid JSON tool arguments.
    json.dumps(value, allow_nan=False)
    return value


def container_kind(schema, defs):
    typ = resolve(schema, defs).get("type")
    types = typ if isinstance(typ, list) else [typ]
    containers = [k for k in ("array", "object") if k in types]
    return containers[0] if len(containers) == 1 else None


@dataclass
class _Value:
    name: str
    schema: dict
    string: bool
    parts: list[str] = field(default_factory=list)
    children: list = field(default_factory=list)


class MiniMaxOutputParser(OutputParser):
    """Native namespaces, repeated thinking, streamed strings and complete declared invokes."""

    thinking_end = THINK_END

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_calls = False
        self.block_had_call = False
        self.header = []
        self.values = []
        self.current = None
        self.raw = []
        self.literal = []
        self.defs = {}
        self._events = []
        self._streamed = False
        self.call_role = None

    @property
    def clean(self):
        return not (self.buf or self.header or self.values or self.current or self.literal or self.pending)

    def _text(self, text):
        if not text:
            return
        if self.current:
            self.raw.append(text)
        if self.values:
            self.values[-1].parts.append(text)
            if len(self.values) == 1 and self.values[0].string and self._streamed:
                self._args(json.dumps(text, ensure_ascii=False)[1:-1])
        elif self.literal:
            self._emit_text(text)
        elif self.current:
            if text.strip():
                raise ValueError("text outside a MiniMax parameter")
        elif self.in_calls:
            self.header.append(text)
        elif self.pending and self.state == "reasoning" and not text.strip():
            self.pending[-1][0] += text
        else:
            if self.pending:
                self._events += self._release(False)
            self._emit_text(text)

    def _emit_text(self, text):
        if text:
            channel = "reasoning" if self.state in ("reasoning", "rcall") else "content"
            self._events.append(Event(channel, self._track(text)))

    def _args(self, text):
        if self._streamed and text:
            self._events.append(Event("tool_args", text, call=self.current))

    @staticmethod
    def _tag_name(tag):
        closing = tag.startswith("</")
        body = tag[2:-1] if closing else tag[1:-1]
        name = body.split(None, 1)[0] if body.strip() else ""
        if not name or len(name) > NAME_LIMIT or re.search(r'[\s<>/"=]', name):
            raise ValueError("invalid MiniMax tag name")
        return name, closing

    def _new_value(self, name, schema):
        if len(self.values) >= MAX_DEPTH:
            raise ValueError("MiniMax value nesting exceeds 64")
        self.values.append(_Value(name, schema, may_be_string(schema, self.defs)))

    def _end_value(self):
        node = self.values.pop()
        text = "".join(node.parts)
        if node.string:
            value = text
        elif node.children:
            if text.strip():
                raise ValueError("mixed text and structured MiniMax value")
            typ = container_kind(node.schema, self.defs)
            if typ == "array" and not all(k == "item" for k, _ in node.children):
                raise ValueError("non-item in MiniMax array")
            if typ != "object" and all(k == "item" for k, _ in node.children):
                value = [v for _, v in node.children]
            else:
                if len({k for k, _ in node.children}) != len(node.children):
                    raise ValueError("duplicate MiniMax object key")
                value = dict(node.children)
        else:
            typ = container_kind(node.schema, self.defs)
            value = [] if typ == "array" and not text.strip() else {} if typ == "object" and not text.strip() else scalar(text)
        if self.values:
            self.values[-1].children.append((node.name, value))
        else:
            self.current.arguments[node.name] = value
            self._args('"' if node.string else json.dumps(value, ensure_ascii=False, allow_nan=False))

    def _tag(self, tag):
        raw = NS + tag
        try:
            name, closing = self._tag_name(tag)
        except ValueError:
            if not self.literal:
                raise
            self._emit_text(raw)
            return
        if self.literal:
            self._emit_text(raw)
            if closing and name == self.literal[-1]:
                self.literal.pop()
                if not self.literal:
                    self.in_calls = False
            elif not closing:
                if len(self.literal) >= MAX_DEPTH:
                    raise ValueError("MiniMax literal nesting exceeds 64")
                self.literal.append(name)
            return
        if self.current:
            self.raw.append(raw)
        if self.values:
            node = self.values[-1]
            if closing and name == node.name:
                self._end_value()
            elif node.string:
                node.parts.append(raw)
                if len(self.values) == 1:
                    self._args(json.dumps(raw, ensure_ascii=False)[1:-1])
            elif closing:
                raise ValueError("mismatched MiniMax value closer")
            else:
                schema = resolve(node.schema, self.defs)
                child = schema.get("items", {}) if name == "item" and container_kind(schema, self.defs) == "array" else (schema.get("properties") or {}).get(name, {})
                self._new_value(name, child)
            return
        if name == "tool_call":
            if closing:
                if not self.in_calls:
                    self._text(raw)
                    return
                if self.current:
                    raise ValueError("MiniMax invoke did not close")
                self.in_calls = False
                if self.pending and self.state == "reasoning":
                    self.pending[-1][0] += "".join(self.header) + raw
                    if "".join(self.header).strip():
                        self._events += self._release(False)
                elif not self.block_had_call:
                    self._emit_text("".join(self.header) + raw)
                elif "".join(self.header).strip():
                    self._emit_text("".join(self.header))
                self.header = []
            else:
                if self.in_calls:
                    raise ValueError("nested MiniMax tool-call block")
                allowed = self._opener_ok() if self.state == "reasoning" else not self._in_code()
                self.in_calls = True
                self.block_had_call = False
                if not allowed:
                    self.literal = [name]
                    self._emit_text(raw)
                else:
                    self.header = [raw]
            return
        if name == "invoke" and self.in_calls:
            if closing:
                if self.current is None:
                    raise ValueError("MiniMax invoke did not open")
                call, source = self.current, "".join(self.raw)
                self._args("}")
                self.current = None
                self.scall = None
                self._streamed = False
                self.state = self.call_role
                self.call_role = None
                if self.state == "reasoning":
                    self.pending.append([source, call])
                else:
                    self._events.append(Event("tool_call", call=call))
                self.raw = []
                return
            if self.current:
                raise ValueError("nested MiniMax invoke")
            match = re.fullmatch(r'<invoke\s+name="([^"<>]+)"\s*>', tag)
            tool = self.aliases.get(match[1], match[1]) if match else None
            if tool is None or tool not in self.schemas:
                self.unread += 1
                if tool and len(self.unread_names) < 5:
                    self.unread_names.append(tool[:80])
                self._emit_text("".join(self.header) + raw)
                self.header = []
                self.literal = ["tool_call", "invoke"]
                return
            self.current = ToolCall(name=tool, arguments={})
            self.block_had_call = True
            self.call_role = self.state
            self.raw = self.header + [raw]
            self.header = []
            spec = self.schemas[tool].get("parameters") or {}
            self.defs = {**(spec.get("definitions") or {}), **(spec.get("$defs") or {})}
            self._streamed = self.stream_tools and self.state == "content"
            self.state = "rcall" if self.call_role == "reasoning" else "call"
            if self._streamed:
                self.scall = self.current
                self._events.append(Event("tool_start", call=self.current))
                self._args("{")
            return
        if self.current and not closing:
            if name in self.current.arguments:
                raise ValueError("duplicate MiniMax parameter")
            props = (self.schemas[self.current.name].get("parameters") or {}).get("properties") or {}
            self._args(("," if self.current.arguments else "") + json.dumps(name) + ":")
            self._new_value(name, props.get(name, {}))
            if self.values[0].string:
                self._args('"')
            return
        self._text(raw)

    def _think(self, tag):
        if self.values or self.literal or self._in_code():
            self._text(tag)
            return
        if self.current:
            raise ValueError("thinking marker inside MiniMax invoke")
        if tag == THINK_END:
            self._events += self._release(True)
            self.state = "content"
        else:
            self.state = "reasoning"
        self._reset_track()

    def feed(self, delta):
        self._events = []
        self.buf += delta
        marks = (NS, THINK, THINK_END)
        while self.buf:
            if self.values and self.values[-1].string:
                if not self._string_step():
                    break
                continue
            hits = [p for p in (self.buf.find(m) for m in marks) if p >= 0]
            if not hits:
                keep = max((n for m in marks for n in range(1, len(m)) if self.buf.endswith(m[:n])), default=0)
                cut = len(self.buf) - keep
                self._text(self.buf[:cut]);self.buf = self.buf[cut:]
                break
            at = min(hits)
            self._text(self.buf[:at]);self.buf = self.buf[at:]
            if self.buf.startswith((THINK, THINK_END)):
                tag = THINK_END if self.buf.startswith(THINK_END) else THINK
                self.buf = self.buf[len(tag):];self._think(tag)
                continue
            rest = self.buf[len(NS):]
            if not rest:
                break
            if not rest.startswith("<"):
                self._text(NS);self.buf = rest
                continue
            end = rest.find(">")
            if end < 0:
                if len(rest) > 1024:
                    if self.current or self.in_calls and not self.literal:
                        raise ValueError("MiniMax tag exceeds 1024 characters")
                    self._text(NS);self.buf = rest
                    continue
                break
            self.buf = rest[end + 1:];self._tag(rest[:end + 1])
        return self._events

    def _string_step(self):
        """Only its own closer followed by native structure ends a free-form string."""
        marker = NS + '</' + self.values[-1].name + '>'
        at = self.buf.find(marker)
        if at < 0:
            keep = max((n for n in range(1, len(marker)) if self.buf.endswith(marker[:n])), default=0)
            cut = len(self.buf) - keep
            self._text(self.buf[:cut]);self.buf = self.buf[cut:]
            return False
        self._text(self.buf[:at]);self.buf = self.buf[at:]
        tail = self.buf[len(marker):]
        stripped = tail.lstrip()
        if not stripped or NS.startswith(stripped):
            return False
        valid = False
        if stripped.startswith(NS):
            rest = stripped[len(NS):]
            if rest and not rest.startswith('<'):
                self.buf = tail
                self._text(marker)
                return True
            end = rest.find('>')
            if end < 0 and len(rest) <= 1024:
                return False
            if end >= 0:
                try:
                    name, closing = self._tag_name(rest[:end + 1])
                    parent = self.values[-2].name if len(self.values) > 1 else 'invoke'
                    valid = name == parent if closing else name not in ('invoke', 'tool_call')
                except ValueError:
                    pass
        self.buf = tail
        if valid:
            self._tag(marker[len(NS):])
        else:
            self._text(marker)
        return True

    def finish(self, reason=None):
        self._events = []
        rest, self.buf = self.buf, ""
        self._text(rest)
        header, self.header = "".join(self.header), []
        if header:
            if self.pending and self.state == "reasoning":
                self.pending[-1][0] += header
            elif header.strip() or not self.block_had_call:
                self._emit_text(header)
        if self.pending:
            self._events += self._release(reason in (None, "stop") and self.state == "reasoning" and not (self.current or self.literal or header.strip()))
        # No synthetic parameter/invoke closers and no completed call for truncated output.
        if self.current and not self._streamed:
            self._emit_text("".join(self.raw))
        if self.call_role:
            self.state = self.call_role
        self.call_role = None
        self.scall = None
        self.current = None
        self.values = []
        return self._events
