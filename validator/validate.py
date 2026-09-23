#!/usr/bin/env python3
# Copyright 2026 AIC-123
# SPDX-License-Identifier: Apache-2.0
"""知识结构工具 · 结构校验器（R1–R10）+ 待填清单

只做两件事：报告「结构是否自洽」，以及列出「还欠什么」。
不判断内容对错，不排序，不建议采信哪一条，不说「该填什么」，不写入任何文件，不自动修复。

    python validator/validate.py ./samples
    python validator/validate.py ./samples --todo              # 待填清单：只列缺口，不给答案
    python validator/validate.py ./samples --allow-verified    # 仅限 hooks 授权目录
    python validator/validate.py --self-test

退出码：有 ERROR 为 1，仅 WARN 为 0，用法错误为 2（--todo 恒为 0）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# --------------------------------------------------------------------------
# 权威常量。与 schema/node.schema.yaml 互为镜像，一致性由 --self-test 强制检查。
# --------------------------------------------------------------------------
PREFIX = {
    "概念": "con",
    "判断点": "judge",
    "条件": "cond",
    "例外": "exc",
    "议题": "issue",
    "立场": "stance",
    "论据": "arg",
    "断言": "claim",
    "案例": "case",
}
REQUIRED_FIELDS = (
    "id", "type", "title", "aliases", "cues", "scope",
    "source", "evidence_status", "relations", "filled_by", "notes",
)
USER_WRITABLE_STATUS = ("已确立", "假说", "有争议", "已淘汰", "未验证")
DEFAULT_STATUS = "未验证"
HOOK_ONLY_STATUS = "已验证"
MAX_VARS = 4

# filled_by 的取值不设白名单（见 SPEC.md）。但下面这个值有**结构含义**，受 R8 约束：
# 它声明"这个节点还没人填过"，所以节点里不该有已填内容。
# ⚠️ R8 目前是**暂定 WARN**：判据（哪些字段算"已填"）尚未定案，详见 R8 块的注释。
EMPTY_FILLER = "未填充"
FILLER_CONVENTIONS = ("人", EMPTY_FILLER)
FILLER_MODEL_PATTERN = r"^模型\(.+\)$"

# source.kind 的单轴枚举（2026-09-22 拆轴）。它只回答「来源是什么文体/载体」，
# 不回答「来源是不是人」（那是归属），也不含「未填」状态——未填是空字符串。
# 所以这里没有 `未知`：它与 ref 为空 30/30 完全共现，零信息量。
#
# 这个枚举是**闭合**的：写了枚举之外的取值报 R10（ERROR）——与 R5 管 `type` 的枚举、
# R7 管 evidence_status 的枚举同理，枚举字段的取值必须闭合，否则视图层按来源标签分组时
# 会把同一个桶拆成两个（`论文` 与 `paper`）。
# 枚举里的 `其他` 是留给"不属于这几类"的出口，所以这条不会逼人说假话。
# 本常量同时用于守护 schema 镜像（--self-test）。
SOURCE_KINDS = ("教材", "论文", "标准", "官方文档", "访谈口述", "其他")

ID_PATTERN = r"^[a-z]{2,6}-\d{4}$"
ID_RE = re.compile(ID_PATTERN)
FM_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$", re.S)
VAR_RE = re.compile(r"变量\s*[:：]\s*(.+)")
VAR_SPLIT_RE = re.compile(r"[、,，;；/]")

SEV_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


class Finding:
    __slots__ = ("sev", "rule", "path", "line", "msg", "fix")

    def __init__(self, sev, rule, path, line, msg, fix):
        self.sev, self.rule = sev, rule
        self.path, self.line = path, line
        self.msg, self.fix = msg, fix

    @property
    def where(self):
        return f"{self.path}:{self.line}"


class Node:
    __slots__ = ("path", "data", "body", "lines", "broken")

    def __init__(self, path, data=None, body="", lines=None, broken=None):
        self.path = path
        self.data = data or {}
        self.body = body
        self.lines = lines or {}
        self.broken = broken

    def ln(self, *keys):
        for k in keys:
            if k in self.lines:
                return self.lines[k]
        return 1

    def at(self, *keys):
        return f"{self.path}:{self.ln(*keys)}"

    @property
    def id(self):
        return self.data.get("id")

    @property
    def type(self):
        return self.data.get("type")

    @property
    def status(self):
        return self.data.get("evidence_status", DEFAULT_STATUS)

    @property
    def relations(self):
        r = self.data.get("relations")
        return [x for x in r if isinstance(x, str)] if isinstance(r, list) else []

    @property
    def source(self):
        s = self.data.get("source")
        return s if isinstance(s, dict) else {}


# --------------------------------------------------------------------------
# 读取
# --------------------------------------------------------------------------
def _key_lines(fm: str, offset: int) -> dict:
    """每个键的行号（相对文件 1-based）。嵌套键用点号连接，如 source.ref。"""
    lines: dict[str, int] = {}
    try:
        root = yaml.compose(fm)
    except yaml.YAMLError:
        return lines

    def walk(node, prefix):
        if not isinstance(node, yaml.MappingNode):
            return
        for k, v in node.value:
            key = prefix + str(k.value)
            lines.setdefault(key, offset + k.start_mark.line + 1)
            walk(v, key + ".")

    walk(root, "")
    return lines


def load(path: Path, display: str) -> Node:
    try:
        raw = path.read_text(encoding="utf-8").lstrip("﻿")
    except OSError as exc:
        return Node(display, broken=f"读取失败：{exc}")

    m = FM_RE.match(raw)
    if not m:
        return Node(display, broken="找不到被 --- 包裹的 YAML front matter")

    fm, body = m.group(1), m.group(2)
    offset = raw[: m.start(1)].count("\n")
    try:
        data = yaml.safe_load(fm)
    except yaml.YAMLError as exc:
        return Node(display, broken=f"front matter 不是合法 YAML：{exc}")
    if not isinstance(data, dict):
        return Node(display, broken="front matter 顶层不是键值映射")
    return Node(display, data, body, _key_lines(fm, offset))


def collect(root: Path) -> list[Node]:
    cwd = Path.cwd().resolve()
    out = []
    for p in sorted(root.rglob("*.md")):
        # README 是给人看的说明，不是知识节点。别把它当节点校验。
        if p.name.lower().startswith("readme"):
            continue
        try:
            display = p.resolve().relative_to(cwd).as_posix()
        except ValueError:
            display = p.as_posix()
        out.append(load(p, display))
    return out


# --------------------------------------------------------------------------
# 规则 R1–R10
# --------------------------------------------------------------------------
def find_cycles(adj: dict[str, list[str]]) -> list[list[str]]:
    """R3 用。返回若干条环路，每条形如 a → b → a。"""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in adj}
    stack: list[str] = []
    found: list[list[str]] = []
    seen: set[frozenset] = set()

    def dfs(u):
        color[u] = GREY
        stack.append(u)
        for v in adj.get(u, ()):
            if v not in color:
                continue
            if color[v] == GREY:
                cycle = stack[stack.index(v):] + [v]
                sig = frozenset(cycle)
                if sig not in seen:
                    seen.add(sig)
                    found.append(cycle)
            elif color[v] == WHITE:
                dfs(v)
        stack.pop()
        color[u] = BLACK

    for k in sorted(adj):  # 排序只为输出稳定，与来源、权威度无关
        if color[k] == WHITE:
            dfs(k)
    return found


def _content_fields(n: Node) -> list[str]:
    """R8 用：列出这个节点里"已经填了内容"的字段。

    只认真正承载知识的字段。**空字符串不算内容**——`source.kind` 的"未填"就是空字符串
    （2026-09-22 拆轴前写作 `未知`，该取值已删除）；写了具体值（教材/论文/访谈口述/其他）才算。

    ⚠️ `title` 目前**也算内容**，但这一条**尚未定案**：同一个文件里的 `todo_report()`
    把 `title` 当节点标签打印、不当缺口。两套判据并存是已知的，留待产品期统一
    （详见 R8 块的说明与 `rules.md` 的 R8 章节）。
    """
    filled: list[str] = []
    for key in ("title", "scope", "notes"):
        if str(n.data.get(key) or "").strip():
            filled.append(key)
    for key in ("aliases", "cues", "relations"):
        v = n.data.get(key)
        if isinstance(v, list) and any(str(x).strip() for x in v):
            filled.append(key)
    ref = n.source.get("ref")
    if ref is not None and str(ref).strip():
        filled.append("source.ref")
    kind = n.source.get("kind")
    if kind is not None and str(kind).strip():
        filled.append("source.kind")
    if (n.body or "").strip():
        filled.append("正文")
    return filled


def check(nodes: list[Node], allow_verified: bool = False) -> list[Finding]:
    F: list[Finding] = []

    def add(sev, rule, node, keys, msg, fix):
        F.append(Finding(sev, rule, node.path, node.ln(*keys), msg, fix))

    # --- 解析失败 ---
    for n in nodes:
        if n.broken:
            F.append(Finding("ERROR", "R5", n.path, 1,
                             f"节点无法解析：{n.broken}。",
                             "修好 front matter 再用。本工具不修复，也不猜。"))

    ok = [n for n in nodes if not n.broken]

    # --- R5 id 冲突或格式错（含 type 前缀、悬挂引用） ---
    seen: dict[str, str] = {}
    for n in ok:
        nid, typ = n.id, n.type
        if not nid:
            add("ERROR", "R5", n, ("id",), "缺少 id。", "按 前缀-四位序号 补一个，如 con-0001。")
        else:
            nid = str(nid)
            if not ID_RE.match(nid):
                add("ERROR", "R5", n, ("id",), f"id 格式不合规：{nid}。",
                    "格式为 前缀-四位序号，如 judge-0001。")
            if nid in seen:
                add("ERROR", "R5", n, ("id",), f"id 重复：{nid} 已出现在 {seen[nid]}。",
                    "改成全局唯一的 id。")
            else:
                seen[nid] = n.path

        if typ not in PREFIX:
            add("ERROR", "R5", n, ("type",), f"未知 type：{typ}。",
                "只能是：" + "、".join(PREFIX) + "。")
        elif nid and ID_RE.match(str(nid)):
            want = PREFIX[typ]
            got = str(nid).split("-")[0]
            if got != want:
                add("ERROR", "R5", n, ("id",),
                    f"前缀与 type 不符：type={typ} 应配 {want}-，实际是 {got}-。",
                    f"改为 {want}-NNNN。")

    ids = {str(n.id) for n in ok if n.id}
    for n in ok:
        for r in n.relations:
            if r not in ids:
                add("ERROR", "R5", n, ("relations",),
                    f"relations 指向不存在的 id：{r}。",
                    "确认 id 拼写，或先把那个节点建出来。")

    # --- R4 类型与字段不匹配 ---
    by_id = {str(n.id): n for n in ok if n.id}
    for n in ok:
        missing = [f for f in REQUIRED_FIELDS if f not in n.data]
        if missing:
            add("ERROR", "R4", n, (missing[0],),
                f"缺少必填字段：{'、'.join(missing)}。",
                "字段不得增删。补上；值确实不知道就留空，不要猜。")

        if n.type == "判断点":
            m = VAR_RE.search(n.body or "")
            if not m:
                add("ERROR", "R4", n, ("type",),
                    "type=判断点，但正文没有声明「变量：…」。",
                    "正文里写清看哪几个变量（不超过 4 个）。")
            else:
                variables = [v for v in VAR_SPLIT_RE.split(m.group(1)) if v.strip()]
                if len(variables) > MAX_VARS:
                    add("ERROR", "R4", n, ("type",),
                        f"type=判断点，声明了 {len(variables)} 个变量，超过上限 {MAX_VARS}。",
                        f"砍到 {MAX_VARS} 个以内。变量再多就不叫判断点了。")

        if n.type == "立场":
            has_issue = any(
                r in by_id and by_id[r].type == "议题" for r in n.relations
            )
            if not has_issue:
                add("ERROR", "R4", n, ("relations",),
                    "type=立场，但 relations 里没有指向任何「议题」的节点。",
                    "立场必须有议题可站。补一条指向 issue-NNNN 的 relations。")

    # --- R1 孤立节点 ---
    targets: set[str] = set()
    for n in ok:
        targets.update(n.relations)
    for n in ok:
        if n.type == "概念":
            continue  # 概念豁免
        if not n.relations and str(n.id) not in targets:
            add("ERROR", "R1", n, ("relations",),
                "孤立节点：自己不指向任何节点，也没有任何节点指向它。",
                "接上关系；或确认它自成一体，那就在正文里说明为什么。概念类型豁免此规则。")

    # --- R3 循环依赖 ---
    adj = {str(n.id): n.relations for n in ok if n.id}
    for cycle in find_cycles(adj):
        node = by_id.get(cycle[0])
        if node is None:
            continue
        F.append(Finding("ERROR", "R3", node.path, node.ln("relations"),
                         f"循环依赖：{' → '.join(cycle)}。",
                         "环上的节点互为前提。删掉环上任意一条 relations。"))

    # --- R2 缺出处 ---
    for n in ok:
        ref = n.source.get("ref")
        has_ref = ref is not None and str(ref).strip() != ""
        if has_ref or n.status == DEFAULT_STATUS:
            continue
        if n.status == HOOK_ONLY_STATUS:
            continue  # 由 R7 专门处理，不重复报
        add("ERROR", "R2", n, ("source.ref", "source", "evidence_status"),
            f"evidence_status={n.status}，却没有 source.ref。",
            "补上出处；补不出来就把 evidence_status 改回 未验证。")

    # --- R6 情境索引缺失（警告级） ---
    for n in ok:
        cues = n.data.get("cues")
        if isinstance(cues, list) and not cues:
            add("WARN", "R6", n, ("cues",),
                "cues 是空数组——没有情境索引，认局的时候调不出这个节点。",
                "补上「当事人会怎么描述自己的处境」。确实写不出就先留着，这只是警告。")

    # --- R7 状态越权自声明 ---
    for n in ok:
        st = n.status
        if st == HOOK_ONLY_STATUS:
            if allow_verified:
                F.append(Finding("INFO", "R7", n.path, n.ln("evidence_status"),
                                 "已验证 —— 本次以 --allow-verified 运行，视为由验证方授予。",
                                 "该开关只允许用于 hooks 授权的输出目录。"))
            elif str(n.data.get("filled_by", "")).startswith("模型"):
                add("ERROR", "R7", n, ("evidence_status",),
                    "疑似模型代填：evidence_status=已验证。该状态只能由验证方通过 hooks 授予，"
                    "不可手工写入。请改为 未验证。",
                    "改为 未验证；要升级就走 hooks 流程。")
            else:
                add("ERROR", "R7", n, ("evidence_status",),
                    "该状态只能由验证方通过 hooks 授予，不可手工写入。请改为 未验证。",
                    "改为 未验证；要升级就走 hooks 流程。")
        elif st not in USER_WRITABLE_STATUS:
            add("ERROR", "R7", n, ("evidence_status",),
                f"evidence_status 取值非法：{st}。",
                "用户可写值只有：" + "、".join(USER_WRITABLE_STATUS)
                + "。已验证只能由 hooks 授予。")

    # --- R8 未填充声明与内容矛盾（⚠️ 暂定：WARN 级，判据未定案） ---
    # filled_by 的取值本身不设白名单，但「未填充」不是一种"署名方式"，
    # 而是一个事实断言：这个节点还没人填过。节点里有内容，这个断言就是假的。
    #
    # ⚠️ 为什么暂定为 WARN 而不是 ERROR（2026-09-22）：
    #    本规则要守的东西没有争议（留痕）；有争议的是**哪些字段算"已填"**。
    #    `_content_fields()` 把 title 也算内容，而同一个文件里的 `todo_report()`
    #    把 title 当节点标签打印、不当缺口——两套判据并存。
    #    于是「有名字的骨架 + filled_by=未填充」这个状态被判死，但它到底是
    #    "合法的留白"还是"填了不署名"，取决于本结构将来用在哪个领域，
    #    属于**产品语义，尚未定案**。
    #    暂定为 WARN：不阻断任何人立骨架，提醒仍在，判据与级别都留待产品期再定。
    for n in ok:
        if str(n.data.get("filled_by", "")).strip() != EMPTY_FILLER:
            continue
        filled = _content_fields(n)
        if filled:
            add("WARN", "R8", n, ("filled_by",),
                f"filled_by={EMPTY_FILLER}，但节点里已经有这些字段：{'、'.join(filled)}。",
                "只是立了骨架、内容还没填 → 忽略这条即可（哪些字段算「已填」尚未定案）。"
                f"确实已经填了东西 → 请如实署名，「{EMPTY_FILLER}」不能和已填内容同时出现。")

    # --- R9 来源标注只填一半（警告级，本仓库新增） ---
    # source 内部允许为空（SPEC §一），所以「ref 空 + kind 空」是合法状态，不报。
    # 但**只填一半**是残缺：说了出处说不出类型，或说了类型说不出出处。
    # 这正是视图层要显示的「来源标签」没填完。与 R6 同理——写不出来是常态，
    # 留空是诚实的，所以只提醒，不阻断。
    #
    # ⚠️ 这不是「镜像 R8」。R8 管的是 filled_by（关于**节点自身**的断言，能被节点内容证伪）；
    #    R9 管的是 source（关于**来源**的断言，节点内容证伪不了它）。两者不同类，不可互推。
    for n in ok:
        ref = n.source.get("ref")
        kind = n.source.get("kind")
        has_ref = ref is not None and str(ref).strip() != ""
        has_kind = kind is not None and str(kind).strip() != ""
        if has_ref and not has_kind:
            add("WARN", "R9", n, ("source.kind", "source"),
                "写了 source.ref，但 source.kind 是空的——说了出处，说不出类型。",
                "补上 kind（教材 / 论文 / 标准 / 官方文档 / 访谈口述 / 其他）。"
                "确实说不出来就先留着，这只是警告。")
        elif has_kind and not has_ref:
            add("WARN", "R9", n, ("source.ref", "source"),
                "写了 source.kind，但 source.ref 是空的——说了类型，说不出出处。",
                "补上具体出处（DOI / 标准编号 / 章节 / 链接）。"
                "确实补不出来就先留着，这只是警告。")

    # --- R10 来源类型取值非法（本仓库新增） ---
    # kind 是**闭合枚举**，值域写在 SPEC.md §一 与 schema 里。写了枚举之外的取值报 ERROR，
    # 与 R5 管 `type` 的枚举、R7 管 evidence_status 的枚举同理。
    #
    # 为什么这次是 ERROR 而不是 WARN：R9 管的是"**没填**"（留空是诚实的，所以只提醒）；
    # R10 管的是"**填错了**"——错值不是留白，它会让视图层按来源标签分组时把同一个桶
    # 拆成两个（`论文` 与 `paper` 各成一桶），静默地坏掉。
    # 枚举里的 `其他` 是留给"不属于这几类"的出口，所以这条不会逼人说假话。
    #
    # 空字符串（未填）与字段缺失都合法——那是"说不出处"，不是"填错了"。
    for n in ok:
        kind = n.source.get("kind")
        if kind is None:
            continue
        ks = str(kind).strip()
        if ks and ks not in SOURCE_KINDS:
            add("ERROR", "R10", n, ("source.kind", "source"),
                f"source.kind 取值非法：{ks}。",
                "只能是：" + " / ".join(SOURCE_KINDS) + "。未填请留空字符串，不要写别的占位词。")

    return F


# --------------------------------------------------------------------------
# 输出
# --------------------------------------------------------------------------
def report(findings: list[Finding], node_count: int, stream=sys.stdout) -> int:
    # 排序键只有 (严重度, 路径, 行号)。不含来源、不含 kind、不含任何权威度。
    findings = sorted(findings, key=lambda f: (SEV_ORDER[f.sev], f.path, f.line))
    counts = {"ERROR": 0, "WARN": 0, "INFO": 0}

    for f in findings:
        counts[f.sev] += 1
        print(f"{f.where}  {f.sev:<5} {f.rule}  {f.msg}", file=stream)
        print(f"    ↳ 修复方向：{f.fix}", file=stream)

    if findings:
        print(file=stream)
    print(f"扫描 {node_count} 个节点 —— ERROR {counts['ERROR']}，"
          f"WARN {counts['WARN']}，INFO {counts['INFO']}", file=stream)
    print("本报告只诊断结构是否自洽，不判断内容对错，不排序，不建议采信任何一条。", file=stream)
    return 1 if counts["ERROR"] else 0


# --------------------------------------------------------------------------
# 待填清单：从结构生成"还欠什么"，不生成"该填什么"
# --------------------------------------------------------------------------
def todo_report(nodes: list[Node], stream=sys.stdout) -> int:
    """列出所有缺口。

    只列缺口，不给答案，也不按任何权威度排序。
    排序键只有文件路径——这是为了保证输出稳定，与来源、机构、可信度无关。
    """
    ok = [n for n in nodes if not n.broken]
    gaps = []

    for n in ok:
        items = []
        cues = n.data.get("cues")
        if isinstance(cues, list) and not cues:
            items.append("cues —— 没有情境索引，认局的时候调不出这个节点")
        ref = n.source.get("ref")
        kind = n.source.get("kind")
        has_ref = ref is not None and str(ref).strip() != ""
        has_kind = kind is not None and str(kind).strip() != ""
        # source 只报一条：两样都空时报 source，否则报缺的那一样。
        # 不各报一条——实测 21 个样本是"两样都空"，各列一条会让清单凭空翻倍成噪音。
        if not has_ref and not has_kind:
            items.append("source —— 说不出这条知识从哪来，也说不出是什么类型")
        elif not has_ref:
            items.append("source.ref —— 说不出这条知识从哪来")
        elif not has_kind:
            items.append("source.kind —— 说不出这条知识是什么类型")
        if "待填" in str(n.data.get("notes", "")):
            items.append("notes —— 自己标记了「待填」")
        if items:
            gaps.append((n, items))

    gaps.sort(key=lambda g: g[0].path)  # 只按路径，不含权威度

    print("待填清单 —— 只列缺口，不给答案，不按任何权威度排序。", file=stream)
    print(file=stream)

    if not gaps:
        print("没有待填项。", file=stream)
    for n, items in gaps:
        print(n.path, file=stream)
        print(f"    {n.type}　「{n.data.get('title', '')}」", file=stream)
        for it in items:
            print(f"    · 缺 {it}", file=stream)
        if n.relations:
            print(f"    · 已挂上：{' → '.join(n.relations)}", file=stream)
        print(file=stream)

    print(f"扫描 {len(ok)} 个节点，{len(gaps)} 个存在待填项。", file=stream)
    print("注意：列出缺口不等于出错。「未验证 + 无出处」是合法状态，列在这里只因为它还欠着。", file=stream)
    print("这份清单只说「还欠什么」，不说「该填什么」。填什么、由谁填，由人决定。", file=stream)
    return 0


# --------------------------------------------------------------------------
# 自检：最小可跑检查。改坏了这里就红。
# --------------------------------------------------------------------------
def _mk(**over) -> Node:
    base = {
        "id": "con-0001", "type": "概念", "title": "t", "aliases": [], "cues": ["c"],
        "scope": "s", "source": {"ref": "", "kind": ""},
        "evidence_status": DEFAULT_STATUS, "relations": [],
        "filled_by": "人", "notes": "",
    }
    base.update(over)
    return Node("selftest.md", base, "", {k: 2 for k in base})


def self_test() -> int:
    def sevs(nodes, **kw):
        return [(f.sev, f.rule, f.msg) for f in check(nodes, **kw)]

    # R7：手写的 已验证 必须被拦
    got = sevs([_mk(evidence_status="已验证")])
    assert any(s == "ERROR" and r == "R7" for s, r, _ in got), got
    assert any("不可手工写入" in m for _, r, m in got if r == "R7"), got

    # R7：模型写的 已验证 文案必须点明"疑似模型代填"
    got = sevs([_mk(evidence_status="已验证", filled_by="模型(示例数据)")])
    assert any("疑似模型代填" in m for _, r, m in got if r == "R7"), got

    # R7：--allow-verified 必须放行，且只降级成 INFO
    got = sevs([_mk(evidence_status="已验证")], allow_verified=True)
    assert not any(s == "ERROR" and r == "R7" for s, r, _ in got), got
    assert any(s == "INFO" and r == "R7" for s, r, _ in got), got

    # R7：合法值之外的一切都报错
    assert any(r == "R7" and s == "ERROR" for s, r, _ in sevs([_mk(evidence_status="大概对")]))

    # R2：有状态没出处 → ERROR；状态是 未验证 → 不报
    assert any(r == "R2" for _, r, _ in sevs([_mk(evidence_status="假说")]))
    assert not any(r == "R2" for _, r, _ in sevs([_mk(evidence_status="未验证")]))

    # R1：孤立节点报错，概念豁免
    assert any(r == "R1" for _, r, _ in sevs([_mk(id="claim-0001", type="断言")]))
    assert not any(r == "R1" for _, r, _ in sevs([_mk()]))

    # R3：环必须被找到，且给出完整路径
    a = _mk(id="arg-0001", type="论据", relations=["arg-0002"])
    b = _mk(id="arg-0002", type="论据", relations=["arg-0001"])
    cycles = find_cycles({"arg-0001": ["arg-0002"], "arg-0002": ["arg-0001"]})
    assert cycles and cycles[0][0] == cycles[0][-1] and len(cycles[0]) == 3, cycles
    assert any(r == "R3" for _, r, _ in sevs([a, b]))

    # R4：判断点变量 >4 报错；立场不指向议题报错
    over = _mk(id="judge-0001", type="判断点",
               relations=["cond-0001"], cues=["c"])
    over.body = "变量：甲、乙、丙、丁、戊\n阈值：略\n"
    assert any(r == "R4" and "超过上限" in m for _, r, m in sevs([over]))
    over.body = "变量：甲、乙\n阈值：略\n"
    assert any(r == "R5" for _, r, _ in sevs([over]))  # cond-0001 不存在 → 悬挂引用
    assert any(r == "R4" for _, r, _ in sevs([_mk(id="stance-0001", type="立场")]))

    # R6：空 cues 是 WARN，不进 ERROR
    got = sevs([_mk(cues=[])])
    assert any(s == "WARN" and r == "R6" for s, r, _ in got), got
    assert not any(s == "ERROR" for s, _, _ in got), got

    # R5：id 格式 / 前缀与 type 不符 / 重复
    assert any("格式不合规" in m for _, r, m in sevs([_mk(id="con-1")]) if r == "R5")
    assert any("前缀与 type 不符" in m for _, r, m in sevs([_mk(id="arg-0001")]) if r == "R5")
    assert any("重复" in m for _, r, m in sevs([_mk(), _mk(title="t2")]) if r == "R5")

    # R4：缺 aliases 字段必须报错（字段清单不得增删）
    n_no_alias = _mk()
    del n_no_alias.data["aliases"]
    assert any(r == "R4" and "aliases" in m for _, r, m in sevs([n_no_alias]))

    # 待填清单：只列缺口，不给答案，不排序
    import io
    buf = io.StringIO()
    rc = todo_report([_mk(cues=[], notes="待填")], stream=buf)
    out = buf.getvalue()
    assert rc == 0, "待填清单不该影响退出码"
    assert "待填清单" in out and "不说「该填什么」" in out, out
    assert "cues" in out and "source" in out, out
    # 无缺口时不虚报
    buf2 = io.StringIO()
    todo_report([_mk(cues=["c"], source={"ref": "x", "kind": "教材"})], stream=buf2)
    assert "没有待填项" in buf2.getvalue(), buf2.getvalue()

    # 待填清单：source 只报一条——两样都空报 source，只缺一样报那一样
    def todo_of(node):
        b = io.StringIO()
        todo_report([node], stream=b)
        return b.getvalue()

    t_both = todo_of(_mk(cues=["c"], source={"ref": "", "kind": ""}))
    assert t_both.count("· 缺 source") == 1, t_both
    assert "说不出这条知识从哪来" in t_both and "什么类型" in t_both, t_both

    t_kind = todo_of(_mk(cues=["c"], source={"ref": "DOI:10.x", "kind": ""}))
    assert t_kind.count("· 缺 source") == 1, t_kind
    assert "缺 source.kind" in t_kind and "什么类型" in t_kind, t_kind

    t_ref = todo_of(_mk(cues=["c"], source={"ref": "", "kind": "教材"}))
    assert t_ref.count("· 缺 source") == 1, t_ref
    assert "缺 source.ref" in t_ref, t_ref

    t_full = todo_of(_mk(cues=["c"], source={"ref": "DOI:10.x", "kind": "教材"}))
    assert "没有待填项" in t_full, t_full

    # R8：空节点声明 未填充 → 合法，不报
    n_blank = _mk(id="con-0002", filled_by=EMPTY_FILLER, title="", scope="",
                  cues=[], source={"ref": "", "kind": ""}, notes="")
    assert not any(r == "R8" for _, r, _ in sevs([n_blank])), "空节点声明未填充，不该报 R8"

    # R8：有内容却声明 未填充 → WARN（⚠️ 暂定级，理由见 R8 块的注释）
    got = sevs([_mk(filled_by=EMPTY_FILLER)])
    assert any(s == "WARN" and r == "R8" for s, r, _ in got), got
    assert not any(s == "ERROR" for s, _, _ in got), "R8 是暂定 WARN，不该产生 ERROR"
    assert any("已经有这些字段" in m for _, r, m in got if r == "R8"), got

    # R8：「有名字的骨架」也必须不阻断。
    # 这正是 R8 暂定为 WARN 要保住的状态——先立骨架、内容慢慢填，
    # 是「空值合法」与待填清单存在的前提。判据未定案前，不能把这个状态判死。
    n_skeleton = _mk(id="con-0005", filled_by=EMPTY_FILLER, title="某个概念",
                     scope="", cues=[], source={"ref": "", "kind": ""}, notes="")
    got = sevs([n_skeleton])
    assert any(s == "WARN" and r == "R8" for s, r, _ in got), got
    assert not any(s == "ERROR" for s, _, _ in got), "有名字的骨架不该被 R8 阻断"

    # R8 只针对 未填充；别的取值不触发（取值本身不设白名单）
    assert not any(r == "R8" for _, r, _ in sevs([_mk(filled_by="人")]))

    # R8：source.kind 为空不算内容（未填 = 空字符串），写具体值才算
    n_kind_blank = _mk(id="con-0003", filled_by=EMPTY_FILLER, title="", scope="",
                       cues=[], source={"ref": "", "kind": ""}, notes="")
    assert not any(r == "R8" for _, r, _ in sevs([n_kind_blank])), "kind 为空不是内容"
    n_kind_real = _mk(id="con-0004", filled_by=EMPTY_FILLER, title="", scope="",
                      cues=[], source={"ref": "", "kind": "教材"}, notes="")
    assert any(r == "R8" for _, r, _ in sevs([n_kind_real])), "kind 写了具体值就该算内容"

    # R9：ref / kind 只填一半 → WARN；全空或全填 → 不报；且必须是警告级
    got = sevs([_mk(source={"ref": "DOI:10.x", "kind": ""})])
    assert any(s == "WARN" and r == "R9" for s, r, _ in got), got
    assert any("说不出类型" in m for _, r, m in got if r == "R9"), got
    assert not any(s == "ERROR" for s, _, _ in got), "R9 是警告级，不该产生 ERROR"

    got = sevs([_mk(source={"ref": "", "kind": "教材"})])
    assert any(s == "WARN" and r == "R9" for s, r, _ in got), got
    assert any("说不出出处" in m for _, r, m in got if r == "R9"), got

    assert not any(r == "R9" for _, r, _ in sevs([_mk()])), \
        "ref 与 kind 全空是合法状态（SPEC §一），不该报 R9"
    assert not any(r == "R9" for _, r, _ in
                   sevs([_mk(source={"ref": "DOI:10.x", "kind": "论文"})])), \
        "两样都填了不该报 R9"

    # R10：source.kind 必须在闭合枚举内；空字符串与字段缺失都合法
    got = sevs([_mk(source={"ref": "DOI:10.x", "kind": "未知"})])
    assert any(s == "ERROR" and r == "R10" for s, r, _ in got), got
    assert any("取值非法" in m for _, r, m in got if r == "R10"), got
    assert not any(r == "R9" for _, r, _ in got), "ref 与 kind 都有值，不该顺带报 R9"

    assert not any(r == "R10" for _, r, _ in sevs([_mk()])), \
        "kind 是空字符串（未填）合法，不该报 R10"
    assert not any(r == "R10" for _, r, _ in
                   sevs([_mk(source={"ref": "DOI:10.x", "kind": "访谈口述"})])), \
        "枚举内的取值不该报 R10"
    n_kind_missing = _mk()
    del n_kind_missing.data["source"]["kind"]
    assert not any(r == "R10" for _, r, _ in sevs([n_kind_missing])), \
        "kind 字段缺失合法（required: false），不该报 R10"

    # --- schema 镜像必须与代码常量一致 ---
    path = Path(__file__).resolve().parent.parent / "schema" / "node.schema.yaml"
    schema = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert set(schema["types"]) == set(PREFIX), "schema 的 types 与代码不一致"
    assert "aliases" in schema["fields"], "schema 缺 aliases 字段"
    assert "aliases" in REQUIRED_FIELDS, "REQUIRED_FIELDS 缺 aliases"
    assert {k: v["prefix"] for k, v in schema["types"].items()} == PREFIX, "前缀映射不一致"
    assert set(schema["fields"]) == set(REQUIRED_FIELDS), "字段清单不一致"
    es = schema["fields"]["evidence_status"]
    assert tuple(es["user_writable"]) == USER_WRITABLE_STATUS, "用户可写状态不一致"
    assert es["default"] == DEFAULT_STATUS, "默认状态不一致"
    assert tuple(es["hook_only"]) == (HOOK_ONLY_STATUS,), "hook-only 状态不一致"

    # --- 以下键此前不在守护范围内，可以静默漂移；现已纳入 ---
    f = schema["fields"]
    assert f["id"]["pattern"] == ID_PATTERN, "schema 的 id.pattern 与 ID_PATTERN 不一致"
    for key in REQUIRED_FIELDS:
        assert f[key].get("required") is True, f"schema 的 {key}.required 应为 true"
    assert f["cues"].get("severity") == "WARN", "schema 的 cues.severity 应为 WARN（R6 是警告级）"
    fb = f["filled_by"]
    assert tuple(fb["convention"]) == FILLER_CONVENTIONS, "filled_by.convention 与代码不一致"
    assert fb["convention_pattern"] == FILLER_MODEL_PATTERN, "filled_by.convention_pattern 不一致"
    assert fb["value_whitelist"] is False, "filled_by.value_whitelist 应为 false（取值不设白名单）"
    assert fb["empty_marker"] == EMPTY_FILLER, "filled_by.empty_marker 与 EMPTY_FILLER 不一致"
    kd = f["source"]["fields"]["kind"]
    assert tuple(kd["enum"]) == SOURCE_KINDS, "schema 的 source.kind.enum 与 SOURCE_KINDS 不一致"
    assert kd.get("empty_means") == "未填", "schema 的 source.kind.empty_means 应为 未填"

    print("self-test 通过：R1–R10 触发正常，schema 镜像一致。")
    print("（校验器只读：不写文件、不修复、不排序。）")
    return 0


def main(argv=None) -> int:
    # Windows 上管道默认按 cp936 编码，中文全是乱码。强制 UTF-8。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    ap = argparse.ArgumentParser(
        description="知识结构校验器：只诊断结构自洽，不判断内容对错。")
    ap.add_argument("root", nargs="?", help="要校验的目录，例如 ./samples")
    ap.add_argument("--allow-verified", action="store_true",
                    help="允许 已验证 存在。仅当校验来源是 hooks 授权的输出目录时才可启用。默认关闭。")
    ap.add_argument("--self-test", action="store_true", help="跑内置自检，不读任何数据文件。")
    ap.add_argument("--todo", action="store_true",
                    help="输出待填清单：只列缺口，不给答案，不按权威度排序。")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.root:
        ap.error("需要给一个目录，例如：python validator/validate.py ./samples")

    root = Path(args.root)
    if not root.is_dir():
        print(f"不是目录：{root}")
        return 2

    nodes = collect(root)
    if not nodes:
        print(f"{root} 下没有找到任何 *.md 节点。")
        return 0

    if args.todo:
        return todo_report(nodes)

    if args.allow_verified:
        print("⚠ --allow-verified 已启用：本次不把「已验证」视为越权。")
        print("  该开关只允许用于 hooks 授权的输出目录。\n")

    return report(check(nodes, allow_verified=args.allow_verified), len(nodes))


if __name__ == "__main__":
    sys.exit(main())
