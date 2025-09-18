# 脚本目录

本目录包含ToolACE项目的主要执行脚本，用于数据生成、模型训练和性能评估。

## 📁 脚本说明

### `generate_data.py`
主要的数据生成脚本，执行完整的ToolACE管道：
- 运行TSS模块生成API池
- 运行SDG模块生成对话数据  
- 运行DLV模块验证数据质量

**使用方法**:
```bash
python scripts/generate_data.py --config config/data_config.yaml --api_count 26507 --dialog_count 100000
```

### `train_model.py`
模型训练脚本，使用生成的数据训练LLM：
- 支持LoRA参数高效训练
- 支持多GPU分布式训练
- 集成实验跟踪和检查点保存

**使用方法**:
```bash
python scripts/train_model.py --config config/training_config.yaml --data_path data/generated/verified/
```

### `evaluate.py`
模型评估脚本，在标准基准上测试模型性能：
- BFCL基准测试
- APIBank基准测试
- 自定义评估指标

**使用方法**:
```bash
python scripts/evaluate.py --model_path models/toolace-8b --benchmark BFCL
```

## 🔧 脚本参数

### 通用参数
- `--config`: 配置文件路径
- `--output_dir`: 输出目录路径
- `--seed`: 随机种子
- `--verbose`: 详细输出模式

### 数据生成参数
- `--api_count`: 目标API数量
- `--dialog_count`: 目标对话数量
- `--verify_only`: 仅运行验证模块
- `--resume_from`: 从检查点恢复生成

### 训练参数  
- `--model_name`: 基础模型名称
- `--epochs`: 训练轮数
- `--batch_size`: 批次大小
- `--learning_rate`: 学习率
- `--lora_rank`: LoRA rank参数

### 评估参数
- `--model_path`: 待评估模型路径
- `--benchmark`: 评估基准名称
- `--output_format`: 结果输出格式

## 🚀 快速开始

### 1. 生成数据
```bash
# 使用默认配置生成完整数据集
python scripts/generate_data.py

# 生成小规模测试数据
python scripts/generate_data.py --api_count 1000 --dialog_count 5000
```

### 2. 训练模型
```bash
# 使用生成的数据训练模型
python scripts/train_model.py --model_name llama3.1-8b

# 继续训练已有模型
python scripts/train_model.py --resume_from checkpoints/epoch_5/
```

### 3. 评估性能
```bash
# 在BFCL基准上评估
python scripts/evaluate.py --model_path models/toolace-8b --benchmark BFCL

# 在APIBank基准上评估
python scripts/evaluate.py --model_path models/toolace-8b --benchmark APIBank
```

## 📊 输出说明

### 数据生成输出
- `data/generated/apis/`: 生成的API定义
- `data/generated/dialogs/`: 生成的原始对话
- `data/generated/verified/`: 验证通过的最终数据
- `logs/generation.log`: 生成过程日志

### 训练输出
- `models/toolace-8b/`: 训练好的模型
- `checkpoints/`: 训练检查点
- `logs/training.log`: 训练日志
- `tensorboard/`: TensorBoard日志

### 评估输出
- `results/evaluation/`: 评估结果文件
- `logs/evaluation.log`: 评估日志
- `metrics/`: 详细性能指标

## 🔍 监控和调试

### 日志查看
```bash
# 查看实时生成日志
tail -f logs/generation.log

# 查看训练进度
tail -f logs/training.log
```

### 进度监控
```bash
# 检查数据生成进度
python scripts/check_progress.py --task generation

# 检查训练进度  
python scripts/check_progress.py --task training
```

### 错误调试
```bash
# 详细错误输出
python scripts/generate_data.py --verbose --debug

# 单步调试模式
python scripts/generate_data.py --step_by_step
```

## ⚙️ 高级用法

### 分布式数据生成
```bash
# 多进程并行生成
python scripts/generate_data.py --num_workers 8

# 集群分布式生成
python scripts/distributed_generate.py --nodes 4
```

### 实验管理
```bash
# 运行消融实验
python scripts/ablation_study.py --config config/ablation_config.yaml

# A/B测试对比
python scripts/ab_test.py --config_a config_v1.yaml --config_b config_v2.yaml
```

### 数据质量分析
```bash
# 分析生成数据质量
python scripts/analyze_data_quality.py --data_path data/generated/verified/

# 生成质量报告
python scripts/generate_quality_report.py --output reports/quality_report.html
```
