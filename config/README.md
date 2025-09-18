# 配置文件目录

本目录包含ToolACE项目的所有配置文件，用于控制数据生成、模型训练和验证过程的各项参数。

## 📁 文件说明

- `model_config.yaml` - 模型相关配置（路径、参数等）
- `data_config.yaml` - 数据生成配置（TSS、SDG、DLV参数）
- `training_config.yaml` - 训练配置（LoRA参数、超参数等）

## 🔧 配置文件使用

### 1. 复制示例配置
```bash
cp config/model_config.yaml.example config/model_config.yaml
cp config/data_config.yaml.example config/data_config.yaml
cp config/training_config.yaml.example config/training_config.yaml
```

### 2. 修改配置参数
根据您的环境和需求修改配置文件中的参数。

### 3. 在代码中使用
```python
import yaml

with open("config/data_config.yaml", "r") as f:
    config = yaml.safe_load(f)
```

## ⚙️ 配置参数说明

### 模型配置
- 目标LLM路径和参数
- API密钥和访问配置
- 推理配置（温度、最大长度等）

### 数据生成配置
- TSS模块：API池大小、多样性级别
- SDG模块：复杂度范围、对话类型
- DLV模块：验证阈值、检查规则

### 训练配置
- LoRA参数：rank、alpha、dropout
- 训练超参数：学习率、批次大小、训练轮数
- 优化器和调度器配置
