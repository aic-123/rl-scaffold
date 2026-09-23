# rl-scaffold

<!-- Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0 -->

[中文](README.md) · **English**

**A knowledge structure for RL (reinforcement learning / LLM post-training) engineering.**
Not a tutorial. Not a paper digest. Not a hyperparameter cheat sheet.

---

## ⚠️ First, honestly: what this content is worth

**This is "curated with citations", not "verified knowledge".**

| Item | The actual situation |
|---|---|
| Who filled it | `filled_by: 模型(DeepSeek-V4.1-Flash)` — all 36 nodes were filled by a model, and that is **not hidden**. ⚠️ **"Case" means two different things here — don't conflate them**: ① **first-hand case** (the user's own experience, which is what layer ⑤ of Scaffold actually means: situational features / options considered / reasoning / outcome / counterfactual) — **there are none**, and a model may not write a single word of one; ② **paper-experiment case** (an experimental record read out of a paper, i.e. `case-0001`–`case-0005`) — **there are 5, all model-filled**. A `case-0006` was once created and later deleted: it turned out to be **a question someone posed to test the system**, not a case |
| Verification status | `evidence_status` is `未验证` (unverified) everywhere; issues with a genuine split are marked `有争议` (contested). **Not one node is marked `已验证` (verified)** |
| Sources | Every node carries a `source.ref` (arXiv ID / DOI / section). Full list in [`SOURCES.md`](SOURCES.md) |
| What I checked | Only two things: that the source **exists**, and that **I actually read the range I claim to have read**. I did **not** try to reproduce any paper's results |
| Main limitation | **All primary sources have now been read down to the full text** (on 2026-09-23, DeepSeekMath / Dr. GRPO / DeepSeek-R1 were upgraded from abstract to HTML body). The only one not fully read is **DAPO** — its body was read only for four technique subsections and the ablation numbers. Per-source scope is recorded in [`SOURCES.md`](SOURCES.md) |
| ⚠️ A hole I found myself | While re-reading, I discovered a node whose `source.ref` claimed "§4.1" while the source list said "abstract page" — i.e. **the citation claimed more than what had actually been read**. This project claims to guard that rule; **at the time it did not**. Logged as debt, see [`SOURCES.md`](SOURCES.md) §七 |

Under Scaffold's rules, `已验证` **can only be granted from outside**. So that row above is not modesty, it's a hard constraint:
**anything a model filled can never be marked verified.** That is the premise this whole structure rests on.

---

## What it is

A **plain-text, line-by-line diffable** knowledge structure covering the places where RL engineering goes wrong.

> ✅ **It is a version-controlled repository** (since 2026-09-23).
> All text is stored as **LF** (pinned by `.gitattributes`, not left to editors),
> so diffs don't get noisy from line endings.

- **The entrance is a situation, not a concept.** An RL engineer's real first sentence is not "I want to learn GRPO" but "**my reward stopped going up**". So the primary index is a situational index (`cues`), not a glossary.
- **Disagreements are listed, never adjudicated.** Where there is a real split (e.g. "what explains length growth"), the structure builds **issue + stance** nodes, attaches both sides, and **does not decide for the reader**.
- **Source, institution and confidence never enter ranking.** The only sort key is the file path. This is a hard rule inherited from Scaffold — otherwise you are rebuilding an authority monopoly.

## What it is not

- **Not a tutorial.** No basic concepts explained; it assumes you know what a policy gradient is
- **Not a paper digest.** It does not summarise papers; it extracts "under what conditions does this hold"
- **Not a hyperparameter table.** It will not tell you what to set β to — that depends on your task
- **Not a retrieval service.** No search engine, no index database, no server. Both views are **static artifacts** you can `git diff`. `tools/find_path.py` is a **deterministic matcher**: offline, model-free, reproducible. Give it one sentence describing your problem and it returns **one workable path** — not a list of hits, not a ranked scoreboard
- **Not an app.** `view.html` is a single-file static render: no server, no dependencies, opens offline. It is not "a website"
- **Does not collect private config.** No internal parameters, unpublished results, or paywalled content
- **Does not publish a "best practices leaderboard".** No ranking, weighting or scoring of any kind. **The match score is no exception**: it measures textual similarity only, **never credibility** — source, institution and evidence status are dropped at parse time, and the scoring function cannot see them in memory

---

## 5-minute quickstart

```bash
# 0. Install the only dependency (PyYAML)
python -m pip install -r requirements.txt

# 1. Check structural self-consistency (does not judge content correctness)
python validator/validate.py ./nodes          # expect: ERROR 0, exit code 0

# 2. List what is still owed
python validator/validate.py ./nodes --todo

# 3. Rebuild the two views (run after editing nodes)
python tools/build_index.py                   # -> index/by-situation.md (text view)
python tools/render_view.py                   # -> index/view.html (rendered view)

# 4. Check the two views are in the same order (they must be two forms of one spec)
python tools/render_view.py --check           # expect: exit code 0

# 5. Retrieve by need: turn the problem you have into a workable path
python tools/find_path.py --problem "日志里 entropy 一路往下掉，我不知道要不要停"
#    If it's a long spoken paragraph (hundreds of characters), split it first and match sentence by sentence
python tools/find_path.py --split "我基于 verl 跑 qwen3.5 的 GRPO，跑了 200 步 reward 崩了…"
#    (cues are one situation each, ~20 characters; matching a whole paragraph directly gets diluted by length)
python tools/find_path.py --list              # browse by situation instead
python tools/find_path.py --check             # self-check (fixed cases + negatives + content assertions)

# 6. Gap probe (the opposite direction: not "did I get it right" but "what am I missing")
python tools/probe_gaps.py                    # run all 39 constructed corpus sentences
python tools/probe_gaps.py --miss             # only the ones that fell through
python tools/probe_gaps.py --held             # paraphrase robustness on a held-out set
```

Dependencies: Python 3.9+ and `PyYAML` (the same one dependency as the vendored validator), listed in `requirements.txt`.
**⚠️ Without it, the very first command fails with `ModuleNotFoundError: No module named 'yaml'`** — that's not a doc oversight, it's the price of the project's "zero lock-in" stance, which is why step 0 is spelled out.

**First-value path**: throw **your own** problem, in your own words, at `tools/find_path.py --problem`. It matches one situation, then walks a six-step path along `relations`.
Prefer browsing? Open [`index/view.html`](index/view.html) — every situation has a "view path" link that opens the six-step path already computed for it.
Currently **112 situations / 36 nodes / 14 workable paths**.

---

## The view layer

Layer ⑥ of Scaffold is the **view layer**, defined as "**query/sort specification (visible, changeable, versionable)**". This project implements all three:

| Requirement | Where it lives |
|---|---|
| **Visible** | `index/view.html` renders the sort spec right at the top; whoever reads the page can see it |
| **Changeable** | The spec is the `SORT_SPEC` constant in `tools/render_view.py`; change it and you change the view |
| **Versionable** | It lives in git and diffs like any node (`.gitattributes` pins line endings to LF) |

**The core rule**: **the only sort key is "file path, then cue text".**
Source, institution, evidence status and filler **never enter the sort**, and are not weighted or scored.
→ Because: **sorting is recommending.** Writing authority into the sort is deciding for the reader whom to trust.

**Two views, one spec**: `by-situation.md` (text) and `view.html` (rendered) must produce a **line-for-line identical** order.
That invariant is enforced by `python tools/render_view.py --check` —
**it cannot live in a comment**, because two generators each writing their own sort will **silently** disagree.

`--check` also verifies three more things (all with negative cases actually executed):

- **"View path" links correspond strictly to 判断点 (decision points)** — present when it should be, absent when it shouldn't
- Both the **`href` and the `data-open` attribute** must point at the same real path block
  (checking one is not enough: the JS uses `data-open`, and breaking it makes the user open **someone else's** path)
- **Tag balance** — a previous generator emitted one extra `</div>`, the page looked completely normal,
  because **browsers silently recover**. Counting tags found it. → **Browser tolerance is not correctness.**

**The filter box in `view.html` only hides; it never reorders**: the order is identical before and after filtering.
It is **not a search feature**, just display convenience.

---

## Retrieval by need: from "the problem I have" to a workable path

The flaw of a flat index: **you have to know what you're looking for before you can find it.**
`tools/find_path.py` covers the other half — from the words in your mouth to an entrance, then along `relations` to a chain.

```bash
python tools/find_path.py --problem "我的模型回答越来越长，token 消耗翻了好几倍"
```

Six steps, each with a reason to exist:

| Step | Answers | Where it comes from |
|---|---|---|
| ① What to look at first | Which quantities to pull up | The 判断点's `变量：` line + numeric decision criteria in the body |
| ② Why (mechanism) | What is actually at work underneath | `概念`. Direct edges first; if none, route via issue/exception **and label it as indirect** |
| ③ When this does not hold | When not to trust the above | `例外` (both out-edges and in-edges) |
| ④ Is there a debate here | Are there two camps | `议题` → `立场` → `论据` → `案例` (≤2 hops in the graph) |
| ⑤ What others did | Who actually ran it, and what happened | `案例`, **in three attachment tiers**: direct / via argument / via concept (weak) |
| ⑥ What you may hit next | The next thing you'll run into | Other 判断点 sharing a concept, labelled with what they route through |

### Retrieval spec (change it in `MATCH_SPEC` inside `tools/find_path.py`)

- **Match keys**: situation sentences (`cues`) + title + aliases.
  ⚠️ **The Chinese body of `scope` does not participate in scoring** — it only contributes its **Latin identifiers** (e.g. `grad_norm`).
  An earlier version said "+ scope", which reads as if the whole scope matched; **that was hollow**.
  (Why not let it participate: `scope` contains "**does not apply to…**" statements, and matching on them would
  **raise a node precisely when the query falls inside its exclusion range** — the direction is backwards. Instead, that exclusion clause is now **printed in the output**.)
- **Algorithm**: Chinese matched by character bigram overlap; English/numeric identifiers matched by exact token set membership, **weighted by rarity** —
  hitting a rare `grad_norm` is strong evidence; hitting a common `kl` is not
- **Long spoken input gets diluted by length, so an "overlap coefficient" was added**: Chinese uses **character bigrams**,
  and Dice's denominator is the sum of both lengths — **the longer the sentence, the lower the score**. Measured: a real 150-character user utterance
  against the closest cue scored **Dice 0.081** but **overlap coefficient 0.400** (5× difference).
  So `0.6 × overlap` was added into `base` (taken as a **max** with Dice, **not summed**) —
  long utterances went 0.15 → 0.24, and **the out-of-scope negative margin actually widened from 0.04 to 0.09**.
- **Split a whole paragraph before matching** (`--split`): `cues` are **one situation each**, while a real user's words are often **a whole paragraph**.
  **Forcing the matcher to swallow a paragraph is wrong — the granularity doesn't line up.** Splitting uses only punctuation and whitespace, no model.
- **Identifiers multiply, they don't add**: they **amplify existing text overlap**, they never score on their own.
  Addition would let one common word lift a node with **zero text overlap** over the threshold — i.e. let one word decide which node the reader sees
- **Entrance prefers 判断点**: if the top scorer is not a 判断点 but one is within reach, switch to the 判断点
  and **print the fact that it switched**. Based on the recorded decision in [`ADAPT.md`](ADAPT.md) §一
- **Threshold is 0.18** (set on 2026-09-23 by a measured sweep: 0.30→9/17, 0.22→13/17, **0.18→15/17**,
  0.16→15/17, 0.14→15/17 but **negatives cross the line**; 0.18 is "the largest threshold that reaches the highest hit rate", so it has the widest safety margin).
  Below it, it **says "no match" honestly** and lists the closest few for you to pick from.
  **It does not guess, does not hedge, does not force an answer at you**
- **A 判断点 must be entered via "a sentence"** (`cue` or `title` hit), **never via "a word"** (alias/identifier).
  **This only applies to 判断点** — the interviewer entrance is legitimately allowed to reach a concept node by name; applying it globally would kill that entrance

### Two red lines enforced by code structure

**One: source and evidence status are dropped at parse time.**
`_match_record()` admits only `id / type / title / aliases / cues / scope / relations`.
`source`, `evidence_status`, `filled_by` **do not exist in memory at all**.
→ So "source doesn't enter matching" is not a promise, it's that the scoring function **cannot see them**. `--check` verifies this empirically.

**Two: fuzzy matching has exactly one implementation.**
`view.html` **does not reimplement scoring** — two implementations inevitably drift, and what drifts is the order.
The browser only does: literal filtering + opening an **already computed** path.

### What the self-check (`--check`) pins down

1. Match records contain no source/evidence-status fields (and it empirically verifies `_match_record` really drops them)
2. Every node referenced by a path exists (no dangling ids)
3. Every 判断点 can produce ①, and ②/④ are not both empty (otherwise it doesn't deserve to be an entrance)
4. **All 25 fixed cases hit, including 4 negatives + 3 content assertions**
   ("今天天气怎么样" must report no match)
5. **Every 判断点's "how to confirm" section is readable**, and no step is half a sentence cut by a line wrap
6. ⭐ **Every 判断点 yields ≥1 "how to confirm" step** (added 2026-09-23)
   — the old version only asserted ① was non-empty, and ① non-emptiness rested on the `变量：` line;
   measured: deleting the entire `## 怎么确认` section of `judge-0005` still left `--check` **at exit code 0**
7. ⭐ **Any node with a `scope` must print its applicability into the text output** (added 2026-09-23)
   — the old render printed not one character of it, so the system could hand you an answer that **explicitly does not apply** while you couldn't see why

`tools/render_view.py --check` has an 8th: **every path block must print that node's applicability scope**.

> **A rule guarded only by a comment is not a rule, it's a wish.**
> That's why match quality is pinned by a table of fixed cases, not by "I think it's fine".
> Negative cases were run: lowering the threshold really does turn the self-check red.
> **Items 6 and 7 are the second time that same sentence came true**: each was **verified with a negative case** —
> delete that section, remove that output, and the check goes red and **names the specific node**.
> A test with no input known to break it is not a test, it's decoration.

**One table, two kinds of row** (this came out of an external challenge):

| Row type | What it pins | What it proves |
|---|---|---|
| **Entrance-only** (most) | Which node this sentence should reach | Existing entrances **are still findable** (regression) |
| **With content assertions** (few) | Whether **the content that should appear** actually appears in the path | **Coverage** |

**Whether the entrances are complete can only be discovered by the second kind.** Sentences you write yourself from the nodes only prove self-consistency.

⚠️ **But do not open a new layer for external cases.** "What would you do if this happened" **is a way of phrasing a symptom**,
and goes through normal retrieval — giving it its own table and its own command would be dressing an existing entrance up as a new category.
Its "external" identity just goes in the notes column.

`--problem` outputs text only. The HTML form of a path lives in `index/view.html`,
and both forms share **one** template: `find_path.build_path()`.

### ⚠️ The main entrance was added later, not there from the start

The first line of `PLAN.md` §一 reads "an RL engineer's real entrance is not 'I want to learn GRPO' but '**my reward stopped going up**'."
**And in the first version's 75 situations, not a single one was that.**

It was forced out by an **external scenario**: someone posed a test case ("if this happened, what would your system do"), and retrieval returned this — **measured before the entrance was added**:

```
reward 曲线跑着跑着崩了
  0.48 con-0006   cue=0.000   title=0.000   alias=0.385   ids=['reward']
```

`cue` overlap **0.000**, `title` overlap **0.000** — that sentence had **zero literal overlap with any situation description or any title**
in the structure. It landed only because the sentence contained a word called `reward`.

**Why the self-check missed it**: the `SELF_TEST` entries are written from **existing nodes**,
so they can only prove "existing entrances are findable" — **never that "the entrances are complete"**.

> **Testing your own system with your own sentences tests self-consistency, not coverage. Coverage has to be forced by external scenarios.**

The fix is in [`ADAPT.md`](ADAPT.md) §十二: a new `judge-0009` (**triage** 判断点) that splits
"reward crashed" into four separately-checkable directions, each with **how to confirm** it.

### ⚠️ And that same question exposed a second gap: ① gave "what to look at" but not "how to look"

The second half of that question was "auditing found 50% of rollouts reasoned correctly but were scored 0".
At the time the system could name **"false negative rate"** but **could not say how to get that number** —
**even though `judge-0009`'s own body spells out the four measurement steps.**

The cause: the path template's ① took only the `变量：` line plus numeric criteria lines, and **did not include the body's "how to confirm" section**.

→ ① became three parts: **variable (what to look at) → how to measure (how to look) → criterion (what counts)**.
One sentence of justification: **a variable you cannot measure has not been given.**

**⚠️ But fixing the template only solved half.** A count showed: **of 9 判断点, only `judge-0009` had that section.**
So the other 8 still had a ① that named quantities without telling you how to measure them.

→ **"How to confirm" was then written for the remaining 8 判断点** (3–4 steps each, 28 steps total).
Three rules: **every step must trace back to a source**; where the source gives no method (e.g. judge-0001 step 3, judge-0002 step 1)
**the source strength must be labelled** and not blended into "what the paper says";
and **not every 判断点 is a troubleshooting question** (`judge-0005` is a selection question, whose "how to confirm" is
"first confirm which implementation you actually have") — **do not force one shape onto all of them**.

### ⚠️ Third thing: that question was **not a case**

Whoever posed it was **testing** what the system would do with such a situation — **it is a question, not a record of fact.**

It was once created as `case-0006` (a case slot, body left empty for the user to fill). **It has been deleted**, because:

> **A case cannot be generated from an example.** Leaving an empty case slot is leaving a fake piece of evidence that "there appear to be cases here".

**And it doesn't need a new home.** "What if this happened" **is simply a way of phrasing a symptom** —
it goes through the ordinary retrieval command and never fell out in the first place. It now lives in `SELF_TEST` as **a case with a content assertion**.

> ⚠️ I did briefly give it its own table (`SCENARIO_TEST`) and its own command (`--scenario`).
> **That was dressing an existing entrance up as a new category** — since merged back into `SELF_TEST`.
> See [`ADAPT.md`](ADAPT.md) §十三.

### The triage node: `judge-0009`

| What you see | What it probably is | Where to look |
|---|---|---|
| Reward is 0 but the reasoning looks right | The scoring rule didn't match (most often: the answer was truncated) | `judge-0004` |
| Every prompt in a batch scores 1 (or all 0) | No within-group variance → advantage 0 → wasted run | `judge-0002` |
| Scoring depends on format, format depends on length | The reward function has fused "is the format right" with "is the answer right" | `con-0006` |
| All of the above ruled out | Not on the reward side — look at entropy and train/inference mismatch | `judge-0001`, `judge-0006` |

**How it differs from `judge-0004`**: `judge-0004` asks "how should truncated samples be rewarded" —
a question you can only ask once you **already know** truncation is the problem.
The real first sentence is "reward crashed", and at that point you don't know the cause.

**This is the only node in the structure with `source.kind: 其他`** — it introduces no new facts,
only **routing**; every triage branch comes from the nodes it points at. See [`ADAPT.md`](ADAPT.md) §十二.

---

## Layout

```
nodes/                 36 nodes (one Markdown file + YAML front matter per node)
index/by-situation.md  situational index (text view; generated, do not hand-edit)
index/view.html        situational view + 14 workable paths (rendered; generated, do not hand-edit)
tools/build_index.py   text view generator
tools/render_view.py   rendered view generator + view consistency check (--check)
tools/find_path.py     retrieval by need + path template + self-check (--check)
validator/validate.py  validator (vendored from Scaffold v0.0.3, unmodified)
schema/node.schema.yaml field definitions (same provenance)
SOURCES.md             source list and inclusion thresholds
ADAPT.md               structure adaptation decisions
PLAN.md                step plan
AUDIT.md               architecture audit + remediation record
DECISIONS.md           settled decisions + working rules (read this first)
```

---

## Where the structure comes from

The six-layer structure, dual index and `R1–R10` validation rules all come from **[Scaffold](https://github.com/aic-123/Scaffold)**
(v0.0.3, commit `f140642`). This project **uses it and does not modify it**.

`validator/` and `schema/` are **byte-for-byte copies**; provenance and discipline in [`validator/VENDORED.md`](validator/VENDORED.md).

**Why vendor rather than reference a path**: this project must be runnable right after `git clone`, without depending on another repo's location on disk.

---

## Known non-goals (not oversights)

| Not done | Why |
|---|---|
| Retrieval service / index database | No search engine, no database, no server. Retrieval is an **offline deterministic matcher** (`tools/find_path.py`): model-free, reproducible, self-checkable. The filter box in `view.html` **only hides, never reorders**, and does not constitute retrieval |
| Using a model for matching | **Explicitly not done.** A model nominating entrances is a non-reproducible, non-auditable self-declaration — the same class of problem as `evidence_status` not being allowed to self-declare "verified"; and a model scoring candidates puts something opaque into the ranking. Matching uses deterministic algorithms only, and **when it can't match, it says so** |
| An application-grade web UI | `index/view.html` is a **single-file static render**: no server, no dependencies, opens offline. It is **not** an app — no backend, no state, no accounts |
| Extending node types | Extending types means changing Scaffold's schema. This project **does not modify upstream** |
| Second-hand sources | The threshold is "only accept sources that have a stable identifier and that I have read". The convention for second-hand sources is written in `SOURCES.md` §四 and **has not been triggered yet** |
| Collecting config values / recommended numbers | See [`ADAPT.md`](ADAPT.md) §三. Even a paper's own intervention ratio is recorded only as "that paper's experimental setting", never as a recommendation |

---

## What the next batch should do (for the next person, or the next me)

1. **Verification** — under Scaffold's rules `已验证` can only be granted **externally**. This project cannot do it for itself
2. **Automate the cross-check between `source.ref` and `SOURCES.md`** — the 2026-09-23 upgrade exposed a hole:
   `con-0001`'s `source.ref` claimed "§4.1" while `SOURCES.md` said "abstract page",
   i.e. **the citation claimed more than had been read, and nothing stopped it**.
   See [`SOURCES.md`](SOURCES.md) §七. **Not implemented.**
3. **Extend the fixed-case table to every situation** — `SELF_TEST` is now 25 rows
   (21 positive + 4 negative, one of which carries content assertions).
   The ideal state is one "how someone else would phrase it" per situation across all 112, to pin match quality.
   **This is something anyone can do, and it pays off immediately.**
   ⚠️ But keep the distinction: sentences written from nodes only test self-consistency; **coverage needs sentences that genuinely come from outside** —
   when one arrives, label it in the notes and give it a **content assertion**
4. **Cases: currently 0** — this needs the user to supply a real experimental record (five body sections).
   A model cannot fill it, and **neither can an example**. This is the project's largest blank, and it can only be filled from outside
5. **Coverage criteria** in [`PLAN.md`](PLAN.md) §五: four entrances (troubleshooter / selector / interviewee / out-of-scope).
   The first release only requires the **troubleshooter** entrance to work
