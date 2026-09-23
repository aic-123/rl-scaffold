#!/usr/bin/env python3
# Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0
"""把 nodes/ 渲染成 index/view.html（视图层的 HTML 形态）。

这个脚本同时承担两件事，对应 Scaffold SPEC 第 ⑥ 层对「视图层」的三个要求：

    「查询/排序规格（可见、可改、可版本化）」

    · 可改      → SORT_SPEC 是下面那个常量，改它就是改视图规格
    · 可见      → SORT_SPEC 会被原样渲染进 HTML 顶部，读页面的人看得见
    · 可版本化  → 它在 git 里，和节点一样能 diff

**它不做的事**（与 tools/build_index.py 的分工）：
    不排序以外的任何加工、不检索、不加权、不打分。
    页面里那个过滤框**只隐藏、不重排**——过滤前后顺序完全一致。

**它与 build_index.py 必须给出一致的顺序**：
    两个视图（.md 与 .html）是同一份规格的两个形态。
    顺序键统一是「文件路径，然后 cue 文本」——见 _sort_key()。
    这条不变量由 `python tools/render_view.py --check` 强制检查（退出码非 0 即失败）。

依赖：PyYAML（与 vendor 来的 validator 同一份依赖）。
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import find_path  # noqa: E402  与 CLI 共用同一份解析与路径模板

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "nodes"
OUT = ROOT / "index" / "view.html"

# ── 视图层规格：改这里就是改视图 ────────────────────────────────────────
# 这一条是本结构的硬规矩，来自 Scaffold（rules.md R9 一节）：
# 任何形式的权威度——来源、机构、置信度——都不许进排序。
# 一旦进了排序，就是在重造权威垄断。
SORT_SPEC = {
    "键": "文件路径，然后 cue 文本",
    "方向": "升序",
    "明确排除": [
        "来源（source.ref / source.kind）",
        "机构、作者",
        "证据状态（evidence_status）",
        "填充者（filled_by）",
        "任何加权、打分、推荐度",
    ],
    "为什么": "排序即推荐。把权威度写进排序，就是在替读者决定该信谁——"
    "而本结构从 Scaffold 继承的立场是：只列不裁。",
    "关系展示": "除 relations（有向）外，额外算出反向边并标注为「被引用」——"
    "反向关系本来写在正文里、不进 relations，视图层把它显式化只是方便看，不改数据。",
}

_TYPE_ORDER = ["概念", "判断点", "条件", "例外", "议题", "立场", "论据", "断言", "案例"]


def _sort_key(pair):
    """唯一的排序键。两个视图必须共用它，否则两个视图会给出不同的顺序。"""
    cue, node = pair
    return (node["_path"].name, cue)


def load(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        print(f"[skip] {path.name}: front matter 解析失败：{exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        return None
    data["_path"] = path
    return data


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def type_rank(t: str) -> int:
    return _TYPE_ORDER.index(t) if t in _TYPE_ORDER else len(_TYPE_ORDER)


# ── 可行路径：与 CLI 共用 find_path 的模板 ────────────────────────────
# 这里**不重新实现打分**。浏览器只做两件事：
#   1. 字面过滤（明确标注「不是模糊匹配」）
#   2. 点开一条已渲染好的路径
# 模糊匹配只存在于 tools/find_path.py 一处——两个实现必然漂移，
# 而"漂移的顺序"正是这个结构最不能容忍的东西。

def _path_html(p: dict) -> list[str]:
    o: list[str] = []
    A = o.append
    A("<details class='path' id='path-")
    A(esc(p["entry"]))
    A("'><summary>")
    A(esc(p["entry"]))
    A(" · ")
    A(esc(p["title"]))
    A("</summary>")
    # ⚠️ 2026-09-23 修正：路径块里必须印 `scope`，尤其是「不适用于」那半句。
    # 旧版只在**节点卡片**里印 scope，**路径块**里一个字都没有——
    # 而用户是顺着路径走的，于是会拿到**明确不适用于他**的方案却看不见排除条件。
    # 见 AUDIT.md §二.3。
    if p.get("scope"):
        A("<div class='meta'><b>⚠️ 适用范围（先看这句能不能排除你）</b> "
          f"{esc(p.get('scope'))}</div>")
    if p["cues"]:
        A(f"<p class='cue-src'>这条处境的原话：「{esc(p['cues'][0])}」</p>")
    s = p["steps"]

    A("<div class='step'><div class='h'>① 先看什么</div>")
    if s["①"]:
        for line in s["①"]:
            A(f"<div class='v'>{esc(line)}</div>")
    else:
        A("<div class='none'>⚠️ 空——没有 `变量：` 行，也没有可抠的判据数值。</div>")
    A("</div>")

    A("<div class='step'><div class='h'>② 为什么（机制）</div>")
    if s["②"]:
        for c in s["②"]:
            via = "" if not c["via"] else f"<span class='w'>（经 {esc(c['via'])} 间接）</span>"
            A(f"<div class='v'><span class='nid'>{esc(c['id'])}</span> "
              f"{esc(find_path.match_title(c))}{via}<br>{esc(c['text'])}</div>")
    else:
        A("<div class='none'>⚠️ 空——它连不到任何概念。"
          "注意这是「没找到」，不是「不存在」。</div>")
    A("</div>")

    A("<div class='step'><div class='h'>③ 什么情况下上面这套不成立</div>")
    if s["③"]:
        for e in s["③"]:
            A(f"<div class='v'><span class='nid'>{esc(e['id'])}</span> "
              f"{esc(find_path.match_title(e))} <span class='w'>（{esc(e['dir'])}）</span>"
              f"<br>{esc(e['text'])}</div>")
    else:
        A("<div class='none'>（未登记例外——是「没找到」，不是「不存在」）</div>")
    A("</div>")

    A("<div class='step'><div class='h'>④ 这背后有没有争论</div>")
    if s["④"]:
        for it in s["④"]:
            A(f"<div class='v'><span class='nid'>议题 {esc(it['id'])}</span> "
              f"{esc(it['title'])} <span class='w'>（图上 {it['hops']} 跳）</span>")
            for st in it["stances"]:
                A(f"<div class='v' style='margin-left:18px'>└ 立场 "
                  f"<span class='nid'>{esc(st['id'])}</span> {esc(st['title'])}")
                for ar in st["args"]:
                    A(f"<div class='v' style='margin-left:36px'>└ 论据 "
                      f"<span class='nid'>{esc(ar['id'])}</span> {esc(ar['title'])}")
                    for c in ar["cases"]:
                        A(f"<div class='v' style='margin-left:54px'>└ 案例 "
                          f"<span class='nid'>{esc(c)}</span></div>")
                    A("</div>")
                A("</div>")
            A("</div>")
    else:
        A("<div class='none'>（未登记议题——这个判断点目前是「有对策、无争论」）</div>")
    A("</div>")

    A("<div class='step'><div class='h'>⑤ 别人怎么做的</div>")
    if s["⑤"]:
        for c in s["⑤"]:
            cls = "grade g1" if c["grade"] == "直接" else "grade"
            A(f"<div class='v'><span class='{cls}'>{esc(c['grade'])}</span>"
              f"<span class='nid'>{esc(c['id'])}</span> {esc(c['title'])}</div>")
        A("<div class='none'>三级说的是<b>挂在哪</b>（直接挂在判断点下 / 挂在它这条争论链"
          "的论据下 / 只挂在概念下），不是<b>哪条更可信</b>。</div>")
    else:
        A("<div class='none'>⚠️ 空——图上没有任何案例能走到它。</div>")
    A("</div>")

    h6 = "⑥ 该去看哪一条（分诊支路）" if p.get("triage") else "⑥ 接下来可能撞上"
    A(f"<div class='step'><div class='h'>{esc(h6)}</div>")
    if s["⑥"]:
        for j in s["⑥"]:
            A(f"<div class='v'><span class='nid'>{esc(j['id'])}</span> {esc(j['title'])} "
              f"<span class='w'>{esc(find_path._via_label(j['via']))}</span></div>")
    else:
        A("<div class='none'>（图里没有相邻判断点——它在判断点这一层是孤立的）</div>")
    A("</div>")

    A("</details>")
    return o


CSS = """
:root{
  --bg:#ffffff; --fg:#1f1f1f; --muted:#6b6b6b; --line:#e3e3e3;
  --card:#fafafa; --accent:#185fa5; --warn:#854f0b; --chip:#f1efe8;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#1a1a1a; --fg:#eaeaea; --muted:#a0a0a0; --line:#333;
    --card:#232323; --accent:#85b7eb; --warn:#fac775; --chip:#2c2c2c;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:22px;font-weight:600;margin:0 0 4px}
h2{font-size:16px;font-weight:600;margin:36px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:14px;font-weight:600;margin:22px 0 8px;color:var(--muted)}
.gen{color:var(--muted);font-size:12px;margin:0 0 20px}
.spec{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:0 0 8px}
.spec dl{margin:0;display:grid;grid-template-columns:88px 1fr;gap:6px 12px;font-size:13px}
.spec dt{color:var(--muted)}
.spec dd{margin:0}
.spec ul{margin:4px 0 0;padding-left:18px}
.counts{color:var(--muted);font-size:13px;margin:14px 0}
input[type=search]{width:100%;padding:9px 12px;font-size:14px;color:var(--fg);
  background:var(--card);border:1px solid var(--line);border-radius:8px;margin:0 0 6px}
.hint{color:var(--muted);font-size:12px;margin:0 0 4px}
.cue{display:flex;gap:10px;align-items:baseline;padding:6px 0;border-bottom:1px solid var(--line)}
.cue:last-child{border-bottom:0}
.cue .q{flex:1;min-width:0}
.cue .to{flex:0 0 auto;color:var(--accent);text-decoration:none;font-size:12px;white-space:nowrap}
.cue .to:hover{text-decoration:underline}
.chip{display:inline-block;background:var(--chip);color:var(--muted);
  border-radius:4px;padding:1px 6px;font-size:11px;margin-left:6px;white-space:nowrap}
.chip.warn{color:var(--warn)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:0 0 10px}
.card .id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--muted)}
.card .t{font-weight:600;margin:2px 0 6px}
.card .meta{font-size:12px;color:var(--muted)}
.card .meta b{font-weight:500;color:var(--fg)}
.edges{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
.edges div{padding:3px 0;border-bottom:1px solid var(--line)}
.edges .rev{color:var(--muted)}
.empty{color:var(--muted);padding:10px 0}
details.path{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:10px 14px;margin:0 0 10px}
details.path>summary{cursor:pointer;font-weight:600;font-size:14px;list-style:none}
details.path>summary::-webkit-details-marker{display:none}
details.path>summary::before{content:"▸ ";color:var(--muted)}
details.path[open]>summary::before{content:"▾ "}
details.path .cue-src{color:var(--muted);font-size:12px;margin:6px 0 0}
.step{margin:14px 0 0;padding-top:10px;border-top:1px solid var(--line)}
.step .h{font-weight:600;font-size:13px}
.step .v{font-size:13px;margin:4px 0 0}
.step .v .nid{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--muted)}
.step .v .w{color:var(--muted);font-size:12px}
.step .none{color:var(--muted);font-size:12.5px;margin:4px 0 0}
.grade{display:inline-block;border-radius:4px;padding:0 5px;font-size:11px;
  background:var(--chip);color:var(--muted);margin-right:5px}
.grade.g1{color:var(--fg)}
a.jump{color:var(--accent);text-decoration:none;font-size:12px;white-space:nowrap;margin-left:8px}
a.jump:hover{text-decoration:underline}
@media print{input[type=search]{display:none}}
"""


def render(nodes: list[dict], match_by_id: dict, raw_by_id: dict) -> str:
    by_id = {str(n.get("id")): n for n in nodes}

    pairs = []
    for n in nodes:
        for cue in n.get("cues") or []:
            if str(cue).strip():
                pairs.append((str(cue).strip(), n))
    pairs.sort(key=_sort_key)

    out: list[str] = []
    A = out.append

    A('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
    A('<meta name="viewport" content="width=device-width,initial-scale=1">')
    A("<title>rl-scaffold · 视图层</title>")
    A(f"<style>{CSS}</style></head><body><div class='wrap'>")

    A("<h1>rl-scaffold · 情境视图</h1>")
    A("<p class='gen'>本文件由 <code>tools/render_view.py</code> 生成，不要手改。"
      "改节点或改排序规格，然后重跑。· Copyright 2026 AIC-123 · Apache-2.0</p>")

    # ── 排序规格（可见）──────────────────────────────────────────────
    A("<div class='spec'><dl>")
    A("<dt>视图层规格</dt><dd><b>本页的顺序由它决定，改它就在 "
      "<code>tools/render_view.py</code> 里改 <code>SORT_SPEC</code></b></dd>")
    A(f"<dt>排序键</dt><dd>{esc(SORT_SPEC['键'])}（{esc(SORT_SPEC['方向'])}）</dd>")
    A("<dt>明确排除</dt><dd><ul>")
    for x in SORT_SPEC["明确排除"]:
        A(f"<li>{esc(x)}</li>")
    A("</ul></dd>")
    A(f"<dt>为什么</dt><dd>{esc(SORT_SPEC['为什么'])}</dd>")
    A(f"<dt>关系展示</dt><dd>{esc(SORT_SPEC['关系展示'])}</dd>")
    A("</dl></div>")

    A(f"<p class='counts'>共 <b>{len(pairs)}</b> 条处境描述，指向 "
      f"<b>{len(nodes)}</b> 个节点。</p>")

    # ── 按需求检索（路径，不是平面表）──────────────────────────────
    A("<h2>按需求检索</h2>")
    A("<div class='spec'><dl>")
    A("<dt>检索规格</dt><dd><b>改它就在 <code>tools/find_path.py</code> 里改 "
      "<code>MATCH_SPEC</code></b>。这里是它的原样呈现，不是另一套。</dd>")
    for k in ("匹配键", "算法", "标识符是乘不是加", "入口优先判断点",
              "排除方式", "阈值", "低于阈值怎么办", "为什么"):
        A(f"<dt>{esc(k)}</dt><dd>{esc(find_path.MATCH_SPEC[k])}</dd>")
    A("<dt>明确排除</dt><dd><ul>")
    for x in find_path.MATCH_SPEC["明确排除"]:
        A(f"<li>{esc(x)}</li>")
    A("</ul></dd>")
    A("</dl></div>")
    A("<p class='hint'><b>浏览器里这个框只做字面过滤，不是模糊匹配。</b>"
      "模糊匹配只有一处实现：命令行 "
      "<code>python tools/find_path.py --problem \"你遇到的问题\"</code>。"
      "这里不重复实现它——两个实现必然漂移，而漂移的正是顺序。"
      "下面是<b>已算好的路径</b>：点「看路径」或直接展开。</p>")

    for n in sorted(nodes, key=lambda x: x["_path"].name):
        if str(n.get("type")) != "判断点":
            continue
        p = find_path.build_path(match_by_id, raw_by_id, str(n.get("id")))
        for line in _path_html(p):
            A(line)

    # ── 按处境 ────────────────────────────────────────────────────
    A("<h2>按处境</h2>")
    A("<input type='search' id='q' placeholder='字面过滤（只隐藏，不重排——顺序永远由上面的排序规格决定）'>")
    A("<p class='hint'>这个框只按字面隐藏，<b>不是</b>按需求检索。"
      "要按你描述的问题找，用上面的命令行。</p>")
    A("<div id='cues'>")
    for cue, n in pairs:
        A("<div class='cue' data-k=\"")
        A(esc(f"{cue} {n.get('id')} {n.get('title')} {n.get('type')}"))
        A("\"><span class='q'>「")
        A(esc(cue))
        A("」</span>")
        if str(n.get("type")) == "判断点":
            A(f"<a class='jump' href='#path-{esc(n.get('id'))}' data-open='path-")
            A(esc(n.get("id")))
            A("'>看路径</a>")
        A("<a class='to' href='../nodes/")
        A(esc(n["_path"].name))
        A("'>")
        A(esc(n.get("id")))
        A(" · ")
        A(esc(n.get("title")))
        A(f"<span class='chip'>{esc(n.get('type'))}</span></a></div>")
    A("</div>")

    # ── 按概念 ────────────────────────────────────────────────────
    A("<h2>按概念</h2>")
    by_type: dict[str, list[dict]] = {}
    for n in nodes:
        by_type.setdefault(str(n.get("type")), []).append(n)
    for typ in sorted(by_type, key=type_rank):
        A(f"<h3>{esc(typ)}　<span class='chip'>{len(by_type[typ])}</span></h3>")
        for n in sorted(by_type[typ], key=lambda x: x["_path"].name):
            src = n.get("source") or {}
            A("<div class='card' data-k=\"")
            A(esc(f"{n.get('id')} {n.get('title')} {n.get('type')} "
                  f"{' '.join(map(str, n.get('aliases') or []))}"))
            A("\">")
            A(f"<div class='id'>{esc(n.get('id'))}"
              f"<span class='chip'>{esc(n.get('type'))}</span>")
            st = str(n.get("evidence_status", ""))
            if st and st != "未验证":
                A(f"<span class='chip warn'>{esc(st)}</span>")
            A("</div>")
            A(f"<div class='t'>{esc(n.get('title'))}</div>")
            al = n.get("aliases") or []
            if al:
                A(f"<div class='meta'><b>别名</b> {'、'.join(esc(a) for a in al)}</div>")
            if src.get("ref") or src.get("kind"):
                A(f"<div class='meta'><b>来源</b> {esc(src.get('kind'))} · "
                  f"{esc(src.get('ref'))}</div>")
            if n.get("scope"):
                A(f"<div class='meta'><b>适用范围</b> {esc(n.get('scope'))}</div>")
            if n.get("notes"):
                A(f"<div class='meta'><b>边界</b> {esc(n.get('notes'))}</div>")
            A("</div>")

    # ── 关系 ──────────────────────────────────────────────────────
    rev: dict[str, list[str]] = {}
    for n in nodes:
        for r in n.get("relations") or []:
            rev.setdefault(str(r), []).append(str(n.get("id")))

    A("<h2>关系</h2>")
    A("<p class='hint'>方向约定继承 Scaffold：<b>论据 → 立场</b>、<b>立场 → 议题</b>、"
      "<b>例外 → 被覆盖的节点</b>、<b>概念：具体 → 基础</b>。"
      "反向关系写在正文里、不写进 <code>relations</code>（写了就构成环）。"
      "下面灰色的「被引用」是本页算出来的，只是方便看。</p>")
    A("<div class='edges'>")
    for n in sorted(nodes, key=lambda x: x["_path"].name):
        nid = str(n.get("id"))
        fwd = [str(r) for r in (n.get("relations") or [])]
        back = rev.get(nid, [])
        if not fwd and not back:
            continue
        line = f"<div>{esc(nid)}"
        if fwd:
            line += " → " + "、".join(esc(r) for r in fwd)
        else:
            line += " <span class='rev'>（无出边）</span>"
        if back:
            line += ("　<span class='rev'>被引用 ← "
                     + "、".join(esc(b) for b in sorted(back)) + "</span>")
        A(line + "</div>")
    A("</div>")

    A("<p class='gen' style='margin-top:40px'>本页只呈现结构，"
      "不判断内容对错，不排序，不建议采信任何一条。</p>")
    A("</div>")

    # ── 过滤脚本（最后）────────────────────────────────────────────
    A("<script>")
    A("var q=document.getElementById('q');")
    A("function run(){var k=q.value.trim().toLowerCase();")
    A("var els=document.querySelectorAll('#cues .cue,.card');")
    A("for(var i=0;i<els.length;i++){var d=els[i].getAttribute('data-k').toLowerCase();")
    A("els[i].style.display=(!k||d.indexOf(k)>=0)?'':'none';}}")
    A("q.addEventListener('input',run);")
    A("var js=document.querySelectorAll('a.jump');")
    A("for(var i=0;i<js.length;i++){js[i].addEventListener('click',function(e){")
    A("e.preventDefault();")
    A("var d=document.getElementById(this.getAttribute('data-open'));")
    A("if(!d)return;d.open=true;")
    A("d.scrollIntoView({block:'start'});});}")
    A("</script></body></html>")
    return "".join(out)


def main() -> int:
    if "--check" in sys.argv:
        return check_parity()

    raw_by_id, match_by_id = find_path.load_all()
    nodes = list(raw_by_id.values())
    if not nodes:
        print("nodes/ 里没有可解析的节点。", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # ⚠️ 同 build_index.py：必须显式写 LF，否则 Windows 上生成物是 CRLF，
    # 工作区会飘（`.gitattributes` 只保得住仓库侧，保不住工作区）。
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(nodes, match_by_id, raw_by_id))
    n_judge = sum(1 for n in nodes if n.get("type") == "判断点")
    print(f"已生成 {OUT.relative_to(ROOT)}：{len(nodes)} 个节点，"
          f"{n_judge} 条可行路径。")
    return 0


# ── 视图一致性检查 ────────────────────────────────────────────────────
# 为什么需要它：两个视图（.md 与 .html）是同一份规格的两个形态。
# 如果两个生成器各写各的排序，它们会**静默地**给出不同顺序——
# 而"顺序"就是这个结构里最敏感的东西（它等于推荐）。
# 所以这条不变量必须可执行，不能只写在注释里。

def _pairs_from_md(text: str) -> list[tuple[str, str]]:
    import re
    return [(m.group(1), m.group(2)) for m in re.finditer(
        r"- 「(.+?)」\n\s*→ \[`(.+?)`\]", text)]


def _pairs_from_html(text: str) -> list[tuple[str, str]]:
    """从 HTML 里读回处境条目。

    注意「看路径」有**两个**属性：`href`（给人看/无 JS 时用）与 `data-open`
    （给脚本用）。只查一个是不够的——改坏另一个，点了就会展开别人的路径。
    所以两个都读回来，由 check_parity 分别核对。
    """
    import html as _h
    import re
    out = []
    for m in re.finditer(
            r"<span class='q'>「(.*?)」</span>"
            r"(?:<a class='jump' href='#path-([^']*)' data-open='path-([^']*)'>看路径</a>)?"
            r"<a class='to' href='\.\./nodes/([^']*)'>"
            r"(.*?)<span class='chip'>", text, re.S):
        cue, href, data_open, fname, tail = m.groups()
        nid = _h.unescape(tail).split(" · ")[0].strip()
        out.append((_h.unescape(cue), nid, fname, href or "", data_open or ""))
    return out


def check_parity() -> int:
    md_p, html_p = ROOT / "index" / "by-situation.md", OUT
    if not md_p.exists() or not html_p.exists():
        print("两个视图还没生成齐，先各跑一次生成器。", file=sys.stderr)
        return 1

    a = _pairs_from_md(md_p.read_text(encoding="utf-8"))
    html_text = html_p.read_text(encoding="utf-8")
    b = _pairs_from_html(html_text)
    problems = []

    if [x[:2] for x in a] != [(x[0], x[1]) for x in b]:
        problems.append(f"两个视图的顺序或内容不一致（md {len(a)} 条 / html {len(b)} 条）")

    bad = [f for _, _, f, _, _ in b if not (NODES / f).exists()]
    if bad:
        problems.append(f"html 里有指向不存在文件的链接：{bad}")

    # 「看路径」的链接必须与判断点严格对应：
    # 是判断点的 cue 必须有，不是判断点的 cue 必须没有，且目标必须真的存在。
    raw_by_id, match_by_id = find_path.load_all()
    import re as _re
    targets = set(_re.findall(r"<details class='path' id='path-([^']*)'", html_text))
    missing, stray = [], []
    for cue, nid, _f, href, data_open in b:
        is_judge = match_by_id.get(nid, {}).get("type") == "判断点"
        if is_judge and not href:
            missing.append(nid)
        if not is_judge and href:
            stray.append(nid)
        for attr, val in (("href", href), ("data-open", data_open)):
            if val and val != nid:
                problems.append(
                    f"「看路径」的 {attr} 指向了别的节点：{cue} → {val}（应为 {nid}）")
        if href and data_open and href != data_open:
            problems.append(f"「看路径」的两个属性不一致：{cue} {href} / {data_open}")
        for val in (href, data_open):
            if val and val not in targets:
                problems.append(f"「看路径」指向了不存在的路径块：{cue} → {val}")
    if missing:
        problems.append(f"这些判断点的处境没有「看路径」链接：{sorted(set(missing))}")
    if stray:
        problems.append(f"非判断点却有「看路径」链接：{sorted(set(stray))}")
    want = {nid for nid, n in match_by_id.items() if n["type"] == "判断点"}
    if targets != want:
        problems.append(f"路径块与判断点对不上：多 {sorted(targets - want)} / "
                        f"少 {sorted(want - targets)}")

    # ⚠️ 2026-09-23 新增：**路径块里必须印出适用范围**。
    # 为什么：用户是顺着路径走的。旧版只在节点卡片印 scope、路径块不印，
    # 等于把「不适用于…」那半句藏起来——而那句话正是他该先看的。
    # 本检查是 §二.3 的第二道守卫（第一道在 find_path.check 里管文本输出）。
    for m in _re.finditer(r"<details class='path' id='path-([^']+)'>(.*?)</details>",
                          html_text, _re.S):
        nid, block = m.group(1), m.group(2)
        scope = str((match_by_id.get(nid) or {}).get("scope") or "")
        flat_scope = _re.sub(r"\s+", "", scope)
        if flat_scope and flat_scope[:24] not in _re.sub(r"\s+", "", block):
            problems.append(f"路径块 {nid} 没有印出适用范围——用户会看不到那句「不适用于…」")

    # 标签配平。为什么要有这条：多一个 </div> 浏览器会**静默容错**，
    # 所以它能一直藏着不被发现——而它迟早会在某次改动后变成真的错位。
    # 这个 bug 就是真发生过的：上一轮生成器多输出一个 </div>，
    # 页面看起来完全正常，只有数数才发现。
    body = html_text[html_text.index("<body>"):]
    for tag in ("div", "details", "summary", "span", "a", "dl", "dt", "dd",
                "ul", "li", "p"):
        o = len(_re.findall(r"<" + tag + r"\b[^>]*>", body))
        c = len(_re.findall(r"</" + tag + r">", body))
        if o != c:
            problems.append(f"<{tag}> 标签不配平：开 {o} / 闭 {c}")

    if problems:
        for p in problems[:12]:
            print(f"[FAIL] {p}", file=sys.stderr)
        if len(problems) > 12:
            print(f"[FAIL] …另有 {len(problems) - 12} 条同类问题未列出。", file=sys.stderr)
        return 1

    print(f"视图一致性检查通过：两个视图同为 {len(a)} 条处境，顺序逐条一致，"
          f"链接全部可解析；{len(targets)} 条可行路径与判断点一一对应。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
