# Tool Self-Evolution Synthesis (TSS) 模块

## 📖 模块概述

Tool Self-Evolution Synthesis (TSS) 是ToolACE框架的核心模块之一，负责自动生成多样化、高质量的API定义。该模块通过模拟生物进化过程，从预训练数据中提取API领域知识，并通过物种形成、适应和演化三个步骤创建全面的API池。

## 🎯 核心功能

TSS模块生成了包含26,507个API的综合API池，覆盖390个不同领域，支持：
- 嵌套参数类型（列表的列表、字典的列表等）
- 多样化的数据类型和约束
- 跨领域的API功能覆盖
- 自演化和持续更新机制

## 🏗️ 模块架构

```
tss/
├── README.md                    # 本文档
├── __init__.py                  # 模块初始化
├── speciation.py               # 物种形成：API上下文树构建
├── adaptation.py               # 适应：域和多样性级别指定
├── evolution.py                # 演化：API持续改进和生成
└── api_pool.py                 # API池管理和维护
```

## 🔄 三步演化过程

### 1. Speciation (物种形成)
- **目标**: 构建分层API上下文树，指导合成过程
- **输入**: 预训练数据中的API相关文档
- **过程**: 
  - 从技术手册、API文档、产品规格等提取API领域
  - 递归生成API功能和用例的层次结构
  - 创建涵盖各种应用和行业的综合上下文树
- **输出**: 分层API上下文树，每个节点代表可能的API功能

### 2. Adaptation (适应)
- **目标**: 为每个API指定领域和多样性级别
- **过程**:
  - 从API上下文树中采样子树
  - 为每个API获取独特的功能组合
  - 控制API的复杂度和专业化程度
- **多样性控制**:
  - 某些API覆盖更多节点→更多领域特定和详细能力
  - 某些API只包含单个节点→简单直接的功能

### 3. Evolution (演化)
- **目标**: 基于结果和新需求持续改进API
- **过程**:
  - 根据采样的子树和API示例生成新API
  - 应用多样性指标进行变异和改进
  - 维护API示例缓冲区供迭代使用
- **多样性指标**:
  - 添加新功能或参数
  - 包含额外约束
  - 变异参数类型
  - 更新返回结果

## 📁 文件详细说明

### `speciation.py`
负责从预训练数据构建API上下文树的核心逻辑：

**主要功能**:
- 解析预训练数据中的API相关文档
- 提取API领域和功能信息
- 构建分层上下文树结构
- 支持递归节点生成

**关键类/函数**:
- `APIContextTree`: API上下文树的数据结构
- `extract_api_domains()`: 从文档中提取API领域
- `build_context_tree()`: 构建分层上下文树
- `get_api_functionalities()`: 获取API功能列表

### `adaptation.py`
处理API的领域适应和多样性级别指定：

**主要功能**:
- 从上下文树中采样子树
- 为API分配独特功能组合
- 控制API复杂度和专业化程度
- 确保API功能的唯一性

**关键类/函数**:
- `DomainAdapter`: 领域适应器
- `sample_subtree()`: 子树采样算法
- `assign_functionalities()`: 功能分配逻辑
- `calculate_diversity_level()`: 多样性级别计算

### `evolution.py`
实现API的持续演化和改进机制：

**主要功能**:
- 基于子树和示例生成新API
- 应用多样性指标进行API变异
- 管理API生成的迭代过程
- 确保生成API的质量和多样性

**关键类/函数**:
- `APIEvolver`: API演化器
- `generate_api()`: API生成核心算法
- `apply_diversity_mutations()`: 应用多样性变异
- `validate_api_definition()`: API定义验证

### `api_pool.py`
管理和维护整个API池：

**主要功能**:
- API池的存储和检索
- API示例缓冲区管理
- API质量评估和筛选
- 统计信息收集和报告

**关键类/函数**:
- `APIPool`: API池管理器
- `add_api()`: 添加API到池中
- `sample_apis()`: 从池中采样API
- `get_pool_statistics()`: 获取池统计信息

## 🔧 使用示例

```python
from toolace.tss import TSS
from toolace.tss.speciation import APIContextTree
from toolace.tss.adaptation import DomainAdapter
from toolace.tss.evolution import APIEvolver

# 初始化TSS模块
tss = TSS(config_path="config/data_config.yaml")

# 构建API上下文树
context_tree = APIContextTree()
context_tree.build_from_pretraining_data("data/raw/pretraining_docs/")

# 领域适应
adapter = DomainAdapter(context_tree)
sampled_subtree = adapter.sample_subtree(diversity_level="medium")

# API演化
evolver = APIEvolver()
new_api = evolver.generate_api(
    subtree=sampled_subtree,
    example_api=tss.api_pool.sample_example()
)

# 添加到API池
tss.api_pool.add_api(new_api)
```

## 📊 输出数据格式

生成的API定义遵循标准JSON Schema格式：

```json
{
  "name": "get_weather_forecast",
  "description": "获取指定地点的天气预报信息",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "地理位置（城市名或坐标）"
      },
      "days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 14,
        "description": "预报天数"
      },
      "include_hourly": {
        "type": "boolean",
        "description": "是否包含每小时预报"
      }
    },
    "required": ["location"]
  },
  "returns": {
    "type": "object",
    "description": "天气预报数据"
  }
}
```

## 🎯 设计原则

1. **多样性优先**: 通过自演化确保API的多样性和覆盖面
2. **质量保证**: 严格的验证机制确保API定义的准确性
3. **可扩展性**: 支持持续添加新的API领域和功能
4. **灵活适应**: 根据不同需求调整API复杂度和专业化程度

## 📈 性能指标

- **API数量**: 26,507个独特API
- **领域覆盖**: 390个不同领域
- **参数类型**: 支持嵌套复杂类型
- **生成效率**: 平均每小时生成500+高质量API

## 🔗 与其他模块的集成

TSS模块生成的API池将被SDG模块用于对话生成，生成的API定义需要通过DLV模块的验证。模块间的数据流：

```
TSS (API生成) → SDG (对话生成) → DLV (质量验证)
```

## 🛠️ 配置选项

在 `config/data_config.yaml` 中可以配置TSS相关参数：

```yaml
tss:
  pretraining_data_path: "data/raw/pretraining_docs/"
  api_pool_size: 30000
  diversity_levels: ["low", "medium", "high"]
  evolution_iterations: 5
  context_tree_depth: 4
```
