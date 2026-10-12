#!/usr/bin/env python3
"""Guided review: list hunks, validate a guide, render it to HTML.

Usage: render.py {hunks|check|render} DIR
DIR holds pr.json, diff.patch and (for check/render) guide.json.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

STATUSES = ("added", "changed", "removed", "unchanged")
EDGE_KINDS = ("call", "http", "writeback", "rewired")
SEQ_KINDS = ("call", "return", "async", "http")
SEQ_COLOUR = {"added": "add", "changed": "chg", "removed": "del"}
NAME_W, SUB_W, TAG_W = 7.6, 6.6, 6.4
STATUS_PREFIX = {"added": "+ ", "changed": "~ ", "removed": "− ", "unchanged": ""}
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


@dataclass
class Line:
    kind: str
    old: int | None
    new: int | None
    text: str


@dataclass
class Hunk:
    header: str
    context: str
    lines: list[Line] = field(default_factory=list)

    def count(self, kind: str) -> int:
        return sum(1 for line in self.lines if line.kind == kind)


@dataclass
class FileDiff:
    path: str
    old_path: str
    status: str = "modified"
    binary: bool = False
    hunks: list[Hunk] = field(default_factory=list)

    def count(self, kind: str) -> int:
        return sum(h.count(kind) for h in self.hunks)


def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur: FileDiff | None = None
    hunk: Hunk | None = None
    old_no = new_no = old_left = new_left = 0
    for raw in text.split("\n"):
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.*) b/(.*)$", raw)
            a, b = (m.group(1), m.group(2)) if m else (raw, raw)
            cur = FileDiff(path=b, old_path=a)
            files.append(cur)
            hunk = None
            continue
        if cur is None:
            continue
        m = HUNK_RE.match(raw)
        if m and hunk is None:
            old_no, new_no = int(m[1]), int(m[3])
            old_left = int(m[2]) if m[2] is not None else 1
            new_left = int(m[4]) if m[4] is not None else 1
            hunk = Hunk(header=raw, context=m[5].strip())
            cur.hunks.append(hunk)
            continue
        if hunk is None:
            if raw.startswith("new file mode"):
                cur.status = "added"
            elif raw.startswith("deleted file mode"):
                cur.status = "deleted"
            elif raw.startswith("rename from "):
                cur.old_path = raw[len("rename from "):]
                cur.status = "renamed"
            elif raw.startswith("rename to "):
                cur.path = raw[len("rename to "):]
            elif raw.startswith("Binary files") or raw.startswith("GIT binary patch"):
                cur.binary = True
            continue
        if raw.startswith("\\"):
            continue
        if raw.startswith("+"):
            hunk.lines.append(Line("add", None, new_no, raw[1:]))
            new_no += 1
            new_left -= 1
        elif raw.startswith("-"):
            hunk.lines.append(Line("del", old_no, None, raw[1:]))
            old_no += 1
            old_left -= 1
        else:
            hunk.lines.append(Line("ctx", old_no, new_no, raw[1:]))
            old_no += 1
            new_no += 1
            old_left -= 1
            new_left -= 1
        if old_left <= 0 and new_left <= 0:
            hunk = None
    return files


def load(directory: Path) -> tuple[dict, list[FileDiff]]:
    pr = json.loads((directory / "pr.json").read_text())
    files = parse_diff((directory / "diff.patch").read_text())
    return pr, files


def cmd_hunks(directory: Path) -> int:
    _, files = load(directory)
    for f in files:
        kind = "binary" if f.binary else f.status
        print(f"{f.path} ({kind}, +{f.count('add')} -{f.count('del')})")
        for i, h in enumerate(f.hunks, 1):
            print(f"  #{i} {h.header}  (+{h.count('add')} -{h.count('del')})")
    return 0


def check(guide: dict, files: list[FileDiff]) -> list[str]:
    errors: list[str] = []
    if not isinstance(guide.get("overview"), str) or not guide["overview"].strip():
        errors.append("overview: must be a non-empty string")
    steps = guide.get("steps")
    if not isinstance(steps, list) or not steps or not all(isinstance(s, str) for s in steps):
        errors.append("steps: must be a non-empty list of strings")
    chapters = guide.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        return errors + ["chapters: must be a non-empty list"]

    by_path = {f.path: f for f in files}
    claims: dict[str, list[tuple[int, list[int] | None]]] = {}
    for ci, ch in enumerate(chapters, 1):
        where = f"chapters[{ci}]"
        for key in ("title", "summary"):
            if not isinstance(ch.get(key), str) or not ch[key].strip():
                errors.append(f"{where}.{key}: must be a non-empty string")
        if "note" in ch and not isinstance(ch["note"], str):
            errors.append(f"{where}.note: must be a string when present")
        if "collapsed" in ch and not isinstance(ch["collapsed"], bool):
            errors.append(f"{where}.collapsed: must be a boolean when present")
        entries = ch.get("files")
        if not isinstance(entries, list) or not entries:
            errors.append(f"{where}.files: must be a non-empty list")
            continue
        for entry in entries:
            path = entry.get("path") if isinstance(entry, dict) else None
            if path not in by_path:
                errors.append(f"{where}.files: unknown path {path!r}")
                continue
            hunks = entry.get("hunks")
            if hunks is not None and (
                not isinstance(hunks, list) or not hunks or not all(isinstance(i, int) for i in hunks)
            ):
                errors.append(f"{where}.files[{path}].hunks: must be a non-empty list of integers")
                continue
            claims.setdefault(path, []).append((ci, hunks))

    for f in files:
        got = claims.get(f.path)
        if not got:
            errors.append(f"unassigned file: {f.path}")
            continue
        if len(got) == 1 and got[0][1] is None:
            continue
        if any(h is None for _, h in got):
            errors.append(f"{f.path}: assigned whole and also split, or whole more than once (chapters {[c for c, _ in got]})")
            continue
        seen: dict[int, int] = {}
        for ci, hunks in got:
            for i in hunks or []:
                if not 1 <= i <= len(f.hunks):
                    errors.append(f"{f.path}: hunk #{i} out of range 1..{len(f.hunks)} (chapter {ci})")
                elif i in seen:
                    errors.append(f"{f.path}: hunk #{i} in chapters {seen[i]} and {ci}")
                else:
                    seen[i] = ci
        missing = [i for i in range(1, len(f.hunks) + 1) if i not in seen]
        if missing:
            errors.append(f"{f.path}: hunks {missing} not in any chapter")

    flow = guide.get("flow")
    if not isinstance(flow, dict):
        return errors + ["flow: must be an object"]
    nodes = flow.get("nodes")
    edges = flow.get("edges")
    if not isinstance(nodes, list) or not nodes:
        return errors + ["flow.nodes: must be a non-empty list"]
    if not isinstance(edges, list):
        return errors + ["flow.edges: must be a list"]
    ids: set[str] = set()
    for n in nodes:
        nid = n.get("id") if isinstance(n, dict) else None
        if not isinstance(nid, str) or nid in ids:
            errors.append(f"flow.nodes: missing or duplicate id {nid!r}")
            continue
        ids.add(nid)
        if not isinstance(n.get("label"), str) or not n["label"]:
            errors.append(f"flow.nodes[{nid}].label: must be a non-empty string")
        if n.get("status") not in STATUSES:
            errors.append(f"flow.nodes[{nid}].status: must be one of {STATUSES}")
        chapter = n.get("chapter")
        if chapter is not None and (not isinstance(chapter, int) or not 1 <= chapter <= len(chapters)):
            errors.append(f"flow.nodes[{nid}].chapter: must be 1..{len(chapters)} when present")
        if n.get("status") != "unchanged" and chapter is None:
            errors.append(f"flow.nodes[{nid}]: changed node needs a chapter")
        errors += check_box(n, f"flow.nodes[{nid}]")
        if "focal" in n and not isinstance(n["focal"], bool):
            errors.append(f"flow.nodes[{nid}].focal: must be a boolean when present")
    if sum(1 for n in nodes if isinstance(n, dict) and n.get("focal") is True) > 2:
        errors.append("flow.nodes: at most 2 nodes may be focal")
    for e in edges:
        if not isinstance(e, dict) or e.get("from") not in ids or e.get("to") not in ids:
            errors.append(f"flow.edges: edge {e!r} must reference node ids")
        elif "label" in e and not isinstance(e["label"], str):
            errors.append(f"flow.edges: label of {e!r} must be a string")
        if isinstance(e, dict) and e.get("kind", "call") not in EDGE_KINDS:
            errors.append(f"flow.edges: kind of {e!r} must be one of {EDGE_KINDS}")
    if "tree" in guide:
        errors += check_tree(guide["tree"], len(chapters))
    if "sequence" in guide:
        errors += check_sequence(guide["sequence"], len(chapters))
    return errors


def check_sequence(seq: dict, chapters: int) -> list[str]:
    if not isinstance(seq, dict):
        return ["sequence: must be an object"]
    errors: list[str] = []
    if "title" in seq and (not isinstance(seq["title"], str) or not seq["title"]):
        errors.append("sequence.title: must be a non-empty string when present")
    actors = seq.get("actors")
    if not isinstance(actors, list) or not 2 <= len(actors) <= 5:
        return errors + ["sequence.actors: must be a list of 2-5 actors"]
    ids: set[str] = set()
    for a in actors:
        aid = a.get("id") if isinstance(a, dict) else None
        if not isinstance(aid, str) or not aid or aid in ids:
            errors.append(f"sequence.actors: missing or duplicate id {aid!r}")
            continue
        ids.add(aid)
        if not isinstance(a.get("label"), str) or not a["label"]:
            errors.append(f"sequence.actors[{aid}].label: must be a non-empty string")
        errors += check_box(a, f"sequence.actors[{aid}]")
    messages = seq.get("messages")
    if not isinstance(messages, list) or not 1 <= len(messages) <= 12:
        return errors + ["sequence.messages: must be a list of 1-12 messages"]
    for i, m in enumerate(messages, 1):
        at = f"sequence.messages[{i}]"
        if not isinstance(m, dict):
            errors.append(f"{at}: must be an object")
            continue
        for key in ("from", "to"):
            if m.get(key) not in ids:
                errors.append(f"{at}.{key}: must be an actor id")
        if not isinstance(m.get("label"), str) or not 1 <= len(m["label"]) <= 32:
            errors.append(f"{at}.label: must be a string of 1-32 characters")
        if m.get("kind", "call") not in SEQ_KINDS:
            errors.append(f"{at}.kind: must be one of {SEQ_KINDS}")
        status = m.get("status", "unchanged")
        if status not in STATUSES:
            errors.append(f"{at}.status: must be one of {STATUSES}")
        chapter = m.get("chapter")
        if chapter is not None and (not isinstance(chapter, int) or not 1 <= chapter <= chapters):
            errors.append(f"{at}.chapter: must be 1..{chapters} when present")
        if status != "unchanged" and chapter is None:
            errors.append(f"{at}: changed message needs a chapter")
        if "note" in m and (not isinstance(m["note"], str) or not 1 <= len(m["note"]) <= 60):
            errors.append(f"{at}.note: must be a string of 1-60 characters when present")
    return errors


def check_box(item: dict, at: str) -> list[str]:
    errors: list[str] = []
    if "sub" in item and (not isinstance(item["sub"], str) or not item["sub"]):
        errors.append(f"{at}.sub: must be a non-empty string when present")
    if "kind" in item and (not isinstance(item["kind"], str) or not 1 <= len(item["kind"]) <= 6):
        errors.append(f"{at}.kind: must be a string of 1-6 characters when present")
    return errors


def check_tree(tree: list[dict], chapters: int, where: str = "tree") -> list[str]:
    if not isinstance(tree, list) or not tree:
        return [f"{where}: must be a non-empty list"]
    errors: list[str] = []
    for k, n in enumerate(tree):
        at = f"{where}[{k}]"
        if not isinstance(n, dict) or not isinstance(n.get("label"), str) or not n["label"]:
            errors.append(f"{at}.label: must be a non-empty string")
            continue
        status = n.get("status", "unchanged")
        if status not in STATUSES:
            errors.append(f"{at}.status: must be one of {STATUSES}")
        chapter = n.get("chapter")
        if chapter is not None and (not isinstance(chapter, int) or not 1 <= chapter <= chapters):
            errors.append(f"{at}.chapter: must be 1..{chapters} when present")
        if status != "unchanged" and chapter is None:
            errors.append(f"{at}: changed node needs a chapter")
        for key in ("path", "detail"):
            if key in n and not isinstance(n[key], str):
                errors.append(f"{at}.{key}: must be a string when present")
        for key in ("inputs", "outputs"):
            if key in n and (not isinstance(n[key], list) or not all(isinstance(i, str) for i in n[key])):
                errors.append(f"{at}.{key}: must be a list of strings when present")
        if "children" in n:
            errors += check_tree(n["children"], chapters, f"{at}.children")
    return errors


def load_checked(directory: Path) -> tuple[dict, list[FileDiff], dict] | None:
    pr, files = load(directory)
    try:
        guide = json.loads((directory / "guide.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"guide.json: {exc}", file=sys.stderr)
        return None
    errors = check(guide, files)
    for err in errors:
        print(err, file=sys.stderr)
    return None if errors else (pr, files, guide)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def prose(text: str) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "".join(f"<p>{inline(p)}</p>" for p in paragraphs)


def inline(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(text))


def render_flow(flow: dict) -> str:
    nodes = flow["nodes"]
    ids = [n["id"] for n in nodes]
    edges = [e for e in flow["edges"] if e["from"] != e["to"]]
    succ: dict[str, list[str]] = {i: [] for i in ids}
    for e in edges:
        succ[e["from"]].append(e["to"])

    state: dict[str, int] = {}
    back: set[tuple[str, str]] = set()

    def dfs(u: str) -> None:
        state[u] = 1
        for v in succ[u]:
            if state.get(v) == 1:
                back.add((u, v))
            elif v not in state:
                dfs(v)
        state[u] = 2

    for i in ids:
        if i not in state:
            dfs(i)
    # A cycle edge is laid out reversed, then drawn with its arrow at the start.
    laid = [(e["to"], e["from"], e) if (e["from"], e["to"]) in back else (e["from"], e["to"], e) for e in edges]

    layer = {i: 0 for i in ids}
    for _ in ids:
        for a, b, _ in laid:
            layer[b] = max(layer[b], layer[a] + 1)

    row_h, gap, pad = 104, 32, 16
    node_h = box_height(nodes)
    width: dict[str, float] = {n["id"]: box_width(n) for n in nodes}

    # Long edges pass through zero-width dummy nodes, one per skipped layer, so they route between real nodes.
    rows: dict[int, list[str]] = {}
    for i in ids:
        rows.setdefault(layer[i], []).append(i)
    up: dict[str, list[str]] = {i: [] for i in ids}
    down: dict[str, list[str]] = {i: [] for i in ids}
    chains: list[tuple[dict, list[str]]] = []
    for k, (start, end, e) in enumerate(laid):
        chain = [start]
        for l in range(layer[start] + 1, layer[end]):
            d = f"\0{k}:{l}"
            width[d] = 0
            up[d], down[d] = [], []
            rows[l].append(d)
            chain.append(d)
        chain.append(end)
        for a, b in zip(chain, chain[1:]):
            down[a].append(b)
            up[b].append(a)
        chains.append((e, chain))

    levels = sorted(rows)
    for _ in range(12):
        for seq, nbrs in ((levels[1:], up), (levels[-2::-1], down)):
            for l in seq:
                index = {v: j for r in rows.values() for j, v in enumerate(r)}
                rows[l].sort(key=lambda v: sum(index[w] for w in nbrs[v]) / len(nbrs[v]) if nbrs[v] else index[v])

    def spacing(a: str, b: str) -> float:
        return gap if width[a] and width[b] else gap / 2

    x: dict[str, float] = {}
    for l in levels:
        cur = 0.0
        for j, v in enumerate(rows[l]):
            if j:
                cur += spacing(rows[l][j - 1], v)
            x[v] = cur
            cur += width[v]

    def centre(v: str) -> float:
        return x[v] + width[v] / 2

    for _ in range(8):
        for seq, nbrs in ((levels[1:], up), (levels[-2::-1], down)):
            for l in seq:
                r = rows[l]
                want = [sum(centre(w) for w in nbrs[v]) / len(nbrs[v]) - width[v] / 2 if nbrs[v] else x[v] for v in r]
                left, right = want[:], want[:]
                for j in range(1, len(r)):
                    left[j] = max(want[j], left[j - 1] + width[r[j - 1]] + spacing(r[j - 1], r[j]))
                for j in range(len(r) - 2, -1, -1):
                    right[j] = min(want[j], right[j + 1] - width[r[j]] - spacing(r[j], r[j + 1]))
                for j, v in enumerate(r):
                    x[v] = (left[j] + right[j]) / 2

    shift = pad - min(x.values())
    for v in x:
        x[v] += shift
    top = {l: pad + 18 + j * row_h for j, l in enumerate(levels)}
    y = {v: top[l] for l in levels for v in rows[l]}
    right_edge = max(x[v] + width[v] for v in x)

    def ports(group: dict[str, list[str]]) -> dict[tuple[str, str], float]:
        out: dict[tuple[str, str], float] = {}
        for v, others in group.items():
            for k, w in enumerate(sorted(others, key=centre), 1):
                out[(v, w)] = x[v] + width[v] * k / (len(others) + 1) if width[v] else x[v]
        return out

    out_port, in_port = ports(down), ports(up)

    def bezier(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
        s = 1 - t
        return s**3 * p0 + 3 * s * s * t * p1 + 3 * s * t * t * p2 + t**3 * p3

    boxes = [(x[v], y[v], x[v] + width[v], y[v] + node_h) for v in ids]
    paths: list[tuple[dict, list[str], str, list[tuple[float, float, float, float, float]]]] = []
    for e, chain in chains:
        d, segments = "", []
        for a, b in zip(chain, chain[1:]):
            x1, y1 = out_port[(a, b)], y[a] + node_h
            x2, y2 = in_port[(b, a)], y[b]
            d += f"M{x1:.1f},{y1:.1f}" if not d else f" L{x1:.1f},{y1:.1f}"
            bend = (y2 - y1) / 2
            d += f" C{x1:.1f},{y1 + bend:.1f} {x2:.1f},{y2 - bend:.1f} {x2:.1f},{y2:.1f}"
            segments.append((x1, y1, x2, y2, bend))
        paths.append((e, chain, d, segments))
    samples = [
        [(bezier(x1, x1, x2, x2, i / 15), bezier(y1, y1 + bend, y2 - bend, y2, i / 15)) for x1, y1, x2, y2, bend in segs for i in range(16)]
        for _, _, _, segs in paths
    ]

    def hits(box: tuple[float, float, float, float]) -> int:
        n = sum(not (box[2] + 4 < b[0] or box[0] - 4 > b[2] or box[3] + 4 < b[1] or box[1] - 4 > b[3]) for b in boxes)
        return n * 99 + sum(
            box[0] - 3 <= px <= box[2] + 3 and box[1] - 3 <= py <= box[3] + 3
            for pts in samples for px, py in pts
        )

    parts, labels = [], []
    for e, chain, d, segments in paths:
        reverse = chain[0] != e["from"]
        kind = e.get("kind", "call")
        arrow = (
            f'class="edge back {kind}" marker-start="url(#arrow-{kind})"'
            if reverse else f'class="edge {kind}" marker-end="url(#arrow-{kind})"'
        )
        parts.append(f'<path {arrow} d="{d}"/>')
        if not e.get("label"):
            continue
        half = len(e["label"]) * 3.4 + 3
        fan_in = len(up[chain[-1]]) > len(down[chain[0]])
        order = segments if fan_in else segments[::-1]
        ts = (0.3, 0.45, 0.2, 0.6, 0.75, 0.1, 0.9, 0.5) if fan_in else (0.7, 0.55, 0.8, 0.4, 0.25, 0.9, 0.1, 0.5)
        cands: list[tuple[float, float, str]] = []
        for x1, y1, x2, y2, bend in order:
            for t in ts:
                px, py = bezier(x1, x1, x2, x2, t), bezier(y1, y1 + bend, y2 - bend, y2, t)
                dx = bezier(x1, x1, x2, x2, t + 0.01) - bezier(x1, x1, x2, x2, t - 0.01)
                dy = bezier(y1, y1 + bend, y2 - bend, y2, t + 0.01) - bezier(y1, y1 + bend, y2 - bend, y2, t - 0.01)
                if abs(dx) < abs(dy):
                    cands += [(px + 8, py, "start"), (px - 8, py, "end")]
                else:
                    cands += [(px, py - 10, "middle"), (px, py + 12, "middle"), (px, py, "middle")]

        def box_of(c: tuple[float, float, str]) -> tuple[float, float, float, float]:
            left = c[0] - half if c[2] == "middle" else c[0] if c[2] == "start" else c[0] - 2 * half
            return (left, c[1] - 8, left + 2 * half, c[1] + 6)

        lx, ly, anchor = min(cands, key=lambda c: hits(box_of(c)))
        boxes.append(box_of((lx, ly, anchor)))
        labels.append(f'<text class="edge-label" x="{lx:.0f}" y="{ly + 4:.0f}" text-anchor="{anchor}">{esc(e["label"])}</text>')
    svg_w = right_edge + pad
    svg_h = max(y.values()) + node_h + pad

    for n in nodes:
        cls = f'node {n["status"]}{" focal" if n.get("focal") else ""}'
        parts.append(render_box(n, x[n["id"]], y[n["id"]], width[n["id"]], node_h, cls))
    marker = "<defs>" + "".join(
        f'<marker id="arrow-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" class="arrowhead {k}"/></marker>'
        for k in EDGE_KINDS
    ) + "</defs>"
    body = "".join(parts) + "".join(labels)
    title = esc(flow.get("title") or "Flow diagram")
    return (
        f'<svg role="img" aria-labelledby="flow-title" width="{svg_w:.0f}" height="{svg_h:.0f}" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}">'
        f'<title id="flow-title">{title}</title>{marker}{body}</svg>'
    )


def render_sequence(seq: dict) -> str:
    actors, messages = seq["actors"], seq["messages"]
    index = {a["id"]: i for i, a in enumerate(actors)}
    lab_w, note_w, pad, loop = 7.3, 6.2, 16, 30
    node_h = box_height(actors)
    width = [max(box_width(a), 108) for a in actors]

    def label_w(m: dict) -> float:
        text = STATUS_PREFIX[m.get("status", "unchanged")] + m["label"]
        return len(text) * lab_w + (26 if m.get("chapter") else 0)

    gaps = [(width[i] + width[i + 1]) / 2 + 24 for i in range(len(actors) - 1)]
    spans = sorted(
        ((abs(index[m["to"]] - index[m["from"]]), min(index[m["to"]], index[m["from"]]), m) for m in messages if m["from"] != m["to"]),
        key=lambda s: s[0],
    )
    for span, lo, m in spans:
        deficit = label_w(m) + 48 - sum(gaps[lo:lo + span])
        if deficit > 0:
            gaps[lo + span - 1] += deficit
    cx = [pad + width[0] / 2]
    for g in gaps:
        cx.append(cx[-1] + g)

    ys, cur = [], pad + node_h + 38
    for m in messages:
        ys.append(cur)
        cur += 58 if m["from"] == m["to"] else 50
    bottom = cur - 10
    right = cx[-1] + width[-1] / 2
    parts = [f'<line class="life" x1="{c:.0f}" y1="{pad + node_h}" x2="{c:.0f}" y2="{bottom}"/>' for c in cx]
    for m, ay in zip(messages, ys):
        status, kind = m.get("status", "unchanged"), m.get("kind", "call")
        head = seq_marker(status, kind)
        cls = f'seq-msg {kind} {status}'
        a, b = cx[index[m["from"]]], cx[index[m["to"]]]
        text = esc(STATUS_PREFIX[status] + m["label"])
        strike = " removed" if status == "removed" else ""

        def badge(bx: float, by: float) -> str:
            return f'<a href="#ch-{m["chapter"]}"><text class="badge" x="{bx:.0f}" y="{by:.0f}">{m["chapter"]:02d}</text></a>' if m.get("chapter") else ""

        if a == b:
            parts.append(f'<path class="{cls}" marker-end="url(#{head})" d="M{a:.0f},{ay} h{loop} v22 h-{loop - 2}"/>')
            lx = a + loop + 8
            parts.append(f'<text class="seq-label{strike}" x="{lx:.0f}" y="{ay + 15}">{text}</text>')
            end = lx + label_w(m)
            parts.append(badge(end - 20, ay + 15))
            note_x, note_y = end + 12, ay + 15
            right = max(right, end)
        else:
            sign = 1 if b > a else -1
            parts.append(f'<path class="{cls}" marker-end="url(#{head})" d="M{a:.0f},{ay} H{b - sign * 1:.0f}"/>')
            lx = (a + b) / 2 - label_w(m) / 2
            parts.append(f'<text class="seq-label{strike}" x="{lx:.0f}" y="{ay - 8}">{text}</text>')
            parts.append(badge(lx + label_w(m) - 20, ay - 8))
            note_x, note_y = max(a, b) + 12, ay + 4
        if m.get("note"):
            parts.append(f'<text class="seq-note" x="{note_x:.0f}" y="{note_y:.0f}">{esc(m["note"])}</text>')
            right = max(right, note_x + len(m["note"]) * note_w)
    for i, a in enumerate(actors):
        parts.append(render_box(a, cx[i] - width[i] / 2, pad, width[i], node_h, "node"))
    svg_w, svg_h = right + pad, bottom + pad
    defs = "<defs>" + "".join(
        f'<marker id="sq-{c}-{shape}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="{"M1,1 L9,5 L1,9" if shape == "open" else "M0,0 L10,5 L0,10 z"}" class="sqh {c} {shape}"/></marker>'
        for c in ("muted", "accent", "add", "chg", "del") for shape in ("solid", "open")
    ) + "</defs>"
    title = esc(seq.get("title") or "Sequence diagram")
    return (
        f'<svg role="img" aria-labelledby="seq-title" width="{svg_w:.0f}" height="{svg_h:.0f}" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}">'
        f'<title id="seq-title">{title}</title>{defs}{"".join(parts)}</svg>'
    )


def render_seq_legend(seq: dict) -> str:
    ms = seq["messages"]
    items = status_legend({m.get("status", "unchanged") for m in ms})
    for k in SEQ_KINDS:
        first = next((m for m in ms if m.get("kind", "call") == k), None)
        if first:
            status = first.get("status", "unchanged")
            items.append(line_legend(f"seq-msg {k} {status}", seq_marker(status, k), k))
    return f'<div class="legend">{"".join(items)}</div>'


def render_legend(flow: dict) -> str:
    items = status_legend({n["status"] for n in flow["nodes"]})
    if any(n.get("focal") for n in flow["nodes"]):
        items.append('<span class="lg focal">focal</span>')
    used = {e.get("kind", "call") for e in flow["edges"]}
    items += [line_legend(f"edge {k}", f"arrow-{k}", k) for k in EDGE_KINDS if k in used]
    return f'<div class="legend">{"".join(items)}</div>'


def status_legend(used: set[str]) -> list[str]:
    return [f'<span class="lg {st}">{STATUS_PREFIX[st]}{st}</span>' for st in STATUSES if st in used]


def line_legend(cls: str, marker: str, label: str) -> str:
    return f'<span class="lg line"><svg width="26" height="8"><path class="{cls}" d="M1,4 H25" marker-end="url(#{marker})"/></svg>{label}</span>'


def seq_marker(status: str, kind: str) -> str:
    colour = SEQ_COLOUR.get(status, "accent" if kind == "http" else "muted")
    return f'sq-{colour}-{"open" if kind == "async" else "solid"}'


def box_height(items: list[dict]) -> int:
    return 52 if any(i.get("sub") or i.get("kind") for i in items) else 34


def box_width(item: dict) -> float:
    tag = len(item["kind"]) * TAG_W + 16 if item.get("kind") else 0
    name = tag + len(STATUS_PREFIX[item.get("status", "unchanged")] + item["label"]) * NAME_W
    return max(name + (30 if item.get("chapter") else 0), len(item.get("sub", "")) * SUB_W) + 28


def render_box(item: dict, bx: float, by: float, w: float, h: int, cls: str) -> str:
    base = by + (21 if h > 34 else 22)
    parts = [f'<g class="{cls}"><rect x="{bx:.0f}" y="{by:.0f}" width="{w:.0f}" height="{h}" rx="6"/>']
    tx = bx + 14
    if item.get("kind"):
        tw = len(item["kind"]) * TAG_W + 10
        parts.append(f'<rect class="tag" x="{bx + 12:.0f}" y="{by + 8:.0f}" width="{tw:.0f}" height="15" rx="2"/>')
        parts.append(f'<text class="tagtext" x="{bx + 12 + tw / 2:.0f}" y="{by + 19:.0f}" text-anchor="middle">{esc(item["kind"])}</text>')
        tx = bx + 12 + tw + 6
    parts.append(f'<text class="name" x="{tx:.0f}" y="{base:.0f}">{esc(STATUS_PREFIX[item.get("status", "unchanged")] + item["label"])}</text>')
    if item.get("sub"):
        parts.append(f'<text class="sub" x="{bx + 14:.0f}" y="{by + 40:.0f}">{esc(item["sub"])}</text>')
    if item.get("chapter"):
        c = item["chapter"]
        parts.append(f'<a href="#ch-{c}"><text class="badge" x="{bx + w - 12:.0f}" y="{base:.0f}" text-anchor="end">{c:02d}</text></a>')
    return "".join(parts) + "</g>"


def render_tree(tree: list[dict], anchors: dict[str, str]) -> str:
    statuses: set[str] = set()

    def collect(ns: list[dict]) -> None:
        for n in ns:
            statuses.add(n.get("status", "unchanged"))
            collect(n.get("children", []))

    collect(tree)
    rows: list[str] = []

    def walk(ns: list[dict], rails: list[bool]) -> None:
        for k, n in enumerate(ns):
            last = k == len(ns) - 1
            depth = len(rails)
            guides = "".join(f'<i class="rail" style="left:{12 + (i - 1) * 24}px"></i>' for i in range(1, depth) if rails[i])
            if depth:
                guides += f'<i class="elbow{" last" if last else ""}" style="left:{12 + (depth - 1) * 24}px"></i>'
            status = n.get("status", "unchanged")
            mark = f'<span class="{status}">{STATUS_PREFIX[status]}</span>' if len(statuses) > 1 else ""
            name = esc(n["label"])
            path = n.get("path", "")
            if path in anchors:
                name = f'<a href="#{anchors[path]}">{name}</a>'
            title = f' title="{esc(path)}"' if path else ""
            detail = f'<div class="tdetail">{inline(n["detail"])}</div>' if n.get("detail") else ""
            badge = f'<a class="tbadge" href="#ch-{n["chapter"]}">{n["chapter"]:02d}</a>' if n.get("chapter") else ""
            rows.append(
                f'<tr class="d{depth}"><td class="tname" style="padding-left:{14 + depth * 24}px">{guides}'
                f'<span class="tlabel"{title}>{mark}{name}</span>{detail}</td>'
                f'<td class="tio">{esc(", ".join(n.get("inputs", [])))}</td>'
                f'<td class="tio">{esc(", ".join(n.get("outputs", [])))}</td><td class="tch">{badge}</td></tr>'
            )
            walk(n.get("children", []), rails + [not last])

    walk(tree, [])
    return (
        '<table class="tree"><thead><tr><th>Component</th><th>Inputs</th><th>Outputs</th><th>Ch.</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def render_hunks(f: FileDiff, indices: list[int]) -> str:
    rows = []
    for i in indices:
        h = f.hunks[i - 1]
        rows.append(f'<tr class="hunk"><td colspan="4">{esc(h.header)}</td></tr>')
        for line in h.lines:
            sign = {"add": "+", "del": "-", "ctx": " "}[line.kind]
            old = "" if line.old is None else line.old
            new = "" if line.new is None else line.new
            rows.append(
                f'<tr class="{line.kind}"><td class="ln">{old}</td><td class="ln">{new}</td>'
                f'<td class="sign">{sign}</td><td class="code">{esc(line.text)}</td></tr>'
            )
    return f'<table class="diff">{"".join(rows)}</table>'


def file_anchor(chapter: int, path: str) -> str:
    return f"ch-{chapter}-{re.sub(r'[^A-Za-z0-9]+', '-', path)}"


def render_page(pr: dict, files: list[FileDiff], guide: dict) -> str:
    by_path = {f.path: f for f in files}
    prefix = os.path.commonpath([os.path.dirname(f.path) for f in files]) if len(files) > 1 else ""
    prefix = f"{prefix}/" if prefix else ""
    total = len(guide["chapters"])
    key_base = f'{pr.get("url", "")}@{pr.get("headRefOid", "")}'
    toc = "".join(
        f'<li><a href="#ch-{ci}">{ci:02d} · {inline(ch["title"])}</a></li>' for ci, ch in enumerate(guide["chapters"], 1)
    )
    jump = "".join(
        f'<option value="{ci}">{ci:02d} · {esc(ch["title"])}</option>' for ci, ch in enumerate(guide["chapters"], 1)
    )
    anchors: dict[str, str] = {}
    for ci, ch in enumerate(guide["chapters"], 1):
        for entry in ch["files"]:
            anchors.setdefault(entry["path"], file_anchor(ci, entry["path"]))
    tree = (
        f'<div class="card"><div class="card-title">Component tree</div>{render_tree(guide["tree"], anchors)}</div>'
        if guide.get("tree") else ""
    )
    seq = guide.get("sequence")
    sequence = (
        f'<div class="card"><div class="card-title">Sequence</div><div class="muted">{inline(seq.get("title", ""))}</div>'
        f'<div class="flow">{render_sequence(seq)}</div>{render_seq_legend(seq)}</div>'
        if seq else ""
    )
    steps = "".join(f"<li>{inline(s)}</li>" for s in guide["steps"])
    flow_title = inline(guide["flow"].get("title", ""))

    chapters_html = []
    for ci, ch in enumerate(guide["chapters"], 1):
        file_list, diffs = [], []
        for entry in ch["files"]:
            f = by_path[entry["path"]]
            indices = entry.get("hunks") or list(range(1, len(f.hunks) + 1))
            split = f" · hunks {', '.join(map(str, indices))} of {len(f.hunks)}" if entry.get("hunks") else ""
            anchor = file_anchor(ci, f.path)
            stats = f'<span class="add">+{f.count("add")}</span> <span class="del">-{f.count("del")}</span>'
            file_list.append(f'<li><a href="#{anchor}" title="{esc(f.path)}">{esc(f.path.removeprefix(prefix))}</a><span>{stats}</span></li>')
            if f.binary:
                body = '<p class="muted">Binary file.</p>'
            elif not f.hunks:
                body = f'<p class="muted">No content change ({esc(f.status)}).</p>'
            else:
                body = render_hunks(f, indices)
            rename = f" ← {esc(f.old_path)}" if f.status == "renamed" else ""
            diffs.append(
                f'<details id="{anchor}" class="file"{"" if ch.get("collapsed") else " open"}>'
                f'<summary><span class="path">{esc(f.path)}{rename}</span>'
                f'<span class="meta">{esc(f.status)}{split} · {stats}'
                f'<label onclick="event.stopPropagation()"><input type="checkbox" class="rv file-rv" '
                f'data-key="{esc(key_base)}:file:{ci}:{esc(f.path)}"> Reviewed</label></span></summary>'
                f"{body}</details>"
            )
        note = f'<div class="note">{prose(ch["note"])}</div>' if ch.get("note") else ""
        chapters_html.append(
            f'<section class="chapter" id="ch-{ci}"><div class="side">'
            f'<h2>{inline(ch["title"])}</h2>'
            f'<div class="counter">{ci:02d} / {total:02d} <label><input type="checkbox" class="rv ch-rv" '
            f'data-key="{esc(key_base)}:chapter:{ci}"> Reviewed</label></div>'
            f'{prose(ch["summary"])}{note}<ul class="files">{"".join(file_list)}</ul></div>'
            f'<div class="main">{"".join(diffs)}</div></section>'
        )

    author = pr.get("author", {}).get("login", "")
    sha = pr.get("headRefOid", "")[:7]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guide · #{pr.get("number", "")} {esc(pr.get("title", ""))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><h1>{esc(pr.get("title", ""))}</h1>
<div class="muted">{esc(author)} · <a href="{esc(pr.get("url", ""))}">#{pr.get("number", "")}</a> · {sha} ·
<span class="add">+{pr.get("additions", 0)}</span> <span class="del">-{pr.get("deletions", 0)}</span> ·
<span id="progress">0</span> / {total} chapters reviewed</div></header>
<section class="overview" id="overview"><div class="intro"><h2>Overview</h2>{prose(guide["overview"])}<ol>{steps}</ol>
<h3>Chapters</h3><ol class="toc">{toc}</ol></div>
<div class="main"><div class="card"><div class="card-title">Before / after</div><div class="muted">{flow_title}</div>
<div class="flow">{render_flow(guide["flow"])}</div>
{render_legend(guide["flow"])}</div>{sequence}{tree}</div></section>
{"".join(chapters_html)}
<nav class="jump"><button id="prev" title="Previous chapter (k)">‹</button><span class="pick"><select id="jump"><option value="0">Overview</option>{jump}</select></span><button id="next" title="Next chapter (j)">›</button></nav>
<script>{JS}</script></body></html>"""


CSS = """
:root{--bg:#fafafa;--fg:#1b1b1f;--muted:#6b6b76;--border:#e4e4e8;--card:#fff;--add-bg:#e9f6ec;--add:#1f7a3a;
--del-bg:#fbeaea;--del:#b42318;--chg-bg:#fdf4e3;--chg:#a15c07;--hunk:#eef1f8;--code:#f0f0f3;--accent:#3b5bdb;--rew:#8250df;--sans:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
@media (prefers-color-scheme:dark){:root{--bg:#141417;--fg:#e8e8ec;--muted:#9a9aa6;--border:#2c2c33;--card:#1c1c21;
--add-bg:#15301f;--add:#5cc983;--del-bg:#3a1a1a;--del:#f0857a;--chg-bg:#3a2c12;--chg:#e9b45a;--hunk:#22283a;--code:#26262d;--accent:#8da2fb;--rew:#b392f0}}
*{box-sizing:border-box}body{margin:0;padding:32px 40px 120px;background:var(--bg);color:var(--fg);
font:15px/1.55 var(--sans)}
a{color:inherit}h1{font-size:24px;margin:0 0 4px}h2{font-size:19px;margin:0 0 6px}h3{font-size:14px;margin:20px 0 6px}
code{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);padding:1px 4px;border-radius:4px}
.muted{color:var(--muted)}.add{color:var(--add)}.del{color:var(--del)}
header{margin-bottom:28px}
section.overview{display:block}.intro{max-width:80ch;margin-bottom:24px}
section{display:grid;grid-template-columns:minmax(320px,60ch) minmax(0,1fr);gap:48px;padding:28px 0;border-top:1px solid var(--border)}
.side{position:sticky;top:16px;align-self:start;max-height:calc(100vh - 32px);overflow-y:auto;padding-right:8px;line-height:1.7}.side p{margin:0 0 14px}.side code{font-size:12.5px;padding:0 3px}.side h2{line-height:1.3;margin-bottom:10px}.main{min-width:0}
.counter{color:var(--muted);font-size:13px;margin-bottom:10px;display:flex;gap:14px}
.note{border-left:3px solid var(--chg);padding:10px 14px 0;margin:16px 0;background:var(--chg-bg);border-radius:0 6px 6px 0}
ul.files{list-style:none;padding:0;margin:18px 0 0;font-size:13px;line-height:1.45}ul.files li{display:flex;justify-content:space-between;gap:12px;padding:4px 0;border-top:1px solid var(--border)}ul.files li>span{white-space:nowrap}
ul.files a{overflow-wrap:anywhere;text-decoration:none;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.toc{list-style:none;padding:0}.toc a{text-decoration:none}.toc li.done a{color:var(--muted);text-decoration:line-through}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px}.card-title{font-weight:600}
.flow{overflow-x:auto;margin-top:10px}.flow svg{max-width:100%;height:auto}
.flow text{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;fill:var(--fg)}
.flow text.name{font:600 13px var(--sans)}
.flow text.sub{font-size:11px;fill:var(--muted)}.flow text.tagtext{font:600 9px var(--sans);fill:var(--muted);letter-spacing:.04em}
.node rect.tag{fill:none;stroke:var(--muted);stroke-width:1}
.edge{fill:none;stroke:var(--muted);stroke-width:1.2;opacity:.75}.edge.back{stroke-dasharray:5 4}.arrowhead{fill:var(--muted)}
.edge.http{stroke:var(--accent);opacity:1}.arrowhead.http{fill:var(--accent)}
.edge.writeback{stroke-dasharray:6 4}
.edge.rewired{stroke:var(--rew);stroke-dasharray:2 3;stroke-width:1.6;opacity:1}.arrowhead.rewired{fill:var(--rew)}
.flow .edge-label{fill:var(--muted);font-size:11px;paint-order:stroke;stroke:var(--card);stroke-width:8px;stroke-linejoin:round}.flow .badge{fill:var(--muted);font-size:11px;text-decoration:underline}
.flow text.seq-label{font-size:12px;paint-order:stroke;stroke:var(--card);stroke-width:8px;stroke-linejoin:round}
.flow text.seq-label.removed{text-decoration:line-through}
.flow text.seq-note{font:italic 11.5px var(--sans);fill:var(--muted);paint-order:stroke;stroke:var(--card);stroke-width:6px;stroke-linejoin:round}
.life{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 5;opacity:.55}
.seq-msg{fill:none;stroke:var(--muted);stroke-width:1.4}.seq-msg.return{stroke-dasharray:6 4}.seq-msg.http{stroke:var(--accent)}
.seq-msg.added{stroke:var(--add)}.seq-msg.changed{stroke:var(--chg)}.seq-msg.removed{stroke:var(--del);stroke-dasharray:4 3}
.sqh{--c:var(--muted);fill:var(--c)}.sqh.accent{--c:var(--accent)}.sqh.add{--c:var(--add)}.sqh.chg{--c:var(--chg)}.sqh.del{--c:var(--del)}
.sqh.open{fill:none;stroke:var(--c);stroke-width:1.6}
.node rect{fill:var(--card);stroke:var(--border)}.node.added rect{fill:var(--add-bg);stroke:var(--add)}
.node.changed rect{fill:var(--chg-bg);stroke:var(--chg)}.node.removed rect{fill:var(--del-bg);stroke:var(--del);stroke-dasharray:4 3}
.node.removed text:not(.badge){text-decoration:line-through}
.node.focal>rect:first-child{stroke:var(--accent);stroke-width:2.5;stroke-dasharray:none}
.legend{display:flex;flex-wrap:wrap;align-items:center;gap:12px;font-size:12px;margin-top:6px}.lg{padding:1px 8px;border-radius:4px;border:1px solid var(--border)}.lg.focal{border:2px solid var(--accent)}.lg.line{display:inline-flex;align-items:center;gap:6px}
.lg.added{background:var(--add-bg)}.lg.changed{background:var(--chg-bg)}.lg.removed{background:var(--del-bg)}
details.file{background:var(--card);border:1px solid var(--border);border-radius:10px;margin-bottom:16px;overflow:hidden}
details.file>summary{display:flex;justify-content:space-between;gap:12px;padding:8px 14px;cursor:pointer;font-size:13px;
border-bottom:1px solid var(--border)}
.path{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}.meta{color:var(--muted);white-space:nowrap;display:flex;gap:10px}
table.diff{border-collapse:collapse;width:100%;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
table.diff td{padding:0 8px;vertical-align:top}td.ln{color:var(--muted);text-align:right;width:1%;user-select:none}
td.sign{width:1%;user-select:none}td.code{white-space:pre-wrap;overflow-wrap:anywhere}
tr.add{background:var(--add-bg)}tr.del{background:var(--del-bg)}tr.hunk td{background:var(--hunk);color:var(--muted);padding:3px 8px}
nav.jump{position:fixed;bottom:20px;right:20px;z-index:10;display:flex;align-items:center;gap:2px;padding:4px;
border-radius:999px;border:1px solid var(--border);background:color-mix(in srgb,var(--card) 80%,transparent);
backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);box-shadow:0 8px 28px rgba(0,0,0,.18)}
nav.jump button,nav.jump select{font:500 13px var(--sans);color:var(--fg);
background:transparent;border:0;cursor:pointer;outline:none}
nav.jump button{width:30px;height:30px;border-radius:50%;font-size:17px;line-height:1;color:var(--muted)}
nav.jump button:hover,nav.jump .pick:hover{background:var(--code);color:var(--fg)}
nav.jump .pick{position:relative;border-radius:999px}
nav.jump .pick::after{content:"";position:absolute;right:12px;top:50%;width:6px;height:6px;margin-top:-5px;
border:solid var(--muted);border-width:0 1.5px 1.5px 0;transform:rotate(45deg);pointer-events:none}
nav.jump select{appearance:none;-webkit-appearance:none;max-width:44ch;padding:6px 30px 6px 12px;text-overflow:ellipsis}
nav.jump :focus-visible{box-shadow:0 0 0 2px var(--muted)}
.main>.card+.card{margin-top:20px}
table.tree{width:100%;border-collapse:collapse;margin-top:12px;font-size:13px}
.tree th{text-align:left;font-weight:500;color:var(--muted);font-size:12px;padding:6px 12px;border-bottom:1px solid var(--border)}
.tree td{padding:7px 12px;vertical-align:top}
.tree tbody tr:hover{background:var(--code)}.tree tr.d0 td{background:var(--hunk)}
.tree td.tname{position:relative;min-width:300px}
.tree .rail,.tree .elbow{position:absolute;top:0;bottom:0;width:12px;border-left:1.5px solid var(--muted);opacity:.8}
.tree .elbow::after{content:"";position:absolute;left:0;top:16px;width:10px;
border-top:1.5px solid var(--muted)}.tree .elbow.last{bottom:auto;height:17px}
.tlabel{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap}.tlabel a{text-decoration:none}
.tlabel a:hover{text-decoration:underline}.tree tr.d0 .tlabel,.tree tr.d1 .tlabel{font-weight:600}
.tdetail{color:var(--muted);font-size:12.5px;margin-top:2px;max-width:70ch}.tdetail code{background:none;padding:0;font-size:12px}
.tio{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}
.tch{width:1%;text-align:right}.tbadge{color:var(--muted);font-size:12px}
@media (max-width:900px){body{padding:20px}section{grid-template-columns:1fr}.side{position:static}}
"""

JS = """
const store={get(k){try{return localStorage.getItem(k)==='1'}catch{return false}},
set(k,v){try{v?localStorage.setItem(k,'1'):localStorage.removeItem(k)}catch{}}};
function refresh(){let done=0;document.querySelectorAll('.ch-rv').forEach((c,i)=>{
const li=document.querySelectorAll('.toc li')[i];if(li)li.classList.toggle('done',c.checked);if(c.checked)done++});
document.getElementById('progress').textContent=done}
document.querySelectorAll('.rv').forEach(c=>{c.checked=store.get(c.dataset.key);
if(c.checked&&c.classList.contains('file-rv'))c.closest('details').open=false;
c.addEventListener('change',()=>{store.set(c.dataset.key,c.checked);
if(c.classList.contains('file-rv')&&c.checked)c.closest('details').open=false;refresh()})});
refresh();
const secs=[...document.querySelectorAll('section.overview,section.chapter')],jump=document.getElementById('jump');
function current(){let i=0;secs.forEach((s,j)=>{if(s.getBoundingClientRect().top<=80)i=j});return i}
function go(i){const s=secs[Math.max(0,Math.min(secs.length-1,i))];s.scrollIntoView();history.replaceState(null,'','#'+s.id)}
jump.addEventListener('change',()=>go(+jump.value));
document.getElementById('prev').addEventListener('click',()=>go(current()-1));
document.getElementById('next').addEventListener('click',()=>go(current()+1));
addEventListener('scroll',()=>{jump.value=current()},{passive:true});
addEventListener('keydown',e=>{if(e.metaKey||e.ctrlKey||e.altKey||e.target.closest?.('input,select,textarea'))return;
if(e.key==='j')go(current()+1);if(e.key==='k')go(current()-1)});
"""


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("hunks", "check", "render"):
        print(__doc__, file=sys.stderr)
        return 2
    command, directory = sys.argv[1], Path(sys.argv[2])
    if command == "hunks":
        return cmd_hunks(directory)
    loaded = load_checked(directory)
    if loaded is None:
        return 1
    if command == "render":
        out = directory / "guide.html"
        out.write_text(render_page(*loaded))
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
