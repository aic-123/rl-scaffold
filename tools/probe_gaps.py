#!/usr/bin/env python3
# Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0
"""缺口探测器：**先写当事人原话，再看哪句落不下去**。

    python tools/probe_gaps.py            # 全量跑，按类别分组
    python tools/probe_gaps.py --miss     # 只看没匹配上的（缺口清单）

## 它和 `find_path.py --check` 的分工

    `--check`  是**验收**工具：已知答案，跑出来必须是"通过"。
    `probe_gaps` 是**采集**工具：**答案未知**，跑出来的东西叫"缺口清单"。

两者方向相反。`--check` 问"我做对了吗"；这个问"我还差什么"。

## 为什么要反过来走

`PLAN.md` §一 的第一条纪律是「**索引规格必须先于内容映射**」——
写不出情境句的内容，根本不该被收录。

**而实际做的时候是反的**：先把论文/教材/官方文档读成节点，
再从节点里"提炼"处境句。后果是**只长出了"论文会写的那部分"**——
论文写的是「我们做了什么」，不是「你该先想什么」。
→ 于是「事前」那一类天生长不出来。

**正确的顺序**：先写当事人原话 → 全丢进匹配器 → **没落下去的那几句就是缺口。**

## 语料怎么写（三条，与 `cues` 的写法纪律一致）

1. **写当事人原话，不写术语。** 写「我该不该给格式分」，不写「reward shaping 设计」。
2. **覆盖多个入口，不只排查者。** `PLAN.md` §五 定了四个入口
   （排查者 / 选型者 / 面试者 / 越界），语料必须都碰。
3. **越界那类必须真的是越界。** 它们是**负例**：落不下去才是对的。

## 输出怎么读

- `MISS` —— 没匹配上。**这是缺口。**
- `NOCUE` —— 落到了判断点上，但**没有任何一条 cue 有重合**（`cue=0.000`）。
  说明它是靠标题、别名或一个通用词落下来的。**这也是缺口**（缺的是一句处境）。
- `NONJUDGE` —— 落到了**非判断点**上（概念 / 例外 / 案例）。
  ⚠️ **这一类不算错**：`PLAN.md` §五 的「面试者」入口要的就是概念节点。
  列出来只是为了让人看一眼——**里面混着"落对了"和"落错了"两种，
  而分清它们需要眼睛，不需要算法。**
- `HIT`  —— 正常命中。

**判定只用两种判据，都不用拍数**：匹配分是否过阈值、cue 重合是否为 0。
（早先还有一档"分数边缘"（< 0.45），实测一份语料下来一次都没触发，
**已删掉**——一个从不触发的阈值就是拍脑袋。）

⚠️ 本工具**只产出清单，不改任何节点**。
清单里哪几条该补，由人决定——**这一步刻意不自动化。**
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import find_path as f  # noqa: E402

# ── 语料 ─────────────────────────────────────────────────────────────
# (类别, 当事人原话)
# ⚠️ 语料只加不减：**每一条都要能被追溯到是谁会这么说**。
#    编不出来的句子不要往里放——那会污染缺口清单。
CORPUS = [
    # A. 排查者（对照组：这几句已知有节点，落不下去说明是回归 bug）
    ("A 排查者", "日志里 entropy 一路往下掉，我不知道要不要停"),
    ("A 排查者", "reward 曲线跑到一半崩了，不知道先查哪里"),
    ("A 排查者", "actor/grad_norm 一直往上爬，调学习率也没用"),
    ("A 排查者", "一批 prompt 奖励全是 1，感觉没贡献梯度"),

    # B. 事前 / 奖励规则设计（本轮怀疑的缺口区）
    ("B 事前·奖励设计", "我打算用规则奖励，担心模型学会只对格式不对答案"),
    ("B 事前·奖励设计", "我的判分规则用正则匹配，会不会有漏判"),
    ("B 事前·奖励设计", "我该不该给格式分"),
    ("B 事前·奖励设计", "奖励里要不要加长度惩罚"),
    ("B 事前·奖励设计", "我想让模型学会一步步想，但不知道奖励怎么给"),
    ("B 事前·奖励设计", "同一个答案有好几种写法，正则只匹配一种，怎么办"),
    ("B 事前·奖励设计", "训练一开始 reward 就冲到 0.99，我怀疑规则太松了"),
    ("B 事前·奖励设计", "要不要给中间步骤打分，还是只看最后答案"),

    # C. 选型
    ("C 选型", "我要不要上 RL，还是继续 SFT 就够了"),
    ("C 选型", "GRPO 和 PPO 我该选哪个"),
    ("C 选型", "我显存不够，能不能只用 GRPO 不要 critic"),
    ("C 选型", "手上有 8 张卡，该跑多大的模型"),
    ("C 选型", "该用现成框架还是自己写训练循环"),
    ("C 选型", "我该选 verl 还是 OpenRLHF"),

    # D. 超参 / 配置
    ("D 超参", "学习率设多少合适"),
    ("D 超参", "每个 prompt 采样几条比较合适"),
    ("D 超参", "batch size 该开多大"),
    ("D 超参", "训练多少步算够"),

    # E. 数据 / 任务构造
    ("E 数据", "我的训练集只有几百条，够不够"),
    ("E 数据", "题目太简单了模型全答对，要不要换难一点的"),
    ("E 数据", "训练数据要不要去重"),
    ("E 数据", "该用什么难度的题"),

    # F. 评测 / 上线
    ("F 评测", "训练集分数涨了但测试集没涨，是不是过拟合了"),
    ("F 评测", "训完的模型和基座比好像变笨了"),
    ("F 评测", "我该用什么评测集"),
    ("F 评测", "训完之后要不要再做一轮 SFT"),
    ("F 评测", "模型训完开始输出重复内容"),

    # G. 面试者（PLAN.md §五 的第三个入口）
    ("G 面试", "GRPO 和 PPO 的区别是什么"),
    ("G 面试", "为什么 GRPO 不需要 critic"),
    ("G 面试", "什么是 reward hacking"),
    ("G 面试", "组内归一化是怎么算的"),

    # H. 越界（负例：落不下去才是对的）
    ("H 越界·负例", "我的显卡坏了怎么办"),
    ("H 越界·负例", "公司不给我批算力"),
    ("H 越界·负例", "今天天气怎么样"),
    ("H 越界·负例", "帮我写一首诗"),
]


# ── 留出集：测**同义改写**能不能落下去（与 CORPUS 用途不同）───────────────
#
# ⚠️ 为什么要有它：`CORPUS` 是**我自己写的**，而且写的时候离 `cues` 很近——
#    所以 CORPUS 上的分数**不能证明覆盖**，它证明的是"我把像的话写进了 cues"。
#    实测证据（2026-09-23）：第一套留出集 9 句里 **5 句**落不下去；
#    补完 cues 之后，第二套（全新的说法）9 句里 **8 句**落不下去。
#
# **这个数字不是"缺口"，是"同义改写的鲁棒性"。两者要分开看。**
# 结论：检索的瓶颈**不在内容量，在匹配算法**——
# 中文走的是**字符二元组重合**，需要**字面共享**；
# 真人换一套词说同一件事，就落不下去。
#
# ⚠️ 所以：**不要用"往 cues 里多抄几句"来压这个数**——那是把测试集喂成训练集。
#    要动就得动匹配算法（那是 D-04 级别的事，见 DECISIONS.md）。
HELD_OUT = [
    # (期望入口, 与 cues 不同的说法)
    ("judge-0010", "我的判分脚本可能认不出另一种写法"),
    ("judge-0010", "答案格式稍微变一下，规则就判错了"),
    ("judge-0010", "规则奖励会不会冤枉了答对的模型"),
    ("judge-0010", "改了答案的写法之后奖励就变成 0 了"),
    ("judge-0010", "担心判分规则太窄，把对的判成错的"),
    ("judge-0011", "给格式分会不会让模型只摆样子"),
    ("judge-0011", "要不要奖励它把思考写在标签里"),
    ("judge-0011", "要不要单独给格式一项加分"),
    ("judge-0011", "奖励里格式和答案各占多少"),
    ("judge-0012", "只看最后答案是不是信号太稀疏了"),
    ("judge-0012", "过程奖励是不是一定比结果奖励好"),
    ("judge-0012", "能不能对每一步都给奖励"),
    ("judge-0012", "奖励信号太稀疏，想铺到中间步骤"),
    ("judge-0013", "模型越写越啰嗦，罚长度有用吗"),
    ("judge-0013", "截断的那些样本要不要单独处理"),
    ("judge-0013", "回答长度失控，加惩罚能压住吗"),
    ("judge-0013", "超出长度上限的部分要不要扣分"),
]


def run_held_out(match_by_id: dict) -> int:
    """跑留出集，报**同义改写命中率**。这是指标，不是验收。"""
    ok = miss = wrong = 0
    print(f"\n■ 留出集（{len(HELD_OUT)} 句，与 CORPUS 用途不同：测**同义改写**）")
    for want, q in HELD_OUT:
        rows = f.rank(q, match_by_id)
        if not rows or rows[0][1] < f.TAU:
            miss += 1
            top = f"{rows[0][0]} {rows[0][1]:.2f}" if rows else "无重合"
            print(f"  ✗ 没匹配上　（最高 {top}）　「{q}」")
            continue
        got, sc, why = f._pick_entry(rows, match_by_id)
        if got == want:
            ok += 1
            print(f"  · [{sc:.2f}] 「{q}」→ {got}")
        else:
            wrong += 1
            print(f"  ✗ 落到了别的节点　[{sc:.2f}] 「{q}」→ {got}（期望 {want}）")
    n = len(HELD_OUT)
    print(f"\n  同义改写命中率 **{ok}/{n}**（落错 {wrong} / 没匹配上 {miss}）")
    print("  ⚠️ 这个数**不是缺口计数**，是**匹配算法对改写的鲁棒性**。")
    print("     别用「往 cues 里多抄几句」来压它——那是把测试集喂成训练集。")
    return 0


def classify(query: str, match_by_id: dict) -> tuple[str, float, str, str]:
    """返回 (判定, 分数, 入口, 依据)。判定 ∈ HIT / NONJUDGE / NOCUE / MISS。

    两条判据都不需要拍数：
      · 分数过不过阈值（`find_path.TAU`，那是检索规格的一部分）
      · 落在判断点上时，`cue_dice` 是不是 0（结构事实：一条 cue 都没重合）
    """
    rows = f.rank(query, match_by_id)
    chosen, rows = f.pick(query, match_by_id)
    if chosen is None:
        top = f"{rows[0][0]} {rows[0][1]:.2f}" if rows else "（无任何重合）"
        gate = ""
        if rows and rows[0][1] >= f.TAU:
            gate = "（分数够，但过不了「判断点必须靠处境句进」那道门槛）"
        return "MISS", (rows[0][1] if rows else 0.0), "—", f"最高分 {top}{gate}"

    nid, sc, why = chosen
    why_s = (f"cue={why['cue_dice']:.3f} title={why['title_dice']:.3f} "
             f"alias={why['alias_dice']:.3f} ids={why['ids']}")
    # ⚠️ 改判必须**可见**。旧版 `_pick_entry` 在这里静默生效，
    # 于是"入口被换掉了"这件事在缺口清单里看不出来——清单会骗人。
    if rows[0][0] != nid:
        why_s += (f"　⟵ **改判**：最高分本是 {rows[0][0]} {rows[0][1]:.2f}"
                  f"（{match_by_id[rows[0][0]]['type']}）")

    if match_by_id[nid]["type"] != "判断点":
        return "NONJUDGE", sc, nid, why_s
    if why["cue_dice"] == 0.0:
        return "NOCUE", sc, nid, why_s + "（一条 cue 都没重合）"
    return "HIT", sc, nid, why_s


def main() -> int:
    raw_by_id, match_by_id = f.load_all()
    if "--held" in sys.argv:
        return run_held_out(match_by_id)
    only_miss = "--miss" in sys.argv

    rows_out = []
    for cat, q in CORPUS:
        verdict, sc, nid, why = classify(q, match_by_id)
        rows_out.append((cat, q, verdict, sc, nid, why))

    # 越界那类是负例：MISS 才是对的。分开统计，否则会污染缺口计数。
    is_neg = lambda c: "越界" in c  # noqa: E731

    groups: dict[str, list] = {}
    for r in rows_out:
        groups.setdefault(r[0], []).append(r)

    for cat in sorted(groups):
        print(f"\n■ {cat}")
        for _c, q, verdict, sc, nid, why in groups[cat]:
            if only_miss and verdict not in ("MISS", "NOCUE"):
                continue
            mark = {"MISS": "✗", "NOCUE": "✗", "NONJUDGE": "?", "HIT": "·"}[verdict]
            print(f"  {mark} [{sc:.2f}] 「{q}」")
            if verdict == "MISS":
                print(f"         {why}")
            elif verdict != "HIT":
                print(f"         落到了 {nid}　{why}")

    pos = [r for r in rows_out if not is_neg(r[0])]
    neg = [r for r in rows_out if is_neg(r[0])]
    miss = [r for r in pos if r[2] == "MISS"]
    nocue = [r for r in pos if r[2] == "NOCUE"]
    nonjudge = [r for r in pos if r[2] == "NONJUDGE"]
    hit = [r for r in pos if r[2] == "HIT"]
    neg_bad = [r for r in neg if r[2] != "MISS"]

    print("\n" + "─" * 74)
    print(f"语料 {len(rows_out)} 句（正例 {len(pos)} + 越界负例 {len(neg)}）")
    print(f"  正常命中 {len(hit)}　"
          f"**缺口 {len(miss) + len(nocue)}**（没匹配上 {len(miss)} + 落在判断点上却无 cue 重合 {len(nocue)}）")
    print(f"  落在非判断点 {len(nonjudge)}（**不算错**，但要人看一眼）")
    print(f"\n  越界负例 {len(neg)} 句，其中 {len(neg) - len(neg_bad)} 句正确落不下去")
    if neg_bad:
        print("  ⚠️ 这些「越界」的话被匹配上了——要么语料写得不越界，要么结构收得太宽：")
        for _c, q, _v, sc, nid, _w in neg_bad:
            print(f"     [{sc:.2f}] 「{q}」→ {nid}")
    print("\n（本工具只产出清单，不改节点。清单里哪几条该补由人决定。）")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
