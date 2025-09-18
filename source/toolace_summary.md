# ToolACE: Winning the Points of LLM Function Calling

## Implementation

### 核心架构
ToolACE采用三模块自动化数据生成管道：

#### 1. Tool Self-Evolution Synthesis (TSS) - 工具自我进化合成
**三步进化过程**：
- **Speciation (物种形成)**: 从预训练数据构建分层API上下文树，涵盖390个领域的26,507个API
- **Adaptation (适应)**: 为每个API分配独特功能，支持从简单到复杂的分层设计
- **Evolution (进化)**: 通过多样性指标和API示例缓冲区持续优化API质量

#### 2. Self-Guided Dialog Generation (SDG) - 自导向对话生成
**多智能体协作框架**：
- **User Agent**: 生成用户请求，支持自导向复杂化调整
- **Assistant Agent**: 处理API调用决策，包含结构化思维过程和多次生成一致性检查
- **Tool Agent**: 模拟API执行结果

**复杂性评估机制**：
```
HM(x, y) = -1/ny * Σ(i=1 to ny) log p(ti|x, t1, ..., ti-1)
```
- 使用待训练模型自身作为复杂性评估器
- 基于损失值动态调整下一轮对话生成的复杂度
- 验证了损失值与API数量、使用工具数、查询-API相似度的正相关关系

**数据类型覆盖**：
- Single function calls (单一函数调用)
- Parallel function calls (并行函数调用)
- Dependent function calls (依赖函数调用)  
- Non-tool-use dialogs (非工具使用对话)

#### 3. Dual-Layer Verification (DLV) - 双层验证系统
**规则验证层**：
- API定义清晰度检查
- 函数调用可执行性验证（API名称匹配、必需参数完整性、格式规范性）
- 对话正确性和数据样本一致性检查

**模型验证层**（三个专门的expert agents）：
- **Hallucination Detection**: 检测函数调用参数是否虚构
- **Consistency Validation**: 验证响应与用户任务的一致性
- **Tool Response Check**: 确保模拟工具响应符合API定义

### 技术创新
- **首个强调API多样性合成的工作**：通过26,507个API覆盖390个领域
- **自适应复杂性控制**：根据目标模型能力动态调整训练数据难度
- **嵌套参数支持**：支持复杂的lists of lists和lists of dictionaries
- **全场景覆盖**：同时支持并行、依赖和多轮函数调用

## Key Findings

### 性能突破
- **ToolACE-8B**在BFCL-v3排行榜上排名第3，超越了大多数API-based和开源模型
- 在API-Bank上达到75.94% Call准确率，与GPT-4系列性能相当
- **参数效率显著**：仅8B参数就能与数万亿参数的GPT-4竞争

### 核心发现

#### 1. 数据质量比模型规模更重要
- 高质量合成数据使小模型达到大模型性能
- ToolACE-8B超越了70B参数的Meta-Llama-3模型

#### 2. 复杂性评估的有效性
通过实验验证，损失值与以下因素正相关：
- 候选API数量 (0-9个API)
- 实际使用API数量 (0-7个API)  
- 用户查询与API描述的不相似度 (0.1-0.9)

#### 3. 平衡性能力突出
- **Relevance**: 85.37% (何时调用函数)
- **Irrelevance**: 83.81% (何时不调用函数)
- 在这两个关键指标上保持优秀平衡，避免了过度调用或调用不足的问题

#### 4. 各组件的贡献度
**数据验证系统影响**：
- 无验证 vs 规则验证：显著提升可执行准确率
- 规则验证 vs 双层验证：进一步提升AST和整体准确率

**复杂性控制效果**：
- 适中复杂度数据的训练效果最佳
- 过简单或过复杂的数据都会降低模型性能

**API多样性价值**：
- 高多样性数据显著提升irrelevance检测能力
- API多样性与整体性能呈正相关

#### 5. 跨模型泛化能力
在Qwen-1.5系列(0.5B-7B)和LLaMA-3系列上的实验表明：
- ToolACE数据对不同规模模型都有显著提升
- 较小模型(0.5B, 1.8B)从几乎无函数调用能力提升到可用水平
- 展现了良好的scaling性能

#### 6. 通用能力保持
在MMLU、HumanEval、GSM8K、CommonSenseQA等基准测试中：
- ToolACE-8B相比原始LLaMA-3.1-8B基本无性能降低
- 函数调用专业化训练不会损害模型的通用能力

### 局限性与未来方向
- **多轮对话性能有待提升**：Multi turn得分仍相对较低(14.37%)
- **通用能力仍有差距**：相比GPT-4在推理和理解能力上还有提升空间
- **复杂性评估的计算开销**：评估过程的计算复杂度随模型规模增长
- **多能力协同优化**：如何在保持函数调用性能的同时提升其他能力仍是开放问题