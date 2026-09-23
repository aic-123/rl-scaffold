# 这两份文件是 vendor 来的，不要在这里改

<!-- Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0 -->

| 项 | 值 |
|---|---|
| 来源仓库 | [Scaffold](https://github.com/aic-123/Scaffold) |
| 来源版本 | tag `v0.0.3` |
| 来源 commit | `f140642f688c1c7e935a6d3a1429cb3d891ab7a2` |
| 拷贝日期 | 2026-09-23 |
| 拷贝方式 | 逐字节 `cp`，拷贝后已 `diff -q` 核对无差异 |

## 拷了什么

```
validator/validate.py      ← ks-demo/validator/validate.py
schema/node.schema.yaml    ← ks-demo/schema/node.schema.yaml
```

## 纪律（三条）

1. **不在这里改**。本目录下的文件是上游的副本，改了就与上游分叉，
   而分叉意味着"同一个校验器在不同仓库行为不同"——那正是本类项目最怕的静默不一致。
2. **要改就去上游改**。Scaffold 有 `CONTRIBUTING.md`：
   新增规则需要**设计方明确认账**，并先开 issue 讨论。
3. **升级时整份替换**，不要手工 merge。替换后跑 `--self-test` 与 `./nodes` 两条命令，
   确认基线未变（校验器自带 `--self-test`，会检查代码常量与 `schema/` 是否互为镜像）。

## 校验器自身的一致性怎么守

`validator/validate.py --self-test` 会检查代码里的常量与 `schema/node.schema.yaml` 是否一致。
所以 `validator/` 与 `schema/` **必须成对升级**——只换一个会立刻被 `--self-test` 拦下。

## 本产品用到它做什么

只用来校验 `nodes/` 的**结构自洽性**（id 唯一、关系不断链、必填字段齐、取值合法……）。
**它不判断内容对错，也不排序**——这一点是 Scaffold 的设计立场，也是本产品选它的原因。
