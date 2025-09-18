# 数据目录

本目录包含ToolACE项目的所有数据文件，包括原始数据、生成数据和示例数据。

## 📁 目录结构

```
data/
├── README.md                    # 本文档
├── raw/                         # 原始数据
│   ├── pretraining_docs/        # 预训练文档（用于TSS）
│   └── seed_apis/               # 种子API定义
├── generated/                   # 生成的数据
│   ├── apis/                    # TSS生成的API池
│   ├── dialogs/                 # SDG生成的对话
│   └── verified/                # DLV验证通过的最终数据
└── examples/                    # 示例数据
    ├── api_examples.json        # API定义示例
    ├── dialog_examples.json     # 对话数据示例
    └── config_examples/         # 配置示例
```

## 📊 数据类型说明

### API定义数据
生成的API定义采用JSON Schema格式：

```json
{
  "name": "get_weather",
  "description": "获取指定地点的天气信息",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "地理位置"
      },
      "days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 14,
        "description": "预报天数"
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

### 对话数据
生成的对话数据包含多轮交互：

```json
{
  "dialog_id": "dialog_001",
  "dialog_type": "single",
  "api_candidates": [...],
  "turns": [
    {
      "role": "user",
      "content": "请查看北京今天的天气",
      "turn_id": 1
    },
    {
      "role": "assistant",
      "content": "我来为您查询北京今天的天气信息。",
      "function_calls": [
        {
          "name": "get_weather",
          "parameters": {
            "location": "北京",
            "days": 1
          }
        }
      ],
      "turn_id": 2
    }
  ],
  "complexity_score": 0.35,
  "quality_metrics": {
    "consistency_score": 0.9,
    "completeness_score": 0.85
  }
}
```

## 🔄 数据流程

1. **原始数据** (`raw/`) → **TSS模块** → **API池** (`generated/apis/`)
2. **API池** → **SDG模块** → **对话数据** (`generated/dialogs/`)
3. **对话数据** → **DLV模块** → **验证数据** (`generated/verified/`)

## 📏 数据规模

### 目标数据规模
- **API数量**: 26,507个
- **覆盖领域**: 390个
- **对话数量**: 100,000个
- **验证通过率**: 85%+

### 数据分布
- **单一函数调用**: 30%
- **并行函数调用**: 25%
- **依赖函数调用**: 25%
- **非工具使用**: 20%

## 💾 存储格式

### JSON格式
- **优点**: 人类可读，结构清晰
- **用途**: 配置文件，小规模数据
- **编码**: UTF-8

### JSONL格式
- **优点**: 流式处理，内存友好
- **用途**: 大规模训练数据
- **编码**: UTF-8，每行一个JSON对象

## 🔍 数据质量控制

### 自动验证
- **格式验证**: JSON Schema合规性
- **内容验证**: 参数完整性和类型检查
- **逻辑验证**: 对话流程合理性

### 人工抽检
- **抽检比例**: 5%随机抽样
- **检查维度**: 准确性、一致性、自然度
- **反馈循环**: 问题数据用于改进算法

## 📈 统计信息

数据生成完成后会产生详细的统计报告：

```json
{
  "api_statistics": {
    "total_apis": 26507,
    "domains": 390,
    "avg_complexity": 0.65,
    "parameter_types": {
      "string": 45.2,
      "integer": 23.1,
      "boolean": 15.6,
      "array": 10.3,
      "object": 5.8
    }
  },
  "dialog_statistics": {
    "total_dialogs": 100000,
    "avg_turns": 3.2,
    "type_distribution": {
      "single": 30000,
      "parallel": 25000,
      "dependent": 25000,
      "non_tool": 20000
    }
  },
  "quality_statistics": {
    "verification_pass_rate": 0.87,
    "avg_quality_score": 0.82,
    "consistency_score": 0.91
  }
}
```

## 🔧 数据使用

### 加载数据
```python
import json

# 加载API池
with open('data/generated/apis/api_pool.json', 'r') as f:
    api_pool = json.load(f)

# 加载验证数据
with open('data/generated/verified/verified_dialogs.json', 'r') as f:
    dialogs = json.load(f)
```

### 数据预处理
```python
from toolace.utils.data_utils import preprocess_dialogs

# 预处理对话数据用于训练
train_data = preprocess_dialogs(dialogs, format='huggingface')
```

## 🚨 注意事项

### 文件大小
- API池文件可能超过100MB
- 完整对话数据可能超过1GB
- 建议使用流式处理大文件

### 版本控制
- 大数据文件不建议放入Git
- 使用Git LFS或外部存储
- 维护数据版本记录

### 隐私保护
- 生成数据为合成数据，无隐私问题
- 预训练文档需检查版权和隐私
- 遵守相关法律法规
