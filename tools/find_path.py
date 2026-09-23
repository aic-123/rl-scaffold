#!/usr/bin/env python3
# Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0
"""按需求检索：把你描述的处境，变成一条**可行路径**，而不是一张平面表。

    python tools/find_path.py --problem "日志里 entropy 一路往下掉，我不知道要不要停"
    python tools/find_path.py --entry judge-0001     # 已知入口，直接出路径
    python tools/find_path.py --list                 # 不匹配，按处境自己找
    python tools/find_path.py --check                # 自检（退出码非 0 即失败）

## 为什么要有它

`index/view.html` 与 `index/by-situation.md` 是**平面**的：75 条处境平铺，
顺序由 `SORT_SPEC` 决定（文件路径）。要查得先知道自己在找什么。
这个工具补的是另一半：**从你嘴里的话走到一个入口，再沿 relations 走出一条链**。

## 检索规格（改这里就是改检索行为）

MATCH_SPEC 是下面那个常量。它和 SORT_SPEC 是两条独立的规格，遵守同一条底线。

## 一条由**代码结构**保证的纪律，不是由注释保证的

`_match_record()` 在解析阶段就把 `source` / `source.ref` / `source.kind` /
`evidence_status` / `filled_by` **全部丢掉**。

→ 打分函数**拿不到**这些字段。所以"来源与证据状态不参与匹配"不是一句承诺，
是**它在内存里根本不存在**。`--check` 会实测这一点。

理由和视图层一样：**排序即推荐**。匹配分也是一样——
分高只说明"你这句话和那条处境描述得近"，**不说明那条更该信**。

## 路径模板（六步）与它的诚实规则

    ① 先看什么     判断点的 `变量：` 行 + 正文「怎么确认」节的步骤 + 正文里的判据数值
    ② 为什么       概念，直连优先，没有直连就走 议题/例外 转一手并**标注是间接的**
    ③ 什么情况下不成立   例外（出边 + 入边）
    ④ 背后有没有争论     议题（图上 ≤2 跳）+ 立场 + 论据 + 案例
    ⑤ 别人怎么做的       案例，**按挂载强度分三级**：直接 / 经论据 / 经概念·弱
    ⑥ 接下来可能撞上     分诊支路（直连的其它判断点）+ 共享概念的其它判断点

**空步必须说"空"，不许静默省略。** 而且要说清是「没找到」而不是「不存在」——
本结构的 `relations` 只收有向边，正文里写的反向关系不进图。

## 验收只有一张表（`SELF_TEST`），但它有两种条目

- **只断入口的**：证明"已有的入口还找得到"。这是回归。
- **还带内容断言的**：证明"路径里该出现的内容确实出现了"。这是覆盖。

**入口齐不齐，只能靠第二类来撞**——自己照节点编的句子证明不了覆盖。

⚠️ **但不为外部用例另开一层。**
「如果遇到这种情况怎么办」**就是症状口吻的一种说法**，走的就是正常检索。
给它单开一张表、单开一个命令，等于把一个已有的入口包装成新类别。
外部用例的"外来身份"写在 `说明` 里就够了，不需要一个字段。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "nodes"

# ── 检索规格：改这里就是改检索 ─────────────────────────────────────────
MATCH_SPEC = {
    "匹配键": "处境句（cues）+ 标题 + 别名（aliases）。"
    "⚠️ **适用范围（scope）的中文正文不参与打分**——它只贡献其中的**拉丁标识符 token**"
    "（如 `grad_norm`），走 `_hay_tokens` / IDF 那条路。"
    "旧版这里写的是「+ 适用范围（scope）」，读起来像 scope 全文参与匹配，**那是虚的**。"
    "⚠️ 为什么不干脆让 scope 全文参与：scope 里含「**不适用于…**」的表述，"
    "一旦参与匹配，**恰恰会在查询落进排除范围时把该节点抬得更高**——方向是反的。"
    "（实测：查询与 scope 的排除句重合 Dice=0.194 / LCS=8，而正常查询最高 0.146 / 4，"
    "两者**分不开**，所以「自动警示」也没做成，见 `AUDIT.md` §六·补。）",
    "算法": "中文按字符二元组重合（Dice 系数），取 cue / 标题 / 别名三者的加权最大；"
    "英文与数字标识符按 token 集合精确命中，且按稀有度（IDF）加权——"
    "命中罕见的 grad_norm 是强证据，命中烂大街的 kl 不是。",
    "标识符是乘不是加": "标识符的作用是**放大已有的文本重合**，不是单独加分。"
    "加法会让一个常见词把「与查询零文本重合」的节点抬过阈值，"
    "等于让一个词替读者决定看哪个节点。",
    "入口优先判断点": "若最高分不是判断点，而某个判断点**也在同一个量级**"
    "（分数 ≥ 最高分 × 0.5，且自己过阈值、且 `cue_dice > 0`），"
    "改判给那个判断点，并把改判**打印出来**。"
    "依据是 ADAPT.md §一 已记在案的决议：「判断点作为主入口」。"
    "够不着就照实返回，不硬凑。"
    "为什么门槛是**相对最高分**而不是相对阈值："
    "入口之争只发生在两个候选**分数接近**时（实测：概念 0.45 vs 判断点 0.38，比值 0.84）；"
    "而当用户那句话**明确指向**另一个节点时，两者会差一个量级"
    "（实测：概念 1.90 vs 判断点 0.27，比值 0.14）——那种情况下改判是**抢**入口。"
    "⚠️ 0.5 这个数是**拍的**，但它写在规格里、带着上面两组实测；"
    "旧址用的是「≥ 阈值 × 0.8」且**从没写进规格**，后果是概念自身得分 1.90 的查询"
    "被 0.27 分的判断点顶掉（实测 81 条处境原句里有 13 条没回到自己的节点）。见 AUDIT.md §二.2。",
    "明确排除": [
        "来源（source.ref / source.kind）",
        "机构、作者",
        "证据状态（evidence_status）",
        "填充者（filled_by）",
        "任何形式的权威度加权",
    ],
    "排除方式": "在解析阶段丢弃——打分函数在内存里拿不到这些字段，不是靠自觉",
    "阈值": 0.18,
    "阈值为什么是 0.18（2026-09-23 实测扫描，不是拍的）":
    "背景：留出集（与 cues 不同的说法）命中率只有 9/17，看着像「匹配算法不认同义改写」。"
    "**实测发现不是**——17 句里那 8 句「没匹配上」的，**正确节点全都已经是最高分**，"
    "只是没过阈值。所以瓶颈在**阈值**，不在算法。"
    "扫描（左=留出命中，右=越界负例最高分）："
    "0.30 → 9/17（负例 0.14）｜0.22 → 13/17（0.14）｜**0.18 → 15/17（0.14）**｜"
    "0.16 → 15/17（0.14）｜0.14 → 15/17（**负例过线**）｜0.12 → 17/17（**负例过线**）。"
    "→ 取 **0.18**：它是**能到 15/17 的最大阈值**，因此安全边距也最大（0.14 → 0.18，0.04）。"
    "⚠️ 边距只有 0.04，**很薄**；所以「离得更近的越界句」必须进 `SELF_TEST` 当负例钉住"
    "（已把「我的显卡坏了怎么办」0.14 与「公司不给我批算力」0.11 补进去）。"
    "⚠️ 想再往上抬命中率，就得动匹配算法，而每种改法都会**抬高所有分数**——"
    "那会把负例一起抬过线。**那是 D-04 级别的事，见 DECISIONS.md。**",
    "低于阈值怎么办": "如实说「没匹配上」，并列出最接近的三条让你自己挑。"
    "不猜、不兜底、不硬凑一个答案给你。",
    "判断点必须靠处境句进（2026-09-23 新增门槛）":
    "**判断点作为入口时，它的 `cue_dice` 也必须过阈值。**"
    "说人话：**我接住的必须是你的一句话，不能是你的一个词。**"
    "为什么只卡判断点、不卡概念/案例：面试者入口本来就允许**靠名字**进概念节点"
    "（「组内归一化是怎么算的」→ `con-0001`，它的 `cue_dice` 是 **0.00**，"
    "而那是**合法**的——问的是概念名）。一刀切会把面试者入口打死。"
    "实测收益（阈值 0.18 时）：**留出集命中不损失（仍 15/17）**，"
    "而「靠一个词硬落下来」的可疑命中从 4 条降到 1 条——"
    "其中一条是真落错：「我要不要上 RL」曾落到 `judge-0013`（长度惩罚），靠的只是一个 `rl`。"
    "⚠️ 它也可能把「本来能兜住、只是 cue 写得不好」的查询判成没匹配上——"
    "**那是可接受的：宁可说「没匹配上」并列出最近的几条，也不要给一个靠名字猜的答案。**",
    "为什么": "匹配分只衡量「你这句话和哪条处境描述得近」，"
    "与来源、机构、证据状态无关。分高不等于该信它。",
    "路径模板": "六步：先看什么 → 为什么 → 什么情况下不成立 → 背后的争论 → "
    "别人怎么做的 → 接下来可能撞上什么。"
    "① 里必须有**三件**：变量（看什么）、怎么测（怎么看，取自正文的「怎么确认」节）、"
    "判据（到什么程度算数）。**只给变量名不给测法，等于没给。**",
}

TAU = MATCH_SPEC["阈值"]

# 匹配器允许看到的字段白名单。不在这个集合里的，一律不进内存。
MATCH_FIELDS = ("id", "type", "title", "aliases", "cues", "scope", "relations")

_TYPE_ORDER = ["概念", "判断点", "条件", "例外", "议题", "立场", "论据", "断言", "案例"]

_PUNCT_RE = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9]+")
_ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.@/-]{1,}|\d+\.\d+")
_ID_STRIP_RE = re.compile(r"[^a-z0-9@]")


# ── 解析：只留白名单字段 ───────────────────────────────────────────────

def load_raw(path: Path) -> dict | None:
    """读 front matter，返回**全部**字段（视图层用）。"""
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


def _match_record(raw: dict) -> dict:
    """**唯一的入口**：把原始节点缩成匹配器能看到的样子。

    这一步是纪律的落点——`source` / `evidence_status` / `filled_by`
    在这里被丢掉，下游代码再也拿不回来。
    """
    return {k: raw.get(k) for k in MATCH_FIELDS}


def load_all() -> tuple[dict[str, dict], dict[str, dict]]:
    """返回 (raw_by_id, match_by_id)。两个视图共用同一份解析。"""
    raw_by_id: dict[str, dict] = {}
    for p in sorted(NODES.glob("*.md")):
        raw = load_raw(p)
        if raw and raw.get("id"):
            raw_by_id[str(raw["id"])] = raw
    match_by_id = {nid: _match_record(raw) for nid, raw in raw_by_id.items()}
    _TITLES.clear()
    _TITLES.update({nid: str(n["title"]) for nid, n in match_by_id.items()})
    _build_idf(match_by_id)
    return raw_by_id, match_by_id


def _hay(node: dict) -> str:
    return " ".join([
        str(node.get("title") or ""),
        *[str(a) for a in (node.get("aliases") or [])],
        *[str(c) for c in (node.get("cues") or [])],
        str(node.get("scope") or ""),
    ])


# 标识符的稀有度。为什么需要它：
#   「kl」这种词几乎每个节点都有，命中它说明不了什么；
#   「grad_norm」只在一个节点里出现，命中它就是强证据。
#   不做这个区分的话，一个烂大街的词就能把分数抬到阈值以上。
_IDF: dict[str, float] = {}
_IDF_MAX = 3.0


def _build_idf(match_by_id: dict[str, dict]) -> None:
    import math
    n = max(len(match_by_id), 1)
    df: dict[str, int] = {}
    for node in match_by_id.values():
        for t in _hay_tokens(node):
            df[t] = df.get(t, 0) + 1
    _IDF.clear()
    for t, c in df.items():
        _IDF[t] = min(math.log(n / (1 + c)) + 0.35, _IDF_MAX)


def _idf(t: str) -> float:
    # 表里没有 = 全库唯一，给最高权重
    return _IDF.get(t, _IDF_MAX)


# ── 文本相似：确定性，无模型 ────────────────────────────────────────────

def _norm(s) -> str:
    return _PUNCT_RE.sub("", str(s).lower())


def _norm_id(s) -> str:
    return _ID_STRIP_RE.sub("", str(s).lower())


def _bigrams(s) -> set[str]:
    s = _norm(s)
    if len(s) < 2:
        return {s} if s else set()
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _dice(a, b) -> float:
    A, B = _bigrams(a), _bigrams(b)
    if not A or not B:
        return 0.0
    return 2 * len(A & B) / (len(A) + len(B))


def _ids(s) -> set[str]:
    """抽出标识符**集合**（不是拼接串）。

    两件事都要做对，否则会出现假命中：

    1. **按 token 比，不按子串比。** 用子串的话 `kl` 会命中 `klcov`——
       于是「KL-Cov」这个别名会把一个跟查询毫不相关的节点抬过阈值。
    2. **长标识符要拆。** `actor/grad_norm` 得同时产出 `actor`、`grad`、
       `gradnorm`，不然用户写全路径时就匹配不上只写 `grad_norm` 的节点。
    """
    out: set[str] = set()
    for m in _ID_RE.finditer(str(s)):
        raw = m.group(0)
        for part in re.split(r"[/_.@-]", raw):
            p = _norm_id(part)
            if len(p) >= 2:
                out.add(p)
        full = _norm_id(raw)
        if len(full) >= 2:
            out.add(full)
    return out


def _hay_tokens(node: dict) -> set[str]:
    return _ids(_hay(node))


def score(query: str, node: dict) -> tuple[float, dict]:
    """给一条处境描述和一个节点打分。返回 (分, 依据)。

    依据是给人核对的：命中了哪条 cue、哪些标识符、各分项多少。
    分数本身不可核对，依据可以。
    """
    cues = [str(c) for c in (node.get("cues") or []) if str(c).strip()]
    title = str(node.get("title") or "")
    aliases = [str(a) for a in (node.get("aliases") or [])]

    q_ids = _ids(query)
    hits = sorted(q_ids & _hay_tokens(node))

    best_cue, cue_d = "", 0.0
    for c in cues:
        d = _dice(query, c)
        if d > cue_d:
            best_cue, cue_d = c, d

    title_d = _dice(query, title)
    alias_d = max((_dice(query, a) for a in aliases), default=0.0)

    # 标识符按稀有度加权，并且**乘在文本分上**，不是加在旁边。
    # 为什么必须乘：加法会让一个烂大街的词（kl）把「和查询毫无文本重合」的
    # 节点也抬过阈值——那等于让一个词替读者决定看哪个节点。
    # 乘法的作用是**放大已有的证据**：本来不像，命中一个词也还是不像。
    id_weight = sum(_idf(t) for t in hits)
    id_factor = 0.9 * min(id_weight / 3.0, 1.0)

    base = max(cue_d, 0.75 * title_d, 0.70 * alias_d)
    total = base * (1.0 + id_factor)
    why = {
        "cue": best_cue, "cue_dice": round(cue_d, 3),
        "title_dice": round(title_d, 3), "alias_dice": round(alias_d, 3),
        "ids": hits, "id_factor": round(id_factor, 3),
    }
    return total, why


def rank(query: str, match_by_id: dict[str, dict]) -> list[tuple[str, float, dict]]:
    rows = []
    for nid, node in match_by_id.items():
        s, why = score(query, node)
        if s > 0:
            rows.append((nid, s, why))
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows


# ── 路径：从入口沿 relations 走出一条链 ────────────────────────────────

def _type(match_by_id: dict, nid: str) -> str:
    n = match_by_id.get(nid)
    return str(n.get("type")) if n else ""


def _rel(match_by_id: dict, nid: str) -> list[str]:
    n = match_by_id.get(nid) or {}
    return [str(r) for r in (n.get("relations") or []) if str(r) in match_by_id]


def build_reverse(match_by_id: dict[str, dict]) -> dict[str, list[str]]:
    rev: dict[str, list[str]] = {nid: [] for nid in match_by_id}
    for nid in match_by_id:
        for t in _rel(match_by_id, nid):
            rev[t].append(nid)
    return rev


def _of(match_by_id: dict, ids, typ: str) -> list[str]:
    return [i for i in ids if i in match_by_id and _type(match_by_id, i) == typ]


def _var_line(raw: dict) -> str | None:
    m = re.search(r"变量\s*[:：]\s*(.+)", raw.get("_body") or "")
    return m.group(1).strip() if m else None


_CRIT_KEYS = ("判据", "高于", "低于", "超过", "阈值")
# ⚠️ 2026-09-23 修正：旧版只认**小数**（`\d+\.\d+`），于是
#   「判据：奖励标准差等于 0。」→ 提取为空
#   「判据：超过 50% 时复查。」  → 提取为空
#   实测后果：全库 9 个判断点里**只有 judge-0006 提得出判据**，其余 8 个的 ①
#   第三件（判据）是**静默缺失**的——路径看起来完整，其实是少了一整件。
#   见 AUDIT.md §二.4。
_CRIT_NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*%?")
# ⚠️ 只把「序号」去掉再找数字——否则「第 2 步才是判据，第 1 步只是信号」这种
#    散文会被当成判据行（放宽数字口径后实测到的假阳性）。
_CRIT_NOISE_RE = re.compile(r"第\s*\d+\s*步|^\s*\d+[.、)]")
# 反向守卫：这些话说的是「**没有**判据」，不能当成判据捞出来。
_CRIT_NEG = ("不给阈值", "不给判据", "没有阈值", "没有判据", "不替你做", "不给出")


def _crit_lines(raw: dict, limit: int = 3) -> list[str]:
    """从正文里抠出**判据行**。两条通路，命中任一条即算：

    **通路 A（显式标签）**：这一行以 `判据` 开头。
    **通路 B（启发式）**：这一行同时有**数字**（整数/小数/百分比）和判据关键词。

    ⚠️ 2026-09-23 加通路 A 的原因：**事前/选型类判断点的判据往往是条件式的**，
    不带数值——例如「如果格式检查项里出现长度相关项，格式分就会随长度变化」。
    只认数字的话，这类判据会被判成"缺失"，于是 ① 看起来残缺。
    **而显式写了「判据：」的行是一个比"有数字"更可靠的信号**——
    它是写的人**主动声明的**，不是启发式猜的。

    两条通路都先过**否定守卫**：说「本节点不给判据线」的那种行，不是判据。
    """
    out = []
    for ln in (raw.get("_body") or "").splitlines():
        s = ln.strip()
        if not s or s.startswith("|") or s.startswith("#"):
            continue
        if any(k in s for k in _CRIT_NEG):
            continue
        bare = re.sub(r"\*\*|`", "", s).strip()
        # 引出语守卫：以冒号 / 破折号收尾的行是"下面就是…"，**它本身不是判据**。
        # 实测踩到：`判据——这条最有价值的地方是它给了数值：` 被通路 A 捞了出来。
        if bare.endswith(("：", ":", "——", "—")):
            continue
        labeled = re.sub(r"^[-*·\s]+", "", bare).startswith("判据")
        numeric = (bool(_CRIT_NUM_RE.search(_CRIT_NOISE_RE.sub("", s)))
                   and any(k in s for k in _CRIT_KEYS))
        if not (labeled or numeric):
            continue
        t = re.sub(r"\*\*|`", "", s).lstrip("- ").strip()
        if t and t not in out:
            out.append(t)
        if len(out) >= limit:
            break
    return out


def _first_sentence(raw: dict, limit: int = 88) -> str:
    t = re.sub(r"\*\*|`", "", raw.get("_body") or "")
    t = re.sub(r"\s+", " ", t).strip()
    i = t.find("。")
    if 0 < i <= limit:
        return t[: i + 1]
    return t[:limit] + ("…" if len(t) > limit else "")


# ① 除了「看什么」，还得给「怎么看」。
# 为什么：`变量：` 行只列出量名，不给测法。**一个测不出来的变量等于没给。**
# 这个缺口是被一个外部考验用例撞出来的：对方问「审计到 50% 的 rollout 推对了
# 却给了 0 分，怎么办」——系统当时能说出「假阴性率」这个名字，
# 却不说这个数怎么得到（而节点正文里写着）。见 ADAPT.md §十三。
_HOWTO_HEADS = ("怎么确认", "怎么测", "怎么查", "如何确认", "怎么判断")
_HOWTO_MARK = "怎么测这些量（本节点正文给的步骤）："
# ①宣称有「三件」：变量 → 怎么测 → 判据。第三件**没有的时候要明说**，
# 不能静默少一行——实测全库 9 个判断点里 8 个的第三件是空的，
# 而路径看起来是完整的（AUDIT.md §二.4）。缺了就说缺了。
_NO_CRIT_MARK = ("判据：**本节点正文没有给出可抠的数值判据**——"
                 "这一件是缺的，不是不重要。")


def _howto_steps(raw: dict, limit: int = 6) -> list[str]:
    """抠出正文里「怎么确认 / 怎么测」那一节的**编号步骤**。

    只认 `## ` 小节，且小节标题要命中 _HOWTO_HEADS。
    只收 `1. …` / `- …` 形式的条目——散文段落不收，
    因为 ① 是清单，不是摘要。

    ⚠️ 2026-09-23 修正：**续行要并进上一步，不能丢。**
    旧版只收 `^\\d+\\.` 开头的行，于是把一个跨两行写的步骤**后半句静默丢掉**：
        探针输入："1. 检查输入样本\\n   同时保留人工复核标记。"
        旧版提取：["检查输入样本"]        ← 后半句没了
    后果很坏：**路径看起来完整，其实断在半句话上**，而且不报错。
    现在缩进续行会被并进上一步。详见 AUDIT.md §二.4。
    """
    out: list[str] = []
    inside = False
    for ln in (raw.get("_body") or "").splitlines():
        s = ln.strip()
        if s.startswith("## "):
            inside = any(k in s for k in _HOWTO_HEADS)
            continue
        if not inside or not s:
            continue
        m = re.match(r"^\d+[.、)]\s*(.+)$", s)
        if not m and s.startswith("- "):
            m = re.match(r"^-\s*(.+)$", s)
        if m:
            t = re.sub(r"\*\*|`", "", m.group(1)).strip()
            if t and t not in out:
                out.append(t)
            continue
        # 缩进续行 → 并进上一步（而不是丢掉）
        if out and (ln[:1] in (" ", "\t")) and not s.startswith(("|", ">", "#")):
            t = re.sub(r"\*\*|`", "", s).strip()
            if t and not out[-1].endswith(t):
                out[-1] = out[-1] + " " + t
        if len(out) >= limit:
            break
    return out


def build_path(match_by_id: dict[str, dict], raw_by_id: dict[str, dict],
               entry: str) -> dict:
    """从入口节点走出一条六步路径。纯函数，CLI 与 HTML 视图共用它。"""
    rev = build_reverse(match_by_id)
    node = match_by_id[entry]
    raw = raw_by_id[entry]

    # ① 先看什么。只有判断点才有判据；其它类型给适用范围，不硬凑。
    #    顺序是：看什么（变量）→ 怎么看（正文给的步骤）→ 到什么程度算数（判据数值）。
    if node["type"] == "判断点":
        step1 = [x for x in [_var_line(raw)] if x]
        how = _howto_steps(raw)
        if how:
            step1.append(_HOWTO_MARK)
            step1 += [f"  {i}. {x}" for i, x in enumerate(how, 1)]
        crit = _crit_lines(raw)
        step1 += crit if crit else [_NO_CRIT_MARK]
    else:
        step1 = [f"（这条不是处境，是「{node['type']}」——它没有判据。）",
                 f"适用范围：{node.get('scope') or '（未填）'}"]

    # ② 为什么：直连优先；没有直连就走 议题/例外 转一手，并标注
    direct_con = _of(match_by_id, _rel(match_by_id, entry), "概念")
    indirect_con: dict[str, str] = {}
    if not direct_con:
        mids = _rel(match_by_id, entry) + rev.get(entry, [])
        for mid in mids:
            if _type(match_by_id, mid) in ("议题", "例外"):
                for c in _of(match_by_id, _rel(match_by_id, mid), "概念"):
                    indirect_con.setdefault(c, mid)
    step2 = [{"id": c, "via": None, "text": _first_sentence(raw_by_id[c])}
             for c in direct_con]
    step2 += [{"id": c, "via": v, "text": _first_sentence(raw_by_id[c])}
              for c, v in sorted(indirect_con.items())]

    # ③ 例外：出边 + 入边（两个方向都算，方向本来就不止一种）
    excs = [{"id": e, "dir": "出边"} for e in _of(match_by_id, _rel(match_by_id, entry), "例外")]
    excs += [{"id": e, "dir": "入边"} for e in _of(match_by_id, rev.get(entry, []), "例外")]
    step3 = [{"id": e["id"], "dir": e["dir"], "text": _first_sentence(raw_by_id[e["id"]])}
             for e in excs if e["id"] in raw_by_id]

    # ④ 议题：图上 ≤2 跳
    frontier = {entry} | set(_rel(match_by_id, entry)) | set(rev.get(entry, []))
    issues: dict[str, int] = {}
    for hop in (1, 2):
        nxt: set[str] = set()
        for x in frontier:
            if x not in match_by_id:
                continue
            if _type(match_by_id, x) == "议题" and x != entry:
                issues[x] = hop
            nxt |= set(_rel(match_by_id, x)) | set(rev.get(x, []))
        frontier = nxt
    step4 = []
    for i in sorted(issues):
        stances = []
        for s in _of(match_by_id, rev.get(i, []), "立场"):
            args = []
            for a in _of(match_by_id, rev.get(s, []), "论据"):
                args.append({"id": a, "title": match_by_id[a]["title"],
                             "cases": _of(match_by_id, rev.get(a, []), "案例")})
            stances.append({"id": s, "title": match_by_id[s]["title"], "args": args})
        step4.append({"id": i, "title": match_by_id[i]["title"],
                      "hops": issues[i], "stances": stances})

    # ⑤ 案例：分三级挂载强度（案例的 relations 方向 SPEC 不作约定，粒度本来就不齐）
    direct_cases = _of(match_by_id, _rel(match_by_id, entry), "案例")
    strong: set[str] = set()
    for it in step4:
        for st in it["stances"]:
            for ar in st["args"]:
                strong |= set(ar["cases"])
    weak: set[str] = set()
    for x in direct_con + list(indirect_con) + [e["id"] for e in excs]:
        weak |= set(_of(match_by_id, rev.get(x, []), "案例"))
    weak -= strong
    step5 = ([{"id": c, "grade": "直接"} for c in direct_cases]
             + [{"id": c, "grade": "经论据"} for c in sorted(strong)]
             + [{"id": c, "grade": "经概念·弱"} for c in sorted(weak)])
    step5 = [dict(x, title=match_by_id[x["id"]]["title"]) for x in step5
             if x["id"] in match_by_id]

    # ⑥ 相邻判断点
    # 先走「分诊支路」：入口直接连着的其它判断点。
    # 为什么必须先走它：分诊型节点（如 judge-0009）的全部内容就是"该去看哪一条"，
    # 而那些分支是**直连的**、不共享概念——只按概念找邻居会让它们整个隐身。
    step6 = []
    seen6: set[str] = set()
    for j in _of(match_by_id, _rel(match_by_id, entry), "判断点"):
        if j != entry and j not in seen6:
            seen6.add(j)
            step6.append({"id": j, "title": match_by_id[j]["title"], "via": "分诊支路"})
    for c in direct_con + list(indirect_con):
        for j in rev.get(c, []):
            if _type(match_by_id, j) == "判断点" and j != entry and j not in seen6:
                seen6.add(j)
                step6.append({"id": j, "title": match_by_id[j]["title"], "via": c})
    for e in [x["id"] for x in excs]:
        for j in _rel(match_by_id, e) + rev.get(e, []):
            if _type(match_by_id, j) == "判断点" and j != entry and j not in seen6:
                seen6.add(j)
                step6.append({"id": j, "title": match_by_id[j]["title"], "via": e})

    triage = any(x["via"] == "分诊支路" for x in step6)

    return {
        "entry": entry,
        "type": node["type"],
        "title": node["title"],
        "cues": list(node.get("cues") or []),
        "scope": node.get("scope") or "",
        "triage": triage,
        "steps": {"①": step1, "②": step2, "③": step3,
                  "④": step4, "⑤": step5, "⑥": step6},
    }


# ── 文本输出 ──────────────────────────────────────────────────────────

RULE = "─" * 74
STEP_NAMES = {
    "①": "先看什么（变量 → 怎么测 → 判据）",
    "②": "为什么（机制）",
    "③": "什么情况下上面这套不成立",
    "④": "这背后有没有争论",
    "⑤": "别人怎么做的",
    "⑥": "接下来可能撞上",
}


def _via_label(via: str) -> str:
    """分诊支路是直连的，不是「经由谁」——措辞要跟着关系走。"""
    return "（分诊支路：本节点直连）" if via == "分诊支路" else f"（经由 {via}）"


def _wrap(text: str, width: int = 66) -> list[str]:
    """按显示宽度折行。中文按 2 列算——`scope` 里常有一长串「不适用于…」。"""
    lines: list[str] = []
    cur, w = "", 0
    for ch in text:
        cw = 2 if ord(ch) > 0x2E80 else 1
        if w + cw > width and cur:
            lines.append(cur)
            cur, w = "", 0
        cur += ch
        w += cw
    if cur:
        lines.append(cur)
    return lines


def render_text(path: dict, why: dict | None = None, alts=None) -> str:
    out: list[str] = []
    A = out.append
    A(RULE)
    A(f"■ {path['entry']} · {path['title']}")
    A(RULE)
    # ⚠️ 2026-09-23 修正：`scope` 必须输出，尤其是「不适用于」那半句。
    # 旧版一个字都不打印，后果是系统会给出**明确不适用于用户**的答案而用户看不见：
    # 实测「我的奖励来自奖励模型，reward 崩了」→ judge-0009（1.40），
    # 而该节点 scope 第一句就是「不适用于奖励来自奖励模型或人工标注的场景」。
    # 见 AUDIT.md §二.3。
    scope = re.sub(r"\*\*|`", "", str(path.get("scope") or "")).strip()
    if scope:
        A("")
        A("⚠️ 适用范围（先看这句能不能排除你）")
        for line in _wrap(scope):
            A("   " + line)
    if path["cues"]:
        A("")
        A(f"  这条处境的原话：「{path['cues'][0]}」")
    if why:
        A("")
        A(f"  为什么是它：处境句重合 {why['cue_dice']}，"
          f"标题 {why['title_dice']}，别名 {why['alias_dice']}"
          + (f"，标识符命中 {'、'.join(why['ids'])}（放大 ×{1 + why['id_factor']:.2f}）"
             if why["ids"] else ""))
        A(f"  最像的那条 cue：「{why['cue']}」")
    A("")

    s = path["steps"]

    A("①  " + STEP_NAMES["①"])
    if s["①"]:
        for line in s["①"]:
            A("    " + line)
    else:
        A("    ⚠️ 空——这个节点没有 `变量：` 行，也没有可抠的判据数值。")
    A("")

    A("②  " + STEP_NAMES["②"])
    if s["②"]:
        for c in s["②"]:
            tag = "（直连）" if not c["via"] else f"（经 {c['via']} 间接）"
            A(f"    · {c['id']} {match_title(c)}{tag}")
            A(f"      {c['text']}")
    else:
        A("    ⚠️ 空——它连不到任何概念。注意这是「没找到」，不是「不存在」：")
        A("       概念层有 8 个节点，但 relations 里没有从它出发的边。")
    A("")

    A("③  " + STEP_NAMES["③"])
    if s["③"]:
        for e in s["③"]:
            A(f"    · {e['id']} {match_title(e)}（{e['dir']}）")
            A(f"      {e['text']}")
    else:
        A("    （未登记例外——是「没找到」，不是「不存在」）")
    A("")

    A("④  " + STEP_NAMES["④"])
    if s["④"]:
        for it in s["④"]:
            A(f"    · 议题 {it['id']} {it['title']}　（图上 {it['hops']} 跳）")
            for st in it["stances"]:
                A(f"        └ 立场 {st['id']} {st['title']}")
                for ar in st["args"]:
                    A(f"            └ 论据 {ar['id']} {ar['title']}")
                    for c in ar["cases"]:
                        A(f"                └ 案例 {c}")
    else:
        A("    （未登记议题——这个判断点目前是「有对策、无争论」）")
    A("")

    A("⑤  " + STEP_NAMES["⑤"])
    if s["⑤"]:
        for c in s["⑤"]:
            A(f"    · [{c['grade']}] {c['id']} {c['title']}")
        A("      注：[直接] 是这条判断点直接挂的案例；[经论据] 是挂在它这条争论链")
        A("          下面的；[经概念·弱] 是只挂在概念下面的。")
        A("          这三级说的是**挂在哪**，不是**哪条更可信**。")
    else:
        A("    ⚠️ 空——图上没有任何案例能走到它。")
    A("")

    A("⑥  " + ("该去看哪一条（分诊支路）" if path.get("triage") else STEP_NAMES["⑥"]))
    if s["⑥"]:
        for j in s["⑥"]:
            A(f"    · {j['id']} {j['title']}　{_via_label(j['via'])}")
    else:
        A("    （图里没有相邻判断点——它在判断点这一层是孤立的）")

    if alts:
        A("")
        A(RULE)
        A("这不是你要的？最接近的几条（按文本重合排，不代表更可信）：")
        for nid, sc, _ in alts:
            A(f"    {sc:5.2f}  {nid}  {match_title({'id': nid})}")
        A("    按处境自己找：python tools/find_path.py --list")

    A("")
    A("（本工具不判断内容对错，不建议采信任何一条。匹配分只衡量文本相近程度。）")
    return "\n".join(out)


_TITLES: dict[str, str] = {}


def match_title(item) -> str:
    return _TITLES.get(item["id"], "")


# ── --list ───────────────────────────────────────────────────────────

def cmd_list(match_by_id: dict[str, dict]) -> int:
    judges = [n for n in match_by_id.values() if n["type"] == "判断点"]
    judges.sort(key=lambda n: str(n["id"]))
    print(RULE)
    print("按处境自己找：下面是全部处境描述，按入口节点分组。")
    print("挑一条，然后跑 --entry <节点 id>。")
    print(RULE)
    for n in judges:
        print(f"\n■ {n['id']} · {n['title']}")
        for c in (n.get("cues") or []):
            print(f"    「{c}」")
    others = [n for n in match_by_id.values() if n["type"] != "判断点"]
    others.sort(key=lambda n: str(n["id"]))
    print("\n（其它类型节点没有处境句，见 index/view.html 的「按概念」。）")
    print(f"\n合计 {len(match_by_id)} 个节点，"
          f"{sum(len(n.get('cues') or []) for n in match_by_id.values())} 条处境。")
    return 0


# ── 自检 ─────────────────────────────────────────────────────────────

SELF_TEST = [
    # (你可能会说的话, 期望入口, 说明[, 断言])
    #
    # 这张表有两个用途，**但只有一张表**：
    #   · 大多数条目只断**入口**——那是回归，证明"已有的入口还找得到"
    #   · 少数条目还带第 4 个元素**断言**——那些多半是从外面来的
    #     （别人的考验、真实跑崩的现场），断的是"路径里该出现的内容有没有出现"
    #
    # ⚠️ **入口齐不齐，只能靠第二类来撞。**
    #    自己照节点编的句子只能证明自洽，证明不了覆盖。
    # ⚠️ 但**不为外部用例另开一张表**：「如果遇到这种情况怎么办」**就是症状口吻的一种说法**，
    #    它走的就是正常检索。给它单开一层，等于把一个已有的入口包装成新类别。
    ("日志里 entropy 一路往下掉，我不知道要不要停", "judge-0001", "逐字命中 cue"),
    ("我的模型回答越来越长，token 消耗翻了好几倍", "judge-0003", "逐字命中 cue"),
    ("actor/grad_norm 一直往上爬，调学习率也没用", "judge-0006", "标识符命中"),
    ("grad_norm 单调上升，是不是引擎的问题", "judge-0006", "换说法 + 标识符"),
    ("回答越来越像一个模子刻出来的", "judge-0001", "只给后半句"),
    ("一批 prompt 奖励全是 1，感觉没贡献梯度", "judge-0002", "换说法"),
    ("回答顶到最大长度被截断了，该给 0 分吗", "judge-0004", "换说法"),
    ("β 设多少合适，能不能干脆不开 KL", "judge-0005", "标识符 β 之外的词命中"),
    ("熵掉得太快，还剩多少可以烧", "judge-0007", "换说法"),
    ("熵崩了，但我不想重写整个损失函数", "judge-0008", "换说法"),
    # 2026-09-23 第四批之后补：主入口「reward 崩了」此前完全没有处境句，
    # 实测 cue 重合 0.000、标题重合 0.000——靠一个通用词 reward 才勉强落下来。
    # 下面五条钉住这条入口。
    ("reward 曲线跑到一半崩了，不知道先查哪里", "judge-0009", "主入口（新）"),
    ("训练跑了两百步 reward 就是不涨", "judge-0009", "主入口，换说法"),
    ("reward 崩了，是奖励函数写错了还是算法的问题", "judge-0009", "主入口，分诊口吻"),
    ("我怀疑有一批推对了的回答被判了 0 分", "judge-0004", "症状侧，指向具体分支"),
    ("verl 跑 Qwen 的 GRPO，跑到 200 步 reward 崩了", "judge-0009", "外部说法（对方举的例）"),
    # 对方举的例子的**完整原话**。它是一道题（"遇到这种情况你怎么办"），
    # 而那**就是症状口吻**——所以它进这张表，不进 nodes/。
    # 带断言：只断入口不够，还要断"该给的测法有没有给"。
    ("我基于 verl 跑 Qwen3.5 的 GRPO，跑到 200 步 reward 曲线崩了，"
     "审计发现有一半 rollout 推对了却给了 0 分",
     "judge-0009", "外部原话 + 断言（要求给出测法，不只是量名）",
     {
         # ① 必须同时给出「量名」和「测法」。只给量名就是被这道题撞出来的缺口。
         "①": ["假阴性率", "怎么测"],
         "②": ["con-0006"],
         "⑥": ["judge-0004"],
     }),
    # 2026-09-23 第七批：`B 事前 · 判分规则设计` 补了 4 个判断点，下面四条钉住它们的入口。
    # ⚠️ 这四条是**只断入口的回归条目**，证明"新入口找得到"。
    # **不要拿它们证明覆盖**——测同义改写的是 `probe_gaps.py --held`（那把尺子现在报 9/17）。
    ("我该不该给格式分", "judge-0011", "事前入口（新）"),
    ("我的判分规则用正则匹配，会不会有漏判", "judge-0010", "事前入口（新）"),
    ("要不要给中间步骤打分，还是只看最后答案", "judge-0012", "事前入口（新）"),
    ("奖励里要不要加长度惩罚", "judge-0013", "事前入口（新）"),
    ("我要不要上 RL，还是继续 SFT 就够了", "judge-0014", "选型入口（新，C2）"),
    ("今天天气怎么样", None, "负例：必须说没匹配上"),
    ("帮我写一首诗", None, "负例：必须说没匹配上"),
    # 2026-09-23 第七批：阈值从 0.30 降到 0.18 之后，**离得最近的越界句要钉住**。
    # 这两句是当前最贴近阈值的一对（0.14 / 0.11），边距只有 0.04——
    # 所以它们必须进表，否则下次谁把阈值再降一点，没人会发现越界已经破了。
    ("我的显卡坏了怎么办", None, "负例（最贴近阈值，0.14）：必须说没匹配上"),
    ("公司不给我批算力", None, "负例（次贴近，0.11）：必须说没匹配上"),
]

FORBIDDEN_IN_MATCH = ("source", "evidence_status", "filled_by", "_path", "_body")


# ── 断言辅助 ──────────────────────────────────────────────────────────
# 只断"入口对不对"是不够的：入口对了、内容缺了，一样是没接住。
# 所以 SELF_TEST 的少数条目多带一个断言字典，靠下面这个函数把步骤压成文本比对。

def _step_text(path: dict, key: str) -> str:
    """把一个步骤压成一段文本，供子串断言用。"""
    parts: list[str] = []
    for it in path["steps"].get(key) or []:
        if isinstance(it, str):
            parts.append(it)
        else:
            parts += [str(it.get("id", "")), str(it.get("title", "")),
                      str(it.get("text", "")), str(it.get("grade", ""))]
    return "\n".join(parts)


def check() -> int:
    raw_by_id, match_by_id = load_all()
    problems: list[str] = []

    # 1) 结构保证：匹配器拿不到来源与证据状态
    leaked = {f for rec in match_by_id.values() for f in rec if f in FORBIDDEN_IN_MATCH}
    if leaked:
        problems.append(f"匹配记录里漏出了不该有的字段：{sorted(leaked)}")
    rec = _match_record({"id": "x", "type": "概念", "title": "t",
                         "source": {"ref": "SECRET", "kind": "论文"},
                         "evidence_status": "已核实", "filled_by": "SECRET"})
    if "SECRET" in str(rec) or "已核实" in str(rec):
        problems.append("_match_record 没有真的丢掉来源 / 证据状态字段")

    # 2) 每条路径的引用都能解析（无悬挂 id）
    #    注意：① 是自由文本（变量行 / 判据行），没有节点引用，跳过它。
    for nid in sorted(match_by_id):
        p = build_path(match_by_id, raw_by_id, nid)
        for k, items in p["steps"].items():
            if k == "①":
                continue
            ids = []
            for it in items:
                if k == "④":
                    ids += [it["id"]] + [s["id"] for s in it["stances"]]
                    ids += [a["id"] for s in it["stances"] for a in s["args"]]
                    ids += [c for s in it["stances"] for a in s["args"] for c in a["cases"]]
                elif isinstance(it, dict):
                    ids.append(it["id"])
                else:
                    ids.append(it)
            for x in ids:
                if x not in match_by_id:
                    problems.append(f"{nid} 的 {k} 步引用了不存在的节点：{x}")

    # 3) 每个判断点必须能给出 ①（否则它不配当入口）
    for nid, n in sorted(match_by_id.items()):
        if n["type"] != "判断点":
            continue
        p = build_path(match_by_id, raw_by_id, nid)
        if not p["steps"]["①"]:
            problems.append(f"入口 {nid} 的 ① 是空的——它不该作为入口")
        if not p["steps"]["②"] and not p["steps"]["④"]:
            problems.append(f"入口 {nid} 的 ② 和 ④ 都是空的——这条路径走不出去")

    # 3b) 「怎么确认」的每一步必须是**一整行**。
    #     为什么要有这条：`_howto_steps` 只收 `^\d+\.` 开头的行，
    #     所以一个跨两行写的步骤，**后半句会被静默丢掉**——
    #     路径上看起来完整，其实断在半句话上。
    #     这个 bug 真发生过（judge-0005 与 judge-0006 各一处）。
    _TAIL_BAD = ("，", ",", "：", ":", "（", "(", "、", "；", ";", "——")
    for nid, n in sorted(match_by_id.items()):
        if n["type"] != "判断点":
            continue
        for s in _howto_steps(raw_by_id[nid]):
            if s.endswith(_TAIL_BAD):
                problems.append(f"{nid} 的「怎么确认」有一步骤像是被换行截断了"
                                f"（结尾是「{s[-1]}」）：…{s[-20:]}")

    # 3c) ⭐ 承诺要有守卫：判断点必须读得出 ≥1 步「怎么确认」。
    #     为什么要有这条：`MATCH_SPEC["路径模板"]` 白纸黑字承诺 ① 里有**三件**
    #     （变量 / 怎么测 / 判据），而旧版 check 只断言 ① 非空——
    #     而 ① 非空靠的是 `变量：` 行，**那一行不在「怎么确认」小节里**。
    #     实测：把 judge-0005 的整个 `## 怎么确认` 小节删掉（只改内存），
    #     `--check` 依然退出码 0、依然打印"全部命中"。
    #     → 上一批刚补的 8 节 28 步**没有任何东西守着**。见 AUDIT.md §二.1。
    for nid, n in sorted(match_by_id.items()):
        if n["type"] != "判断点":
            continue
        if not _howto_steps(raw_by_id[nid]):
            problems.append(
                f"{nid} 是判断点，但正文里读不出任何「怎么确认」步骤——"
                f"① 承诺的三件（变量/怎么测/判据）里第二件是空的。")

    # 3d) ⭐ 适用范围必须真的**输出**给使用者。
    #     为什么要有这条：路径对象里有 `scope`，但旧版 `render_text()` 一个字都不打印，
    #     于是系统会给出**明确不适用于用户**的答案而用户看不见。
    #     实测：「我的奖励来自奖励模型，reward 崩了」→ judge-0009（1.40），
    #     而该节点 scope 第一句就是「不适用于奖励来自奖励模型或人工标注的场景」。
    #     见 AUDIT.md §二.3。
    for nid, n in sorted(match_by_id.items()):
        p = build_path(match_by_id, raw_by_id, nid)
        scope = re.sub(r"\*\*|`", "", str(p.get("scope") or "")).strip()
        if not scope:
            continue
        # ⚠️ 比对前**两边都去掉所有空白**：`render_text` 会把 scope 折行，
        # 换了行之后子串就对不上了——而那是**探针的毛病，不是缺陷**。
        # （实测踩过：探针第一版用原样子串比，明明印出来也报 FAIL。）
        flat_scope = re.sub(r"\s+", "", scope)
        flat_rendered = re.sub(r"\s+", "", render_text(p))
        probe = flat_scope[:24]
        if probe and probe not in flat_rendered:
            problems.append(f"{nid} 有适用范围，但文本输出里没印出来（开头是「{probe}…」）")

    # 4) 匹配质量：固定用例必须命中，负例必须不命中；
    #    带断言的条目还要核"路径里该出现的内容有没有出现"
    fails = []
    n_assert = 0
    for case in SELF_TEST:
        query, expect, note = case[0], case[1], case[2]
        asserts = case[3] if len(case) > 3 else {}
        chosen, rows = pick(query, match_by_id)
        if chosen is None:
            got, path = None, None
        else:
            got = chosen[0]
            path = build_path(match_by_id, raw_by_id, got)
        if got != expect:
            top = f"{rows[0][0]} {rows[0][1]:.2f}" if rows else "无"
            fails.append(f"「{query}」（{note}）期望 {expect or '没匹配上'}，"
                         f"实得 {got or '没匹配上'}（最高分 {top}）")
            continue
        for key, wants in asserts.items():
            n_assert += 1
            text = _step_text(path, key)
            if not text.strip():
                fails.append(f"「{query}」（{note}）的 {key} 步是空的——"
                             f"用例走到了这一步，路径却没内容")
                continue
            for w in wants:
                if w not in text:
                    fails.append(f"「{query}」（{note}）的 {key} 步里没出现「{w}」")
    if fails:
        problems += ["匹配自检失败：" + f for f in fails]

    if problems:
        for p in problems:
            print(f"[FAIL] {p}", file=sys.stderr)
        return 1

    n_cue = sum(len(n.get("cues") or []) for n in match_by_id.values())
    n_judge = sum(1 for n in match_by_id.values() if n["type"] == "判断点")
    n_neg = sum(1 for c in SELF_TEST if c[1] is None)
    n_scope = sum(1 for n in match_by_id.values()
                  if str(n.get("scope") or "").strip())
    print(f"检索自检通过：{len(match_by_id)} 个节点 / {n_cue} 条处境；"
          f"{len(SELF_TEST)} 条固定用例全部命中（含 {n_neg} 条负例、{n_assert} 组内容断言）；"
          f"所有路径引用可解析；匹配器拿不到来源与证据状态；"
          f"{n_judge} 个判断点的「怎么确认」都读得出步骤；"
          f"{n_scope} 个节点的适用范围都印得出（含「不适用于…」那半句）。")
    return 0


# ── CLI ──────────────────────────────────────────────────────────────

def _arg(name: str) -> str | None:
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def main() -> int:
    if "--check" in sys.argv:
        return check()

    raw_by_id, match_by_id = load_all()
    if not match_by_id:
        print("nodes/ 里没有可解析的节点。", file=sys.stderr)
        return 1
    global _TITLES
    _TITLES = {nid: str(n["title"]) for nid, n in match_by_id.items()}

    if "--list" in sys.argv:
        return cmd_list(match_by_id)

    entry = _arg("--entry")
    problem = _arg("--problem")

    if entry:
        if entry not in match_by_id:
            print(f"没有这个节点：{entry}", file=sys.stderr)
            return 1
        print(render_text(build_path(match_by_id, raw_by_id, entry)))
        return 0

    if not problem:
        print(__doc__.strip().split("## 为什么要有它")[0].strip())
        return 0

    entry_row, rows = pick(problem, match_by_id)
    if entry_row is None:
        top = rows[0] if rows else None
        print(f"没匹配上。阈值 {TAU}，最高分 {top[1]:.2f}" if top else "没匹配上：没有任何节点重合。")
        if top and top[1] >= TAU:
            # 分数够、但过不了「判断点必须靠处境句进」那道门槛。
            # 这种要说出来——否则用户会以为"分数够了却说没匹配上"是 bug。
            print(f"（{top[0]} 分数够，但它是判断点，而它命中的只是一些词、"
                  f"没有一条处境句和你这句话对得上——按规矩不认，不猜。）")
        print("（本结构不猜。下面是文本上最接近的几条，你自己看哪条对——")
        print("  它们只是字面更像，不代表更可信。）")
        print()
        for nid, sc, why in rows[:5]:
            print(f"  {sc:5.2f}  {nid}  {match_by_id[nid]['title']}")
            print("         最像的 cue："
                  + (f"「{why['cue']}」" if why["cue"] else "（没有一条 cue 有重合）"))
        print("\n按处境自己找：python tools/find_path.py --list")
        return 2

    nid, sc, why = entry_row
    if entry_row is not rows[0]:
        alt_id, alt_sc = rows[0][0], rows[0][1]
        print(f"最高分是 {alt_sc:.2f} → {alt_id} · {match_by_id[alt_id]['title']}"
              f"（{match_by_id[alt_id]['type']}）")
        print(f"但你要的是一个处境，而 {match_by_id[alt_id]['type']} 不是一个处境——"
              f"改判给判断点里最近的一条。")
        print()
    print(f"匹配：{sc:.2f}  →  {nid} · {match_by_id[nid]['title']}"
          f"（{match_by_id[nid]['type']}）")
    print("（匹配分只衡量文本相近程度，与来源、机构、证据状态无关。）")
    print()
    print(render_text(build_path(match_by_id, raw_by_id, nid), why,
                      alts=rows[1:4]))
    if match_by_id[nid]["type"] != "判断点":
        print()
        print(f"注意：{nid} 是「{match_by_id[nid]['type']}」，不是一个处境。")
        print("如果你是在排故障，下面是图上最近的处境：")
        for j, s2, _ in rows:
            if match_by_id[j]["type"] == "判断点":
                print(f"  {s2:5.2f}  {j}  {match_by_id[j]['title']}")
    return 0


# 入口优先判断点。这不是权宜之计，是 ADAPT.md §一 已经记在案的决议：
# 「诊断类内容用组合承载，并在索引页里把 `判断点` 作为主入口。」
#
# ⚠️ 2026-09-23 修正：**旧规则用的是拍数，而且这个拍数从没写进规格。**
#
# 旧规则：`判断点分数 ≥ 阈值 × 0.8`（即 0.24）就改判。后果：
#   概念节点 con-0005 自身得分 **1.90** 的查询，被一个 **0.27** 分的判断点顶掉。
#   实测把库里 81 条处境原句逐条回灌，**13 条没回到自己的节点**。
#   而 `probe_gaps.py` 开头还写着「判定都不用拍数」——同一条纪律一处守一处不守。
#   见 AUDIT.md §二.2。
#
# 新规则：**只在两个候选分数是同一个量级时才改判。**
#   ① 最高分那个**不是**判断点；
#   ② 存在判断点：过阈值、`cue_dice > 0`、且 `分数 ≥ 最高分 × _ENTRY_PREFER_RATIO`。
#
# 为什么门槛要**相对最高分**，不相对阈值——两组实测：
#   · 入口之争的形态：「β 设多少合适，能不能干脆不开 KL」
#     概念 con-0003 **0.45** vs 判断点 judge-0005 **0.38**，比值 **0.84**
#     → 两者分数接近，确实是"该进哪个门"的问题，改判正确。
#   · 用户明确指向的形态：「我在看 loss 是怎么算的…」
#     概念 con-0005 **1.90** vs 判断点 judge-0008 **0.27**，比值 **0.14**
#     → 差一个量级，这时候改判就是**抢**入口。
#
# ⚠️ 0.5 是拍的。但它**写在 MATCH_SPEC 里、带着上面两组实测**——
#    拍数不可怕，"拍完了不写下来"才可怕：下一个模型会从零再拍一遍。
_ENTRY_PREFER_RATIO = 0.5


def _pick_entry(rows: list, match_by_id: dict) -> tuple:
    if not rows:
        return None
    top = rows[0]
    if match_by_id[top[0]]["type"] == "判断点":
        return top
    floor = top[1] * _ENTRY_PREFER_RATIO
    for nid, sc, why in rows:
        if (match_by_id[nid]["type"] == "判断点"
                and sc >= TAU and sc >= floor and why.get("cue_dice", 0.0) > 0.0):
            return (nid, sc, why)
    return top


def accepts(nid: str, why: dict, match_by_id: dict) -> bool:
    """这个入口**该不该被接受**（而不是"分数够不够"）。

    ⚠️ 2026-09-23 新增。**判断点必须靠"一句话"进来——`cue` 或 `标题` 命中都算。**

    为什么是「cue 或标题」而不是「只有 cue」：**标题本身就常常是一句处境**
    （`judge-0007` 的标题是「熵掉得太快，还剩多少可烧」）。
    实测踩过：只认 cue 的话，「熵掉得太快，还剩多少可以烧」这条**合法**查询
    会被判成没匹配上（它分数 0.64、靠标题命中）——那是**把用户的一句话当成了不是**。

    **不卡非判断点**：面试者入口本来就允许靠**名字**进概念节点
    （「组内归一化是怎么算的」→ `con-0001`，`cue_dice` 是 0.00，那是**合法**的）。
    一刀切会把面试者入口打死——实测过。

    实测（阈值 0.18）：留出集命中**不损失**（仍 15/17），
    而「靠一个词硬落下来」的可疑命中从 4 条降到 1 条
    （其中「我要不要上 RL」曾落到 `judge-0013` 长度惩罚，靠的只是个 `rl`）。
    """
    if match_by_id[nid]["type"] != "判断点":
        return True
    return max(why.get("cue_dice", 0.0), why.get("title_dice", 0.0)) >= TAU


def pick(query: str, match_by_id: dict):
    """CLI / 自检 / 采集工具**共用**的入口判定。返回 (选中行 or None, 全部排名)。

    **三处必须走同一个函数**——否则三个地方会给出三种"算不算匹配上"，
    而用户看到的和自检断言的就不是一回事了。
    """
    rows = rank(query, match_by_id)
    if not rows or rows[0][1] < TAU:
        return None, rows
    chosen = _pick_entry(rows, match_by_id)
    if chosen is None or not accepts(chosen[0], chosen[2], match_by_id):
        return None, rows
    return chosen, rows


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
