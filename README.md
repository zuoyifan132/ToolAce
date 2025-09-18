# ToolACE: 函数调用LLM训练数据生成管道

[![论文](https://img.shields.io/badge/论文-ICLR%202025-blue)](source/2409.00920v2.pdf)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://python.org)

> **ToolACE: Winning the Points of LLM Function Calling**  
> 一个自动化的代理管道，旨在生成准确、复杂和多样化的工具学习数据，专门针对大语言模型的能力进行定制。

## 📖 项目概述

ToolACE是一个系统性的工具学习管道，通过三个核心模块自动合成高质量的函数调用数据：

1. **Tool Self-Evolution Synthesis (TSS)** - 工具自演化合成模块
2. **Self-Guided Dialog Generation (SDG)** - 自引导对话生成模块  
3. **Dual-Layer Verification (DLV)** - 双层验证模块

### 🎯 核心特性

- **演化多样性**: 通过TSS模块生成26,507个跨390个领域的多样化API
- **自引导复杂度**: 根据目标LLM的能力动态调整数据复杂度
- **精确验证**: 双层验证系统确保数据的执行性和一致性
- **多类型支持**: 支持单一、并行、依赖和非工具使用等多种函数调用类型

### 📊 性能表现

- 仅使用8B参数的模型即可达到与最新GPT-4模型相当的性能
- 在BFCL和APIBank基准测试中超越现有开源LLM
- 在幻觉检测方面表现优异，相关性和无关性得分分别达到85.37%和83.81%

## 🏗️ 项目架构

```
toolace/
├── README.md                    # 项目主文档
├── requirements.txt             # Python依赖包
├── config/                      # 配置文件目录
│   ├── README.md
│   ├── model_config.yaml        # 模型配置
│   ├── data_config.yaml         # 数据生成配置
│   └── training_config.yaml     # 训练配置
├── toolace/                     # 核心实现目录
│   ├── __init__.py
│   ├── tss/                     # Tool Self-Evolution Synthesis
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── speciation.py        # 物种形成 - API上下文树构建
│   │   ├── adaptation.py        # 适应 - 域和多样性指定
│   │   ├── evolution.py         # 演化 - API持续改进
│   │   └── api_pool.py          # API池管理
│   ├── sdg/                     # Self-Guided Dialog Generation
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── complexity_evaluator.py  # 复杂度评估器
│   │   ├── multi_agent_generator.py # 多代理生成器
│   │   ├── agents/              # 代理实现
│   │   │   ├── __init__.py
│   │   │   ├── user_agent.py    # 用户代理
│   │   │   ├── assistant_agent.py # 助手代理
│   │   │   └── tool_agent.py    # 工具代理
│   │   └── self_guided_complication.py # 自引导复杂化
│   ├── dlv/                     # Dual-Layer Verification
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── rule_checker.py      # 规则检查器
│   │   ├── model_checker.py     # 模型检查器
│   │   └── verification_rules.py # 验证规则定义
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       ├── data_utils.py        # 数据处理工具
│       ├── model_utils.py       # 模型工具
│       └── logger.py            # 日志工具
├── data/                        # 数据目录
│   ├── README.md
│   ├── raw/                     # 原始数据
│   ├── generated/               # 生成的数据
│   │   ├── apis/                # 生成的API定义
│   │   ├── dialogs/             # 生成的对话
│   │   └── verified/            # 验证后的数据
│   └── examples/                # 示例数据
├── scripts/                     # 脚本目录
│   ├── README.md
│   ├── generate_data.py         # 数据生成主脚本
│   ├── train_model.py           # 模型训练脚本
│   └── evaluate.py              # 评估脚本
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_tss.py
│   ├── test_sdg.py
│   └── test_dlv.py
└── docs/                        # 文档目录
    ├── README.md
    ├── api_reference.md         # API参考文档
    ├── tutorial.md              # 使用教程
    └── examples.md              # 使用示例
```

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置设置

1. 复制并修改配置文件：
```bash
cp config/model_config.yaml.example config/model_config.yaml
cp config/data_config.yaml.example config/data_config.yaml
```

2. 在配置文件中设置您的模型API密钥和路径

### 生成数据

```bash
python scripts/generate_data.py --config config/data_config.yaml
```

### 训练模型

```bash
python scripts/train_model.py --config config/training_config.yaml
```

## 📚 核心模块说明

### Tool Self-Evolution Synthesis (TSS)
通过三个步骤生成多样化的API定义：
- **Speciation**: 从预训练数据构建分层API上下文树
- **Adaptation**: 指定每个API的域和多样性级别  
- **Evolution**: 基于结果和新需求持续改进API

### Self-Guided Dialog Generation (SDG)
生成适合目标LLM能力的对话数据：
- **Complexity Evaluator**: 使用目标LLM评估数据复杂度
- **Multi-Agent Generator**: 通过用户、助手、工具三个代理生成对话
- **Self-Guided Complication**: 动态调整对话复杂度

### Dual-Layer Verification (DLV)
确保生成数据的准确性：
- **Rule Checker**: 基于规则验证语法和结构要求
- **Model Checker**: 使用LLM检测幻觉、一致性和工具响应

## 📊 评估基准

- **BFCL**: Berkeley Function Calling Leaderboard
- **APIBank**: API调用评估系统

## 🤝 贡献指南

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📝 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- [原始论文](source/2409.00920v2.pdf)
- [Hugging Face模型](https://huggingface.co/Team-ACE)
- [论文摘要](source/toolace_summary.md)

## 📧 联系方式

如有问题或建议，请提交Issue或联系项目维护者。
