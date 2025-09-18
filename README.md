# ToolACE: Function Calling Training Data Generation Pipeline

[![Paper](https://img.shields.io/badge/Paper-ICLR%202025-blue)](source/2409.00920v2.pdf)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://python.org)

> **ToolACE: Winning the Points of LLM Function Calling**  
> An automated agent pipeline designed to generate accurate, complex, and diverse tool learning data specifically tailored for Large Language Models' capabilities.

## 📖 Project Overview

ToolACE is a systematic tool learning pipeline that automatically synthesizes high-quality function calling data through three core modules:

1. **Tool Self-Evolution Synthesis (TSS)** - Tool evolution and synthesis module
2. **Self-Guided Dialog Generation (SDG)** - Self-guided dialogue generation module
3. **Dual-Layer Verification (DLV)** - Dual-layer verification module

### 🎯 Core Features

- **Evolutionary Diversity**: Generate diverse APIs across multiple domains through the TSS module
- **Self-Guided Complexity**: Dynamically adjust data complexity based on target LLM capabilities
- **Precise Verification**: Dual-layer verification system ensures data executability and consistency
- **Multi-Type Support**: Support for single, parallel, dependent, and non-tool usage function calling types

## 🏗️ Project Structure

```
toolace/
├── config/                      # Configuration directory
│   ├── data_config.yaml        # Data generation config
│   └── README.md
├── data/                       # Data directory
│   ├── examples/               # Example data
│   │   ├── api_examples.json
│   │   └── dialog_examples.json
│   ├── generated/             # Generated data
│   │   ├── apis/
│   │   ├── dialogs/
│   │   └── verified/
│   └── README.md
├── toolace/                    # Core implementation
│   ├── dlv/                   # Dual-Layer Verification
│   │   ├── model_checker.py   # Model verification
│   │   ├── rule_checker.py    # Rule verification
│   │   └── verification_rules.py
│   ├── sdg/                   # Self-Guided Dialog Generation
│   │   ├── agents/           # Agent implementations
│   │   │   ├── assistant_agent.py
│   │   │   ├── tool_agent.py
│   │   │   └── user_agent.py
│   │   └── complexity_evaluator.py
│   ├── tss/                   # Tool Self-Evolution Synthesis
│   │   ├── adaptation.py      # Domain adaptation
│   │   ├── api_pool.py        # API pool management
│   │   ├── evolution.py       # API evolution
│   │   └── speciation.py      # API context tree building
│   └── utils/                 # Utility functions
│       ├── io_utils.py        # I/O utilities
│       ├── logger.py          # Logging utilities
│       └── model_generator/   # Model implementations
└── tests/                     # Test directory
    └── test_simple_model.py
```

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy and modify configuration files:
```bash
cp config/data_config.yaml.example config/data_config.yaml
```

2. Set up your model API keys and paths in the configuration files

### Generate Data

```bash
python scripts/generate_data.py --config config/data_config.yaml
```

## 📚 Core Modules

### Tool Self-Evolution Synthesis (TSS)
Generates diverse API definitions through three steps:
- **Speciation**: Builds hierarchical API context trees from pre-training data
- **Adaptation**: Specifies domain and diversity levels for each API
- **Evolution**: Continuously improves APIs based on results and new requirements

### Self-Guided Dialog Generation (SDG)
Generates dialogue data suitable for target LLM capabilities:
- **Complexity Evaluator**: Evaluates data complexity using target LLM
- **Multi-Agent Generator**: Generates dialogues through user, assistant, and tool agents
- **Self-Guided Complication**: Dynamically adjusts dialogue complexity

### Dual-Layer Verification (DLV)
Ensures generated data accuracy:
- **Rule Checker**: Validates syntax and structural requirements
- **Model Checker**: Detects hallucinations, consistency, and tool responses

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Original Paper](source/2409.00920v2.pdf)
- [Paper Summary](source/toolace_summary.md)

## 📧 Contact

For questions or suggestions, please submit an Issue or contact the project maintainers.