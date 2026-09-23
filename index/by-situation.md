# 情境索引

<!-- Copyright 2026 AIC-123 · SPDX-License-Identifier: Apache-2.0 -->

<!-- 本文件由 tools/build_index.py 生成，不要手改。改节点，然后重跑。 -->

> **怎么用**：在下面找一句最接近你处境的描述，点进节点。
>
> **排序说明**：只按文件路径排序。**来源、机构、置信度一律不进排序**——
> 这是本结构从 Scaffold 继承的硬规矩（`rules.md` R9 一节）。

---
共 **112** 条处境描述，指向 **36** 个节点。
---
## 按处境
- 「DAPO 凭什么说这四项都有用，而不是碰巧」
  → [`arg-0001`](../nodes/arg-0001-dapo-ablation-chain.md) **增量消融：四项技术各加一项，分数单调上升**　<sub>论据</sub>
- 「我想看一个能区分「哪一项贡献多少」的实验」
  → [`arg-0001`](../nodes/arg-0001-dapo-ablation-chain.md) **增量消融：四项技术各加一项，分数单调上升**　<sub>论据</sub>
- 「Dr. GRPO 凭什么说它比 GRPO 好，好在哪里」
  → [`arg-0002`](../nodes/arg-0002-token-efficiency.md) **把优势公式的偏差与「token 效率」直接挂钩**　<sub>论据</sub>
- 「我想知道有没有把「偏差」和「浪费」连起来的证据」
  → [`arg-0002`](../nodes/arg-0002-token-efficiency.md) **把优势公式的偏差与「token 效率」直接挂钩**　<sub>论据</sub>
- 「我想找一个开源、能复现的大规模 LLM RL 配置」
  → [`case-0001`](../nodes/case-0001-dapo-aime24.md) **DAPO：在 AIME 2024 上把朴素 GRPO 从 30 分做到 50 分**　<sub>案例</sub>
- 「我的 GRPO 规模上不去，想看看别人在类似处境下做了什么」
  → [`case-0001`](../nodes/case-0001-dapo-aime24.md) **DAPO：在 AIME 2024 上把朴素 GRPO 从 30 分做到 50 分**　<sub>案例</sub>
- 「只用少量算力能跑到什么程度」
  → [`case-0002`](../nodes/case-0002-drgrpo-7b-aime.md) **Dr. GRPO：7B 基座做到 AIME 2024 的 43.3%**　<sub>案例</sub>
- 「我想用很小的模型复现 R1-Zero，有可查的例子吗」
  → [`case-0002`](../nodes/case-0002-drgrpo-7b-aime.md) **Dr. GRPO：7B 基座做到 AIME 2024 的 43.3%**　<sub>案例</sub>
- 「有人说去掉优势公式里的标准差项就够了，有实验吗」
  → [`case-0002`](../nodes/case-0002-drgrpo-7b-aime.md) **Dr. GRPO：7B 基座做到 AIME 2024 的 43.3%**　<sub>案例</sub>
- 「我想知道 RL 到底能不能让模型自己学会检查和反思」
  → [`case-0003`](../nodes/case-0003-r1-zero-pure-rl.md) **R1-Zero：不做 SFT、不用人工推理轨迹，纯 RL 跑出自我验证**　<sub>案例</sub>
- 「有人说不做 SFT 也能训出推理能力，有依据吗」
  → [`case-0003`](../nodes/case-0003-r1-zero-pure-rl.md) **R1-Zero：不做 SFT、不用人工推理轨迹，纯 RL 跑出自我验证**　<sub>案例</sub>
- 「纯 RL 训出来的模型有什么副作用」
  → [`case-0003`](../nodes/case-0003-r1-zero-pure-rl.md) **R1-Zero：不做 SFT、不用人工推理轨迹，纯 RL 跑出自我验证**　<sub>案例</sub>
- 「on-policy 和 off-policy，我该分别上哪些稳定手段」
  → [`case-0004`](../nodes/case-0004-qwen-30b-moe-stability.md) **30B MoE 烧掉几十万 GPU 小时，换一张稳定性配方表**　<sub>案例</sub>
- 「冷启动数据选哪一份，对最终效果影响大吗」
  → [`case-0004`](../nodes/case-0004-qwen-30b-moe-stability.md) **30B MoE 烧掉几十万 GPU 小时，换一张稳定性配方表**　<sub>案例</sub>
- 「我想知道别人在 MoE + 大规模下是怎么把训练跑稳的」
  → [`case-0004`](../nodes/case-0004-qwen-30b-moe-stability.md) **30B MoE 烧掉几十万 GPU 小时，换一张稳定性配方表**　<sub>案例</sub>
- 「我想看看熵和性能的关系是怎么被验证出来的」
  → [`case-0005`](../nodes/case-0005-entropy-predicts-performance.md) **只用前 36 步，预测后面 200 步的性能**　<sub>案例</sub>
- 「有没有办法在训练早期就知道这次大概能到多少分」
  → [`case-0005`](../nodes/case-0005-entropy-predicts-performance.md) **只用前 36 步，预测后面 200 步的性能**　<sub>案例</sub>
- 「熵掉下去和分数上不去，这两件事是同一件事吗」
  → [`case-0005`](../nodes/case-0005-entropy-predicts-performance.md) **只用前 36 步，预测后面 200 步的性能**　<sub>案例</sub>
- 「同一个 prompt 采样了好几条，为什么它们必须放在一起算」
  → [`con-0001`](../nodes/con-0001-group-relative-normalization.md) **GRPO 的组内归一化**　<sub>概念</sub>
- 「我在读 GRPO 的公式，想知道优势那一项的分母是哪来的」
  → [`con-0001`](../nodes/con-0001-group-relative-normalization.md) **GRPO 的组内归一化**　<sub>概念</sub>
- 「显存不够，想知道 GRPO 到底比 PPO 省了哪一块」
  → [`con-0002`](../nodes/con-0002-no-value-network.md) **GRPO 相比 PPO 省掉的那一份模型**　<sub>概念</sub>
- 「有人问我 GRPO 为什么不需要 critic」
  → [`con-0002`](../nodes/con-0002-no-value-network.md) **GRPO 相比 PPO 省掉的那一份模型**　<sub>概念</sub>
- 「我不知道那个一直不更新的模型是干什么用的」
  → [`con-0003`](../nodes/con-0003-reference-model-and-kl.md) **参考模型与 KL 惩罚**　<sub>概念</sub>
- 「我在纠结 KL 系数设多少」
  → [`con-0003`](../nodes/con-0003-reference-model-and-kl.md) **参考模型与 KL 惩罚**　<sub>概念</sub>
- 「日志里 entropy 这一项一路往下掉，我不知道该不该管」
  → [`con-0004`](../nodes/con-0004-policy-entropy.md) **策略熵**　<sub>概念</sub>
- 「有人说熵掉了是收敛，有人说是坏事」
  → [`con-0004`](../nodes/con-0004-policy-entropy.md) **策略熵**　<sub>概念</sub>
- 「我在看 loss 是怎么算的，不确定是对每个样本还是每个 token」
  → [`con-0005`](../nodes/con-0005-loss-aggregation-granularity.md) **损失聚合粒度：样本级与 token 级**　<sub>概念</sub>
- 「长回答里的 token 是不是被稀释了」
  → [`con-0005`](../nodes/con-0005-loss-aggregation-granularity.md) **损失聚合粒度：样本级与 token 级**　<sub>概念</sub>
- 「为什么有人明确说不要用神经奖励模型」
  → [`con-0006`](../nodes/con-0006-verifiable-reward.md) **可验证奖励（RLVR）与规则奖励**　<sub>概念</sub>
- 「我在决定奖励该用规则判还是训一个奖励模型」
  → [`con-0006`](../nodes/con-0006-verifiable-reward.md) **可验证奖励（RLVR）与规则奖励**　<sub>概念</sub>
- 「我的任务有标准答案，是不是可以不训 RM」
  → [`con-0006`](../nodes/con-0006-verifiable-reward.md) **可验证奖励（RLVR）与规则奖励**　<sub>概念</sub>
- 「同一个权重、同一个输入，两个引擎算出的概率为什么不一样」
  → [`con-0007`](../nodes/con-0007-training-inference-mismatch.md) **训练-推理偏差**　<sub>概念</sub>
- 「我的推理引擎为了吞吐换了 kernel，这算不算引入噪声」
  → [`con-0007`](../nodes/con-0007-training-inference-mismatch.md) **训练-推理偏差**　<sub>概念</sub>
- 「训练和推理用的不是同一个引擎，这会有影响吗」
  → [`con-0007`](../nodes/con-0007-training-inference-mismatch.md) **训练-推理偏差**　<sub>概念</sub>
- 「为什么要优化的是序列级奖励，实际算的却是 token 级的和」
  → [`con-0008`](../nodes/con-0008-first-order-approximation.md) **一阶近似：token 级目标凭什么代替序列级目标**　<sub>概念</sub>
- 「同一批 rollout 被切成好几份做多次更新，后面几次还作数吗」
  → [`con-0008`](../nodes/con-0008-first-order-approximation.md) **一阶近似：token 级目标凭什么代替序列级目标**　<sub>概念</sub>
- 「把一批数据多训几遍，为什么有人说不稳」
  → [`con-0008`](../nodes/con-0008-first-order-approximation.md) **一阶近似：token 级目标凭什么代替序列级目标**　<sub>概念</sub>
- 「我想用 Dr. GRPO 的做法，但不确定放弃了什么」
  → [`exc-0001`](../nodes/exc-0001-cost-of-removing-std.md) **去掉标准差项，代价是什么**　<sub>例外</sub>
- 「有人说把优势公式里的标准差去掉更好，是真的吗」
  → [`exc-0001`](../nodes/exc-0001-cost-of-removing-std.md) **去掉标准差项，代价是什么**　<sub>例外</sub>
- 「标准 PPO 实现里也有同样的长度偏差吗」
  → [`exc-0001`](../nodes/exc-0001-cost-of-removing-std.md) **去掉标准差项，代价是什么**　<sub>例外</sub>
- 「同样的配置别人跑不崩我跑就崩，是不是卡的问题」
  → [`exc-0002`](../nodes/exc-0002-non-hopper-precision.md) **换张卡就好了：精度问题的触发条件**　<sub>例外</sub>
- 「我的 grad_norm 在涨，但换了个 GPU 型号就没事」
  → [`exc-0002`](../nodes/exc-0002-non-hopper-precision.md) **换张卡就好了：精度问题的触发条件**　<sub>例外</sub>
- 「我要不要为这个精度问题改我的训练脚本」
  → [`exc-0002`](../nodes/exc-0002-non-hopper-precision.md) **换张卡就好了：精度问题的触发条件**　<sub>例外</sub>
- 「两个方案都说能解决长度问题，但它们说的原因不一样」
  → [`issue-0001`](../nodes/issue-0001-length-growth-attribution.md) **GRPO 训练中响应变长，该归因于什么**　<sub>议题</sub>
- 「我知道响应变长了，但不知道该改哪一处」
  → [`issue-0001`](../nodes/issue-0001-length-growth-attribution.md) **GRPO 训练中响应变长，该归因于什么**　<sub>议题</sub>
- 「有人说错误回答变长是偏差，这说法站得住吗」
  → [`issue-0001`](../nodes/issue-0001-length-growth-attribution.md) **GRPO 训练中响应变长，该归因于什么**　<sub>议题</sub>
- 「GRPO 不用价值网络，是不是意味着它的优势估计更差」
  → [`issue-0002`](../nodes/issue-0002-does-grpo-need-critic.md) **GRPO 是否真的不需要 critic**　<sub>议题</sub>
- 「GRPO 和 PPO 我该选哪个」
  → [`issue-0002`](../nodes/issue-0002-does-grpo-need-critic.md) **GRPO 是否真的不需要 critic**　<sub>议题</sub>
- 「我在选 PPO 还是 GRPO，想知道省掉 critic 有没有代价」
  → [`issue-0002`](../nodes/issue-0002-does-grpo-need-critic.md) **GRPO 是否真的不需要 critic**　<sub>议题</sub>
- 「选 GRPO 还是 PPO，区别到底在哪」
  → [`issue-0002`](../nodes/issue-0002-does-grpo-need-critic.md) **GRPO 是否真的不需要 critic**　<sub>议题</sub>
- 「我的模型回答越来越像一个模子刻出来的」
  → [`judge-0001`](../nodes/judge-0001-entropy-collapse.md) **熵在掉，该不该动手**　<sub>判断点</sub>
- 「日志里 entropy 一路往下掉，我不知道要不要停」
  → [`judge-0001`](../nodes/judge-0001-entropy-collapse.md) **熵在掉，该不该动手**　<sub>判断点</sub>
- 「同一个 prompt 采样出来的答案都对了，这一组还算不算数」
  → [`judge-0002`](../nodes/judge-0002-zero-advantage-group.md) **一组全对或全错，这一组是不是白跑了**　<sub>判断点</sub>
- 「训练日志里有一批 prompt 的奖励全是 1，我怀疑它们没贡献梯度」
  → [`judge-0002`](../nodes/judge-0002-zero-advantage-group.md) **一组全对或全错，这一组是不是白跑了**　<sub>判断点</sub>
- 「我想知道长度涨是坏事还是正常的推理变长」
  → [`judge-0003`](../nodes/judge-0003-response-length-growth.md) **响应越训越长，该不该管**　<sub>判断点</sub>
- 「我的模型回答越来越长，token 消耗翻了好几倍」
  → [`judge-0003`](../nodes/judge-0003-response-length-growth.md) **响应越训越长，该不该管**　<sub>判断点</sub>
- 「训练到后期模型开始写废话，但准确率没涨」
  → [`judge-0003`](../nodes/judge-0003-response-length-growth.md) **响应越训越长，该不该管**　<sub>判断点</sub>
- 「我怀疑奖励噪声来自那些没生成完的回答」
  → [`judge-0004`](../nodes/judge-0004-truncated-sample-reward.md) **被截断的样本，奖励怎么给**　<sub>判断点</sub>
- 「我怀疑有一批推对了的回答被判了 0 分」
  → [`judge-0004`](../nodes/judge-0004-truncated-sample-reward.md) **被截断的样本，奖励怎么给**　<sub>判断点</sub>
- 「有些回答顶到最大长度被截断了，这些样本该给 0 分吗」
  → [`judge-0004`](../nodes/judge-0004-truncated-sample-reward.md) **被截断的样本，奖励怎么给**　<sub>判断点</sub>
- 「答案被截断了，所以正则没匹配到，reward 直接判了 0」
  → [`judge-0004`](../nodes/judge-0004-truncated-sample-reward.md) **被截断的样本，奖励怎么给**　<sub>判断点</sub>
- 「我在纠结 β 设多少，也有人说干脆别开」
  → [`judge-0005`](../nodes/judge-0005-kl-penalty-on-or-off.md) **KL 项该不该开**　<sub>判断点</sub>
- 「模型训完变得不会说人话了，是不是 KL 没拉住」
  → [`judge-0005`](../nodes/judge-0005-kl-penalty-on-or-off.md) **KL 项该不该开**　<sub>判断点</sub>
- 「actor/grad_norm 从训练一开始就单调往上爬，调学习率也没用」
  → [`judge-0006`](../nodes/judge-0006-grad-norm-climbing.md) **grad_norm 一直往上走，是算法问题还是引擎问题**　<sub>判断点</sub>
- 「同样的配置别人跑不崩我跑就崩，不知道该先查哪里」
  → [`judge-0006`](../nodes/judge-0006-grad-norm-climbing.md) **grad_norm 一直往上走，是算法问题还是引擎问题**　<sub>判断点</sub>
- 「我想知道训练崩之前有没有一个能提前看到的指标」
  → [`judge-0006`](../nodes/judge-0006-grad-norm-climbing.md) **grad_norm 一直往上走，是算法问题还是引擎问题**　<sub>判断点</sub>
- 「我想在训练早期就知道这次大概能到多少分」
  → [`judge-0007`](../nodes/judge-0007-entropy-budget-pace.md) **熵掉得太快，还剩多少可烧**　<sub>判断点</sub>
- 「才训了几十步熵就掉了大半，后面还有必要接着训吗」
  → [`judge-0007`](../nodes/judge-0007-entropy-budget-pace.md) **熵掉得太快，还剩多少可烧**　<sub>判断点</sub>
- 「熵掉到什么程度就算没救了」
  → [`judge-0007`](../nodes/judge-0007-entropy-budget-pace.md) **熵掉得太快，还剩多少可烧**　<sub>判断点</sub>
- 「我试过加熵正则，系数调来调去不是没用就是炸，怎么办」
  → [`judge-0008`](../nodes/judge-0008-which-tokens-to-intervene.md) **该干预哪些 token：少数派在主导**　<sub>判断点</sub>
- 「熵崩了，我想动手但不想重写整个损失函数」
  → [`judge-0008`](../nodes/judge-0008-which-tokens-to-intervene.md) **该干预哪些 token：少数派在主导**　<sub>判断点</sub>
- 「该不该只对一小部分 token 做干预」
  → [`judge-0008`](../nodes/judge-0008-which-tokens-to-intervene.md) **该干预哪些 token：少数派在主导**　<sub>判断点</sub>
- 「reward 崩了，是奖励函数写错了还是算法的问题」
  → [`judge-0009`](../nodes/judge-0009-reward-not-rising.md) **reward 不涨或崩了，先查哪一边**　<sub>判断点</sub>
- 「reward 曲线跑到一半崩了，不知道先查哪里」
  → [`judge-0009`](../nodes/judge-0009-reward-not-rising.md) **reward 不涨或崩了，先查哪一边**　<sub>判断点</sub>
- 「同一套配置别人能跑起来，我的 reward 一直在低位震荡」
  → [`judge-0009`](../nodes/judge-0009-reward-not-rising.md) **reward 不涨或崩了，先查哪一边**　<sub>判断点</sub>
- 「训练跑了两百步 reward 就是不涨」
  → [`judge-0009`](../nodes/judge-0009-reward-not-rising.md) **reward 不涨或崩了，先查哪一边**　<sub>判断点</sub>
- 「同一个答案有好几种写法，正则只匹配一种，怎么办」
  → [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>判断点</sub>
- 「我的判分脚本可能认不出另一种写法」
  → [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>判断点</sub>
- 「我的判分规则用正则匹配，会不会有漏判」
  → [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>判断点</sub>
- 「答案格式稍微变一下，规则就判错了」
  → [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>判断点</sub>
- 「规则判对错的覆盖面够不够，怎么提前看出来」
  → [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>判断点</sub>
- 「规则奖励会不会冤枉了答对的模型」
  → [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>判断点</sub>
- 「还没开跑，我想先把判分规则的坑排掉」
  → [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>判断点</sub>
- 「奖励里给格式一点权重，会不会养出只摆格式的模型」
  → [`judge-0011`](../nodes/judge-0011-format-reward.md) **格式分该不该给**　<sub>判断点</sub>
- 「怎么让模型把推理过程单独写出来」
  → [`judge-0011`](../nodes/judge-0011-format-reward.md) **格式分该不该给**　<sub>判断点</sub>
- 「我打算用规则奖励，担心模型学会只对格式不对答案」
  → [`judge-0011`](../nodes/judge-0011-format-reward.md) **格式分该不该给**　<sub>判断点</sub>
- 「我该不该给格式分」
  → [`judge-0011`](../nodes/judge-0011-format-reward.md) **格式分该不该给**　<sub>判断点</sub>
- 「给格式分会不会让模型只摆样子」
  → [`judge-0011`](../nodes/judge-0011-format-reward.md) **格式分该不该给**　<sub>判断点</sub>
- 「要不要奖励它把思考写在标签里」
  → [`judge-0011`](../nodes/judge-0011-format-reward.md) **格式分该不该给**　<sub>判断点</sub>
- 「只看最后答案是不是信号太稀疏了」
  → [`judge-0012`](../nodes/judge-0012-process-reward.md) **过程分该不该给：先看中间判据是谁给的**　<sub>判断点</sub>
- 「我想让模型学会一步步想，但不知道奖励怎么给」
  → [`judge-0012`](../nodes/judge-0012-process-reward.md) **过程分该不该给：先看中间判据是谁给的**　<sub>判断点</sub>
- 「用过程奖励是不是一定比只看结果好」
  → [`judge-0012`](../nodes/judge-0012-process-reward.md) **过程分该不该给：先看中间判据是谁给的**　<sub>判断点</sub>
- 「要不要给中间步骤打分，还是只看最后答案」
  → [`judge-0012`](../nodes/judge-0012-process-reward.md) **过程分该不该给：先看中间判据是谁给的**　<sub>判断点</sub>
- 「过程分上面的那层判据从哪来」
  → [`judge-0012`](../nodes/judge-0012-process-reward.md) **过程分该不该给：先看中间判据是谁给的**　<sub>判断点</sub>
- 「过程奖励是不是一定比结果奖励好」
  → [`judge-0012`](../nodes/judge-0012-process-reward.md) **过程分该不该给：先看中间判据是谁给的**　<sub>判断点</sub>
- 「加长度惩罚和改优势公式，哪个对」
  → [`judge-0013`](../nodes/judge-0013-length-penalty.md) **长度惩罚要不要加：先分清你要治哪个长度病**　<sub>判断点</sub>
- 「奖励里要不要加长度惩罚」
  → [`judge-0013`](../nodes/judge-0013-length-penalty.md) **长度惩罚要不要加：先分清你要治哪个长度病**　<sub>判断点</sub>
- 「截断的那些样本要不要额外罚」
  → [`judge-0013`](../nodes/judge-0013-length-penalty.md) **长度惩罚要不要加：先分清你要治哪个长度病**　<sub>判断点</sub>
- 「模型回答越来越长，我想直接罚长度行不行」
  → [`judge-0013`](../nodes/judge-0013-length-penalty.md) **长度惩罚要不要加：先分清你要治哪个长度病**　<sub>判断点</sub>
- 「模型越写越啰嗦，罚长度有用吗」
  → [`judge-0013`](../nodes/judge-0013-length-penalty.md) **长度惩罚要不要加：先分清你要治哪个长度病**　<sub>判断点</sub>
- 「长度一直在涨，我想从奖励上压一压」
  → [`judge-0013`](../nodes/judge-0013-length-penalty.md) **长度惩罚要不要加：先分清你要治哪个长度病**　<sub>判断点</sub>
- 「SFT 已经能跑了，还有必要上 RL 吗」
  → [`judge-0014`](../nodes/judge-0014-rl-or-sft.md) **要不要上 RL，还是 SFT 就够了**　<sub>判断点</sub>
- 「什么时候该上 RL，什么时候 SFT 就够了」
  → [`judge-0014`](../nodes/judge-0014-rl-or-sft.md) **要不要上 RL，还是 SFT 就够了**　<sub>判断点</sub>
- 「我要不要上 RL，还是继续 SFT 就够了」
  → [`judge-0014`](../nodes/judge-0014-rl-or-sft.md) **要不要上 RL，还是 SFT 就够了**　<sub>判断点</sub>
- 「直接上 RL 行不行，还是得先 SFT」
  → [`judge-0014`](../nodes/judge-0014-rl-or-sft.md) **要不要上 RL，还是 SFT 就够了**　<sub>判断点</sub>
- 「DAPO 那四项技术分别打的是哪个问题」
  → [`stance-0001`](../nodes/stance-0001-dapo-attribution.md) **DAPO：长度与熵的问题出在损失聚合和裁剪上界**　<sub>立场</sub>
- 「我想知道 DAPO 认为长度增长的根因在哪」
  → [`stance-0001`](../nodes/stance-0001-dapo-attribution.md) **DAPO：长度与熵的问题出在损失聚合和裁剪上界**　<sub>立场</sub>
- 「Dr. GRPO 到底改了什么，为什么说 GRPO 有偏差」
  → [`stance-0002`](../nodes/stance-0002-drgrpo-optimization-bias.md) **Dr. GRPO：归一化本身就带偏差**　<sub>立场</sub>
- 「基座模型自己是不是已经有推理能力了」
  → [`stance-0002`](../nodes/stance-0002-drgrpo-optimization-bias.md) **Dr. GRPO：归一化本身就带偏差**　<sub>立场</sub>
- 「有人主张去掉优势公式里的标准差项」
  → [`stance-0002`](../nodes/stance-0002-drgrpo-optimization-bias.md) **Dr. GRPO：归一化本身就带偏差**　<sub>立场</sub>
- 「GRPO 当初为什么要去掉 critic」
  → [`stance-0003`](../nodes/stance-0003-grpo-original-motivation.md) **GRPO 原文：省掉 critic 是为了同时解决两件事**　<sub>立场</sub>
- 「我想知道 GRPO 的动机是省内存还是别的」
  → [`stance-0003`](../nodes/stance-0003-grpo-original-motivation.md) **GRPO 原文：省掉 critic 是为了同时解决两件事**　<sub>立场</sub>

---

## 按概念

### 概念
- [`con-0001`](../nodes/con-0001-group-relative-normalization.md) **GRPO 的组内归一化**　<sub>别名：group relative advantage、组内相对优势、组内标准化</sub>
- [`con-0002`](../nodes/con-0002-no-value-network.md) **GRPO 相比 PPO 省掉的那一份模型**　<sub>别名：value network、critic、价值网络、critic model</sub>
- [`con-0003`](../nodes/con-0003-reference-model-and-kl.md) **参考模型与 KL 惩罚**　<sub>别名：reference model、KL penalty、KL 正则、参考策略</sub>
- [`con-0004`](../nodes/con-0004-policy-entropy.md) **策略熵**　<sub>别名：entropy、策略熵、entropy collapse</sub>
- [`con-0005`](../nodes/con-0005-loss-aggregation-granularity.md) **损失聚合粒度：样本级与 token 级**　<sub>别名：loss aggregation、token-level loss、sample-level loss</sub>
- [`con-0006`](../nodes/con-0006-verifiable-reward.md) **可验证奖励（RLVR）与规则奖励**　<sub>别名：RLVR、rule-based reward、verifiable reward、规则奖励</sub>
- [`con-0007`](../nodes/con-0007-training-inference-mismatch.md) **训练-推理偏差**　<sub>别名：TIM、training-inference mismatch、训推不一致、training-inference discrepancy</sub>
- [`con-0008`](../nodes/con-0008-first-order-approximation.md) **一阶近似：token 级目标凭什么代替序列级目标**　<sub>别名：first-order approximation、一阶近似、surrogate objective、策略陈旧度、policy staleness</sub>

### 判断点
- [`judge-0001`](../nodes/judge-0001-entropy-collapse.md) **熵在掉，该不该动手**　<sub>别名：entropy collapse、熵坍缩</sub>
- [`judge-0002`](../nodes/judge-0002-zero-advantage-group.md) **一组全对或全错，这一组是不是白跑了**　<sub>别名：zero advantage、零优势、全对组</sub>
- [`judge-0003`](../nodes/judge-0003-response-length-growth.md) **响应越训越长，该不该管**　<sub>别名：length bias、长度偏置、length explosion</sub>
- [`judge-0004`](../nodes/judge-0004-truncated-sample-reward.md) **被截断的样本，奖励怎么给**　<sub>别名：overlong reward shaping、truncation、截断样本、假阴性奖励、判分漏判</sub>
- [`judge-0005`](../nodes/judge-0005-kl-penalty-on-or-off.md) **KL 项该不该开**　<sub>别名：KL penalty、KL 系数</sub>
- [`judge-0006`](../nodes/judge-0006-grad-norm-climbing.md) **grad_norm 一直往上走，是算法问题还是引擎问题**　<sub>别名：grad_norm 排查、rollout_probs_diff_mean、训推不匹配判据</sub>
- [`judge-0007`](../nodes/judge-0007-entropy-budget-pace.md) **熵掉得太快，还剩多少可烧**　<sub>别名：熵消耗节奏、性能上限预测、熵-性能变换方程</sub>
- [`judge-0008`](../nodes/judge-0008-which-tokens-to-intervene.md) **该干预哪些 token：少数派在主导**　<sub>别名：高协方差 token、Clip-Cov、KL-Cov、token 级干预</sub>
- [`judge-0009`](../nodes/judge-0009-reward-not-rising.md) **reward 不涨或崩了，先查哪一边**　<sub>别名：reward 崩溃、reward 不涨、奖励误判、假阴性率、分诊</sub>
- [`judge-0010`](../nodes/judge-0010-grader-coverage.md) **判分规则写好了，怎么知道它会漏判**　<sub>别名：判分漏判、正则漏判、规则覆盖、等价写法</sub>
- [`judge-0011`](../nodes/judge-0011-format-reward.md) **格式分该不该给**　<sub>别名：格式奖励、format reward、格式分、格式分与长度耦合</sub>
- [`judge-0012`](../nodes/judge-0012-process-reward.md) **过程分该不该给：先看中间判据是谁给的**　<sub>别名：过程奖励、process reward、PRM、中间步骤打分</sub>
- [`judge-0013`](../nodes/judge-0013-length-penalty.md) **长度惩罚要不要加：先分清你要治哪个长度病**　<sub>别名：长度惩罚、overlong reward shaping、长度偏差、越长越罚</sub>
- [`judge-0014`](../nodes/judge-0014-rl-or-sft.md) **要不要上 RL，还是 SFT 就够了**　<sub>别名：要不要上 RL、SFT 还是 RL、RL 必要性、SFT 够了没</sub>

### 例外
- [`exc-0001`](../nodes/exc-0001-cost-of-removing-std.md) **去掉标准差项，代价是什么**　<sub>别名：Dr. GRPO、unbiased optimization、去掉 std</sub>
- [`exc-0002`](../nodes/exc-0002-non-hopper-precision.md) **换张卡就好了：精度问题的触发条件**　<sub>别名：非 Hopper GPU、vLLM issue 22103、disable_cascade_attn、A100 精度问题</sub>

### 议题
- [`issue-0001`](../nodes/issue-0001-length-growth-attribution.md) **GRPO 训练中响应变长，该归因于什么**　<sub>别名：length bias、长度偏置归因</sub>
- [`issue-0002`](../nodes/issue-0002-does-grpo-need-critic.md) **GRPO 是否真的不需要 critic**　<sub>别名：critic、value function、价值函数必要性</sub>

### 立场
- [`stance-0001`](../nodes/stance-0001-dapo-attribution.md) **DAPO：长度与熵的问题出在损失聚合和裁剪上界**　<sub>别名：DAPO 归因</sub>
- [`stance-0002`](../nodes/stance-0002-drgrpo-optimization-bias.md) **Dr. GRPO：归一化本身就带偏差**　<sub>别名：Dr. GRPO、unbiased optimization</sub>
- [`stance-0003`](../nodes/stance-0003-grpo-original-motivation.md) **GRPO 原文：省掉 critic 是为了同时解决两件事**　<sub>别名：GRPO 原始动机</sub>

### 论据
- [`arg-0001`](../nodes/arg-0001-dapo-ablation-chain.md) **增量消融：四项技术各加一项，分数单调上升**　<sub>别名：ablation、消融链</sub>
- [`arg-0002`](../nodes/arg-0002-token-efficiency.md) **把优势公式的偏差与「token 效率」直接挂钩**　<sub>别名：token efficiency、无偏优化</sub>

### 案例
- [`case-0001`](../nodes/case-0001-dapo-aime24.md) **DAPO：在 AIME 2024 上把朴素 GRPO 从 30 分做到 50 分**　<sub>别名：DAPO 实验</sub>
- [`case-0002`](../nodes/case-0002-drgrpo-7b-aime.md) **Dr. GRPO：7B 基座做到 AIME 2024 的 43.3%**　<sub>别名：Dr. GRPO 实验、Oat-Zero-7B、minimalist R1-Zero recipe</sub>
- [`case-0003`](../nodes/case-0003-r1-zero-pure-rl.md) **R1-Zero：不做 SFT、不用人工推理轨迹，纯 RL 跑出自我验证**　<sub>别名：R1-Zero、DeepSeek-R1</sub>
- [`case-0004`](../nodes/case-0004-qwen-30b-moe-stability.md) **30B MoE 烧掉几十万 GPU 小时，换一张稳定性配方表**　<sub>别名：MiniRL、Stabilizing RL with LLMs 实验、Qwen 稳定性实验</sub>
- [`case-0005`](../nodes/case-0005-entropy-predicts-performance.md) **只用前 36 步，预测后面 200 步的性能**　<sub>别名：熵-性能变换方程验证、entropy 拟合实验</sub>

---

## 关系（`relations` 是有向的）
> 方向约定继承 Scaffold：**论据 → 立场**、**立场 → 议题**、**例外 → 被覆盖的节点**、**概念：具体 → 基础**。反向关系写在正文里，不写进 `relations`（否则构成环，被 R3 判错）。

- `arg-0001` → `stance-0001`
- `arg-0002` → `stance-0002`
- `case-0001` → `arg-0001`
- `case-0002` → `stance-0002`、`arg-0002`
- `case-0003` → `con-0006`
- `case-0004` → `con-0007`
- `case-0005` → `con-0004`
- `con-0002` → `con-0001`
- `con-0003` → `con-0002`
- `con-0004` → `con-0001`
- `con-0005` → `con-0001`
- `con-0006` → `con-0003`
- `con-0007` → `con-0008`
- `exc-0001` → `con-0001`、`issue-0001`
- `exc-0002` → `judge-0006`
- `issue-0001` → `con-0005`、`con-0001`
- `issue-0002` → `con-0002`
- `judge-0001` → `con-0004`、`exc-0001`
- `judge-0002` → `con-0001`、`con-0005`
- `judge-0003` → `issue-0001`
- `judge-0004` → `con-0006`、`case-0001`
- `judge-0005` → `con-0003`
- `judge-0006` → `con-0007`
- `judge-0007` → `con-0004`
- `judge-0008` → `con-0004`
- `judge-0009` → `con-0006`、`judge-0004`、`judge-0002`、`judge-0001`、`judge-0006`
- `judge-0010` → `con-0006`
- `judge-0011` → `con-0006`
- `judge-0012` → `con-0001`、`con-0006`
- `judge-0013` → `con-0005`、`con-0006`
- `judge-0014` → `con-0006`、`con-0002`
- `stance-0001` → `issue-0001`
- `stance-0002` → `issue-0001`
- `stance-0003` → `issue-0002`
