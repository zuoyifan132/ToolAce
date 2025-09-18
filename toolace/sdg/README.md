# Self-Guided Dialog Generation (SDG) 模块

## 📖 模块概述

Self-Guided Dialog Generation (SDG) 是ToolACE框架的核心模块，负责生成适合目标LLM能力的函数调用对话数据。该模块采用复杂度评估器和多代理生成器相结合的方式，确保生成的对话数据具有适当的复杂度，能够有效填补模型的能力缺口。

## 🎯 核心特性

- **自适应复杂度**: 根据目标LLM的能力动态调整对话复杂度
- **多代理协作**: 通过用户、助手、工具三个代理的角色扮演生成对话
- **多类型支持**: 生成单一、并行、依赖和非工具使用四种类型的对话
- **质量保证**: 多实例一致性检查确保响应质量
- **结构化思维**: 专门为函数调用设计的思维过程

## 🏗️ 模块架构

```
sdg/
├── README.md                        # 本文档
├── __init__.py                      # 模块初始化
├── complexity_evaluator.py         # 复杂度评估器
├── multi_agent_generator.py        # 多代理生成器
├── self_guided_complication.py     # 自引导复杂化策略
├── agents/                          # 代理实现
│   ├── __init__.py                  # 代理模块初始化
│   ├── user_agent.py               # 用户代理实现
│   ├── assistant_agent.py          # 助手代理实现
│   └── tool_agent.py               # 工具代理实现
```

## 🔄 工作流程

### 1. 复杂度评估 (Complexity Evaluation)
使用目标LLM作为评估器，计算数据样本的复杂度：

**复杂度计算公式**:
```
H_M(x, y) = -1/n_y * Σ(i=1 to n_y) log p(t_i | x, t_1, ..., t_{i-1})
```

**复杂度影响因素**:
- 候选API数量 - 选择难度
- 使用API数量 - 查询复杂度 
- 查询与API描述的相似度 - 推理难度

### 2. 多代理对话生成 (Multi-Agent Dialog Generation)
通过三个代理的协作生成四种类型的对话：

**代理角色**:
- **用户代理**: 发起请求，提供额外信息，实施复杂化策略
- **助手代理**: 处理查询，调用API，总结结果
- **工具代理**: 执行API，返回模拟结果

**对话类型**:
- **单一函数调用**: 简单直接的API调用
- **并行函数调用**: 同时调用多个API
- **依赖函数调用**: 基于前一个API结果调用下一个API
- **非工具使用**: 不需要API的对话

### 3. 自引导复杂化 (Self-Guided Complication)
根据复杂度评估结果动态调整对话：

- **过于简单**: 指导用户代理生成更复杂的查询
- **过于复杂**: 指导用户代理简化查询
- **适当复杂度**: 保持当前复杂度水平

## 📁 文件详细说明

### `complexity_evaluator.py`
实现复杂度评估的核心逻辑：

**主要功能**:
- 使用目标LLM计算数据样本损失
- 建立适当的复杂度范围
- 提供复杂度指导信息
- 分析复杂度影响因素

**关键类/函数**:
- `ComplexityEvaluator`: 复杂度评估器主类
- `calculate_loss()`: 计算样本损失值
- `establish_complexity_range()`: 建立复杂度范围
- `analyze_complexity_factors()`: 分析复杂度因素

### `multi_agent_generator.py`
协调多个代理进行对话生成：

**主要功能**:
- 管理三个代理的交互流程
- 处理不同类型对话的生成逻辑
- 实施多实例一致性检查
- 控制对话轮次和长度

**关键类/函数**:
- `MultiAgentGenerator`: 多代理生成器
- `generate_dialog()`: 生成完整对话
- `coordinate_agents()`: 协调代理交互
- `consistency_check()`: 一致性检查

### `self_guided_complication.py`
实现自引导复杂化策略：

**主要功能**:
- 根据复杂度评估调整用户指令
- 实施增加或降低复杂度的策略
- 监控复杂度变化趋势
- 确保适当的学习曲线

**关键类/函数**:
- `SelfGuidedComplicator`: 自引导复杂化器
- `adjust_complexity()`: 调整复杂度
- `generate_complication_instruction()`: 生成复杂化指令
- `monitor_complexity_trend()`: 监控复杂度趋势

### `agents/user_agent.py`
用户代理的具体实现：

**主要功能**:
- 生成初始查询请求
- 响应助手的询问
- 实施复杂化策略
- 提供额外信息和澄清

**行为模式**:
- 基于API功能生成自然查询
- 根据复杂度指导调整查询
- 模拟真实用户的交互行为

### `agents/assistant_agent.py`
助手代理的具体实现：

**主要功能**:
- 分析用户查询意图
- 选择和调用适当的API
- 处理API返回结果
- 生成最终响应

**决策过程**:
- 结构化思维过程
- 多实例生成和一致性检查
- 错误处理和重试机制

### `agents/tool_agent.py`
工具代理的具体实现：

**主要功能**:
- 解析API调用参数
- 模拟API执行过程
- 生成符合API定义的返回结果
- 处理异常和错误情况

**模拟策略**:
- 基于API定义生成合理结果
- 考虑参数约束和业务逻辑
- 模拟真实API的行为特征

## 🔧 使用示例

```python
from toolace.sdg import SDG
from toolace.sdg.complexity_evaluator import ComplexityEvaluator
from toolace.sdg.multi_agent_generator import MultiAgentGenerator

# 初始化SDG模块
sdg = SDG(target_model_path="models/llama3.1-8b")

# 设置API候选列表
api_candidates = api_pool.sample_apis(count=5)

# 生成对话
dialog = sdg.generate_dialog(
    api_candidates=api_candidates,
    dialog_type="parallel",
    target_turns=4
)

# 输出对话
for turn in dialog.turns:
    print(f"{turn.role}: {turn.content}")
```

## 📊 输出数据格式

生成的对话数据采用标准化JSON格式：

```json
{
  "dialog_id": "dialog_001",
  "dialog_type": "parallel",
  "api_candidates": [...],
  "turns": [
    {
      "role": "user",
      "content": "我想同时查看北京的天气和股票行情",
      "turn_id": 1
    },
    {
      "role": "assistant", 
      "content": "我来帮您同时获取这两个信息...",
      "function_calls": [
        {
          "name": "get_weather",
          "parameters": {"location": "北京"}
        },
        {
          "name": "get_stock_price", 
          "parameters": {"symbol": "000001"}
        }
      ],
      "turn_id": 2
    }
  ],
  "complexity_score": 0.65,
  "quality_metrics": {
    "consistency_score": 0.9,
    "completeness_score": 0.85
  }
}
```

## 📈 复杂度管理

### 复杂度范围设定
- **下界**: 模型已掌握的案例损失值
- **上界**: 模型学习困难的案例损失值
- **目标区间**: 略高于当前能力的适中难度

### 动态调整策略
```python
if current_loss < lower_bound:
    # 数据过于简单，增加复杂度
    complication_strategy = "increase_apis"
elif current_loss > upper_bound:
    # 数据过于复杂，降低复杂度
    complication_strategy = "simplify_query"
else:
    # 复杂度适中，保持当前水平
    complication_strategy = "maintain"
```

## 🎯 质量保证机制

### 多实例一致性检查
- 生成多个候选响应
- 检查决策一致性
- 选择一致性最高的响应

### 结构化思维过程
```
1. 理解用户查询
2. 分析所需功能
3. 选择合适API
4. 规划调用顺序
5. 执行并处理结果
```

### 错误处理和重试
- 参数验证失败重新生成
- API调用错误自动重试
- 响应质量不达标重新生成

## 🔗 与其他模块的集成

SDG模块接收TSS生成的API池，生成的对话数据将送入DLV模块进行验证：

```
TSS (API池) → SDG (对话生成) → DLV (质量验证)
```

## 🛠️ 配置选项

在 `config/data_config.yaml` 中配置SDG相关参数：

```yaml
sdg:
  target_model_path: "models/llama3.1-8b"
  max_dialog_turns: 6
  complexity_range: [0.3, 0.8]
  consistency_threshold: 0.8
  dialog_types:
    - "single"
    - "parallel" 
    - "dependent"
    - "non_tool"
  agent_configs:
    user_agent:
      temperature: 0.8
      max_retries: 3
    assistant_agent:
      temperature: 0.7
      thinking_steps: 5
    tool_agent:
      simulation_mode: "realistic"
```

## 📊 性能指标

- **对话生成速度**: 平均每分钟生成50个高质量对话
- **复杂度控制精度**: 95%的对话在目标复杂度范围内
- **一致性检查准确率**: 98%的不一致响应被成功识别
- **类型分布平衡**: 四种对话类型分布均匀
