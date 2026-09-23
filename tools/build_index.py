#!/usr/bin/env python3
# Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0
"""从 nodes/ 生成 index/by-situation.md（情境索引页）。

只做一件事：把节点按 cues 摊开，让人能从「我现在的处境」走到节点。
不检索、不排序（排序键只有文件路径）、不判断内容对错。

依赖：PyYAML（与 vendor 来的 validator 同一份依赖）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "nodes"
OUT = ROOT / "index" / "by-situation.md"

HEADER = """# 情境索引

<!-- Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0 -->

<!-- 本文件由 tools/build_index.py 生成，不要手改。改节点，然后重跑。 -->

> **怎么用**：在下面找一句最接近你处境的描述，点进节点。
>
> **排序说明**：只按文件路径排序。**来源、机构、置信度一律不进排序**——
> 这是本结构从 Scaffold 继承的硬规矩（`rules.md` R9 一节）。

---
"""


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
    data["_body"] = parts[2]
    return data


def main() -> int:
    nodes = [n for n in (load(p) for p in sorted(NODES.glob("*.md"))) if n]
    if not nodes:
        print("nodes/ 里没有可解析的节点。", file=sys.stderr)
        return 1

    # --- 情境索引：一句 cues → 它命中的节点 ---
    pairs: list[tuple[str, dict]] = []
    for n in nodes:
        for cue in n.get("cues") or []:
            if str(cue).strip():
                pairs.append((str(cue).strip(), n))
    pairs.sort(key=lambda p: (p[1]["_path"].name, p[0]))  # 只按路径，不含权威度

    lines = [HEADER, f"共 **{len(pairs)}** 条处境描述，指向 **{len(nodes)}** 个节点。\n", "---\n"]

    lines.append("## 按处境\n")
    for cue, n in pairs:
        lines.append(
            f"- 「{cue}」\n"
            f"  → [`{n.get('id')}`]({_rel(n)}) **{n.get('title')}**"
            f"　<sub>{n.get('type')}</sub>\n"
        )

    # --- 概念索引：title 为主键 ---
    lines.append("\n---\n\n## 按概念\n")
    by_type: dict[str, list[dict]] = {}
    for n in nodes:
        by_type.setdefault(str(n.get("type")), []).append(n)
    for typ in sorted(by_type, key=lambda t: _type_order(t)):
        lines.append(f"\n### {typ}\n")
        for n in sorted(by_type[typ], key=lambda x: x["_path"].name):
            aliases = n.get("aliases") or []
            alias_txt = f"　<sub>别名：{'、'.join(map(str, aliases))}</sub>" if aliases else ""
            lines.append(
                f"- [`{n.get('id')}`]({_rel(n)}) **{n.get('title')}**{alias_txt}\n"
            )

    # --- 关系图（纯文本邻接表，不做可视化） ---
    lines.append("\n---\n\n## 关系（`relations` 是有向的）\n")
    lines.append(
        "> 方向约定继承 Scaffold：**论据 → 立场**、**立场 → 议题**、**例外 → 被覆盖的节点**、"
        "**概念：具体 → 基础**。反向关系写在正文里，不写进 `relations`（否则构成环，被 R3 判错）。\n\n"
    )
    for n in sorted(nodes, key=lambda x: x["_path"].name):
        rels = n.get("relations") or []
        if rels:
            lines.append(f"- `{n.get('id')}` → {'、'.join(f'`{r}`' for r in rels)}\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"已生成 {OUT.relative_to(ROOT)}：{len(pairs)} 条处境 / {len(nodes)} 个节点。")
    return 0


def _rel(n: dict) -> str:
    return f"../nodes/{n['_path'].name}"


_TYPE_ORDER = ["概念", "判断点", "条件", "例外", "议题", "立场", "论据", "断言", "案例"]


def _type_order(t: str) -> int:
    return _TYPE_ORDER.index(t) if t in _TYPE_ORDER else len(_TYPE_ORDER)


if __name__ == "__main__":
    raise SystemExit(main())
