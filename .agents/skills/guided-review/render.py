#!/usr/bin/env python3
"""Guided review: list hunks, validate a guide, render it to HTML.

Usage: render.py {hunks|check|render} DIR
DIR holds pr.json, diff.patch and (for check/render) guide.json.
"""
from __future__ import annotations

import html
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

STATUSES = ("added", "changed", "removed", "unchanged")
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
    for e in edges:
        if not isinstance(e, dict) or e.get("from") not in ids or e.get("to") not in ids:
            errors.append(f"flow.edges: edge {e!r} must reference node ids")
        elif "label" in e and not isinstance(e["label"], str):
            errors.append(f"flow.edges: label of {e!r} must be a string")
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
    succ: dict[str, list[str]] = {i: [] for i in ids}
    for e in flow["edges"]:
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

    layer = {i: 0 for i in ids}
    for _ in ids:
        for e in flow["edges"]:
            if (e["from"], e["to"]) not in back:
                layer[e["to"]] = max(layer[e["to"]], layer[e["from"]] + 1)

    char_w, node_h, row_h, gap, pad, loop = 7.8, 34, 72, 28, 12, 70
    width: dict[str, float] = {}
    for n in nodes:
        text = STATUS_PREFIX[n["status"]] + n["label"]
        width[n["id"]] = len(text) * char_w + 28 + (30 if n.get("chapter") else 0)
    rows: dict[int, list[str]] = {}
    for i in ids:
        rows.setdefault(layer[i], []).append(i)
    row_w = {l: sum(width[i] for i in r) + gap * (len(r) - 1) for l, r in rows.items()}
    max_w = max(row_w.values())
    pos: dict[str, tuple[float, float]] = {}
    for l, r in rows.items():
        x = pad + loop + (max_w - row_w[l]) / 2
        for i in r:
            pos[i] = (x, pad + l * row_h)
            x += width[i] + gap
    svg_w = pad * 2 + max_w + loop * 2
    svg_h = pad * 2 + (max(rows) + 1) * row_h - (row_h - node_h)

    parts = []
    for e in flow["edges"]:
        u, v = e["from"], e["to"]
        if layer[v] - layer[u] > 1:
            x1, y1 = pos[u][0], pos[u][1] + node_h / 2
            x2, y2 = pos[v][0], pos[v][1] + node_h / 2
            bend = min(x1, x2) - loop + 10
            d = f"M{x1:.0f},{y1:.0f} C{bend:.0f},{y1:.0f} {bend:.0f},{y2:.0f} {x2:.0f},{y2:.0f}"
            lx, ly, anchor = bend + 4, (y1 + y2) / 2 + 4, "start"
        elif layer[v] > layer[u]:
            x1, y1 = pos[u][0] + width[u] / 2, pos[u][1] + node_h
            x2, y2 = pos[v][0] + width[v] / 2, pos[v][1]
            d = f"M{x1:.0f},{y1:.0f} C{x1:.0f},{y1 + 24:.0f} {x2:.0f},{y2 - 24:.0f} {x2:.0f},{y2:.0f}"
            lx, ly, anchor = (x1 + x2) / 2 + 6, (y1 + y2) / 2 + 4, "start"
        else:
            x1, y1 = pos[u][0] + width[u], pos[u][1] + node_h / 2
            x2, y2 = pos[v][0] + width[v], pos[v][1] + node_h / 2
            bend = max(x1, x2) + loop - 10
            d = f"M{x1:.0f},{y1:.0f} C{bend:.0f},{y1:.0f} {bend:.0f},{y2:.0f} {x2:.0f},{y2:.0f}"
            lx, ly, anchor = bend - 4, (y1 + y2) / 2 + 4, "end"
        parts.append(f'<path class="edge" d="{d}" marker-end="url(#arrow)"/>')
        if e.get("label"):
            parts.append(f'<text class="edge-label" x="{lx:.0f}" y="{ly:.0f}" text-anchor="{anchor}">{esc(e["label"])}</text>')
    for n in nodes:
        nx, ny = pos[n["id"]]
        w = width[n["id"]]
        text = esc(STATUS_PREFIX[n["status"]] + n["label"])
        parts.append(f'<g class="node {n["status"]}"><rect x="{nx:.0f}" y="{ny:.0f}" width="{w:.0f}" height="{node_h}" rx="6"/>')
        parts.append(f'<text x="{nx + 14:.0f}" y="{ny + 22:.0f}">{text}</text>')
        if n.get("chapter"):
            c = n["chapter"]
            parts.append(
                f'<a href="#ch-{c}"><text class="badge" x="{nx + w - 12:.0f}" y="{ny + 22:.0f}" text-anchor="end">{c:02d}</text></a>'
            )
        parts.append("</g>")
    marker = (
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" class="arrowhead"/></marker></defs>'
    )
    return f'<svg width="{svg_w:.0f}" height="{svg_h:.0f}" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}">{marker}{"".join(parts)}</svg>'


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


def render_page(pr: dict, files: list[FileDiff], guide: dict) -> str:
    by_path = {f.path: f for f in files}
    total = len(guide["chapters"])
    key_base = f'{pr.get("url", "")}@{pr.get("headRefOid", "")}'
    toc = "".join(
        f'<li><a href="#ch-{ci}">{ci:02d} · {inline(ch["title"])}</a></li>' for ci, ch in enumerate(guide["chapters"], 1)
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
            anchor = f"ch-{ci}-{re.sub(r'[^A-Za-z0-9]+', '-', f.path)}"
            stats = f'<span class="add">+{f.count("add")}</span> <span class="del">-{f.count("del")}</span>'
            file_list.append(f'<li><a href="#{anchor}">{esc(f.path)}</a><span>{stats}</span></li>')
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
<style>{CSS}</style></head><body>
<header><h1>{esc(pr.get("title", ""))}</h1>
<div class="muted">{esc(author)} · <a href="{esc(pr.get("url", ""))}">#{pr.get("number", "")}</a> · {sha} ·
<span class="add">+{pr.get("additions", 0)}</span> <span class="del">-{pr.get("deletions", 0)}</span> ·
<span id="progress">0</span> / {total} chapters reviewed</div></header>
<section class="overview"><div class="side"><h2>Overview</h2>{prose(guide["overview"])}<ol>{steps}</ol>
<h3>Chapters</h3><ol class="toc">{toc}</ol></div>
<div class="main"><div class="card"><div class="card-title">Before / after</div><div class="muted">{flow_title}</div>
<div class="flow">{render_flow(guide["flow"])}</div>
<div class="legend"><span class="lg added">+ added</span><span class="lg changed">~ changed</span>
<span class="lg removed">− removed</span><span class="lg unchanged">unchanged</span></div></div></div></section>
{"".join(chapters_html)}
<script>{JS}</script></body></html>"""


CSS = """
:root{--bg:#fafafa;--fg:#1b1b1f;--muted:#6b6b76;--border:#e4e4e8;--card:#fff;--add-bg:#e9f6ec;--add:#1f7a3a;
--del-bg:#fbeaea;--del:#b42318;--chg-bg:#fdf4e3;--chg:#a15c07;--hunk:#eef1f8;--code:#f0f0f3}
@media (prefers-color-scheme:dark){:root{--bg:#141417;--fg:#e8e8ec;--muted:#9a9aa6;--border:#2c2c33;--card:#1c1c21;
--add-bg:#15301f;--add:#5cc983;--del-bg:#3a1a1a;--del:#f0857a;--chg-bg:#3a2c12;--chg:#e9b45a;--hunk:#22283a;--code:#26262d}}
*{box-sizing:border-box}body{margin:0;padding:32px 40px 120px;background:var(--bg);color:var(--fg);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:inherit}h1{font-size:24px;margin:0 0 4px}h2{font-size:19px;margin:0 0 6px}h3{font-size:14px;margin:20px 0 6px}
code{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);padding:1px 4px;border-radius:4px}
.muted{color:var(--muted)}.add{color:var(--add)}.del{color:var(--del)}
header{margin-bottom:28px}
section{display:grid;grid-template-columns:minmax(260px,380px) minmax(0,1fr);gap:36px;padding:28px 0;border-top:1px solid var(--border)}
.side{position:sticky;top:16px;align-self:start}.main{min-width:0}
.counter{color:var(--muted);font-size:13px;margin-bottom:10px;display:flex;gap:14px}
.note{border-left:3px solid var(--chg);padding:2px 12px;margin:10px 0;background:var(--chg-bg);border-radius:0 6px 6px 0}
ul.files{list-style:none;padding:0;font-size:13px}ul.files li{display:flex;justify-content:space-between;gap:10px;padding:2px 0}
ul.files a{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-decoration:none}
.toc{list-style:none;padding:0}.toc a{text-decoration:none}.toc li.done a{color:var(--muted);text-decoration:line-through}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px}.card-title{font-weight:600}
.flow{overflow-x:auto;margin-top:10px}
.flow text{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;fill:var(--fg)}
.flow .edge{fill:none;stroke:var(--muted);stroke-width:1.2}.flow .arrowhead{fill:var(--muted)}
.flow .edge-label{fill:var(--muted);font-size:11px}.flow .badge{fill:var(--muted);font-size:11px;text-decoration:underline}
.node rect{fill:var(--card);stroke:var(--border)}.node.added rect{fill:var(--add-bg);stroke:var(--add)}
.node.changed rect{fill:var(--chg-bg);stroke:var(--chg)}.node.removed rect{fill:var(--del-bg);stroke:var(--del);stroke-dasharray:4 3}
.node.removed text:not(.badge){text-decoration:line-through}
.legend{display:flex;gap:12px;font-size:12px;margin-top:6px}.lg{padding:1px 8px;border-radius:4px;border:1px solid var(--border)}
.lg.added{background:var(--add-bg)}.lg.changed{background:var(--chg-bg)}.lg.removed{background:var(--del-bg)}
details.file{background:var(--card);border:1px solid var(--border);border-radius:10px;margin-bottom:16px;overflow:hidden}
details.file>summary{display:flex;justify-content:space-between;gap:12px;padding:8px 14px;cursor:pointer;font-size:13px;
border-bottom:1px solid var(--border)}
.path{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}.meta{color:var(--muted);white-space:nowrap;display:flex;gap:10px}
table.diff{border-collapse:collapse;width:100%;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
table.diff td{padding:0 8px;vertical-align:top}td.ln{color:var(--muted);text-align:right;width:1%;user-select:none}
td.sign{width:1%;user-select:none}td.code{white-space:pre-wrap;overflow-wrap:anywhere}
tr.add{background:var(--add-bg)}tr.del{background:var(--del-bg)}tr.hunk td{background:var(--hunk);color:var(--muted);padding:3px 8px}
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
