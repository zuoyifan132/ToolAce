#!/usr/bin/env python3
"""
ToolACE 数据生成主脚本

该脚本执行完整的ToolACE数据生成管道，包括:
1. Tool Self-Evolution Synthesis (TSS) - API生成
2. Self-Guided Dialog Generation (SDG) - 对话生成  
3. Dual-Layer Verification (DLV) - 质量验证
"""

import argparse
import os
import sys
import time
import yaml
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from toolace import ToolACE, initialize_global_model_manager
from toolace.utils.logger import setup_logger


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="ToolACE 数据生成管道")
    
    # 基本参数
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/data_config.yaml",
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--api_count",
        type=int,
        default=26507,
        help="目标API生成数量"
    )
    
    parser.add_argument(
        "--dialog_count", 
        type=int,
        default=100000,
        help="目标对话生成数量"
    )
    
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/generated/",
        help="输出目录路径"
    )
    
    # 模式控制
    parser.add_argument(
        "--tss_only",
        action="store_true",
        help="仅运行TSS模块"
    )
    
    parser.add_argument(
        "--sdg_only", 
        action="store_true",
        help="仅运行SDG模块"
    )
    
    parser.add_argument(
        "--dlv_only",
        action="store_true", 
        help="仅运行DLV模块"
    )
    
    parser.add_argument(
        "--verify_only",
        action="store_true",
        help="仅验证已生成的数据"
    )
    
    # 调试参数
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出模式"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="调试模式"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子"
    )
    
    # 性能参数
    parser.add_argument(
        "--num_workers",
        type=int,
        default=4,
        help="并行工作进程数"
    )
    
    parser.add_argument(
        "--batch_size",
        type=int, 
        default=32,
        help="批处理大小"
    )
    
    # 恢复参数
    parser.add_argument(
        "--resume_from",
        type=str,
        help="从检查点恢复生成"
    )
    
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ 配置文件未找到: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)


def setup_environment(args, config):
    """设置运行环境"""
    # 设置随机种子
    import random
    import numpy as np
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 设置日志
    log_level = "DEBUG" if args.debug else ("INFO" if args.verbose else "WARNING")
    logger = setup_logger("toolace_generation", log_level)
    
    return logger


def run_tss_only(toolace, args, logger):
    """仅运行TSS模块"""
    logger.info("🔧 运行TSS模块 (工具自演化合成)")
    
    start_time = time.time()
    api_pool = toolace.tss.run_synthesis(
        pretraining_data_path=toolace.config.get("tss", {}).get("pretraining_data_path"),
        target_api_count=args.api_count
    )
    
    # 保存API池
    api_output_path = os.path.join(args.output_dir, "apis")
    os.makedirs(api_output_path, exist_ok=True)
    api_pool.export_apis(f"{api_output_path}/api_pool.json")
    
    elapsed = time.time() - start_time
    logger.info(f"✅ TSS完成! 生成 {len(api_pool.apis)} 个API，用时 {elapsed:.2f}秒")
    
    # 输出统计信息
    stats = api_pool.get_pool_statistics()
    logger.info(f"📊 API池统计: {stats}")
    
    return {"api_count": len(api_pool.apis), "api_stats": stats}


def run_sdg_only(toolace, args, logger):
    """仅运行SDG模块"""
    logger.info("💬 运行SDG模块 (自引导对话生成)")
    
    # 需要先加载API池
    api_pool_path = os.path.join(args.output_dir, "apis/api_pool.json")
    if not os.path.exists(api_pool_path):
        logger.error("❌ 未找到API池文件，请先运行TSS模块")
        return None
        
    # 加载API池 (这里简化处理，实际需要实现加载逻辑)
    logger.info(f"📥 从 {api_pool_path} 加载API池")
    
    start_time = time.time()
    dialogs = toolace.sdg.batch_generate_dialogs(
        api_pool=toolace.tss.api_pool,  # 实际应该从文件加载
        count=args.dialog_count
    )
    
    # 保存对话
    dialog_output_path = os.path.join(args.output_dir, "dialogs")
    os.makedirs(dialog_output_path, exist_ok=True)
    
    import json
    with open(f"{dialog_output_path}/dialogs.json", 'w', encoding='utf-8') as f:
        json.dump(dialogs, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    logger.info(f"✅ SDG完成! 生成 {len(dialogs)} 个对话，用时 {elapsed:.2f}秒")
    
    return {"dialog_count": len(dialogs)}


def run_dlv_only(toolace, args, logger):
    """仅运行DLV模块"""
    logger.info("🔍 运行DLV模块 (双层验证)")
    
    # 需要先加载对话数据
    dialog_path = os.path.join(args.output_dir, "dialogs/dialogs.json")
    if not os.path.exists(dialog_path):
        logger.error("❌ 未找到对话文件，请先运行SDG模块")
        return None
        
    # 加载对话数据
    import json
    logger.info(f"📥 从 {dialog_path} 加载对话数据")
    with open(dialog_path, 'r', encoding='utf-8') as f:
        dialogs = json.load(f)
        
    start_time = time.time()
    verification_results = toolace.dlv.batch_verify(dialogs)
    
    # 筛选验证通过的对话
    valid_dialogs = [
        dialog for dialog, result in zip(dialogs, verification_results)
        if result["final_decision"] == "passed"
    ]
    
    # 保存验证通过的数据
    verified_output_path = os.path.join(args.output_dir, "verified")
    os.makedirs(verified_output_path, exist_ok=True)
    
    with open(f"{verified_output_path}/verified_dialogs.json", 'w', encoding='utf-8') as f:
        json.dump(valid_dialogs, f, ensure_ascii=False, indent=2)
        
    # 保存验证报告
    with open(f"{verified_output_path}/verification_report.json", 'w', encoding='utf-8') as f:
        json.dump(verification_results, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    pass_rate = len(valid_dialogs) / len(dialogs) if dialogs else 0
    logger.info(f"✅ DLV完成! 验证通过 {len(valid_dialogs)}/{len(dialogs)} 个对话 ({pass_rate:.2%})，用时 {elapsed:.2f}秒")
    
    # 统计信息
    stats = toolace.dlv.get_verification_statistics(verification_results)
    logger.info(f"📊 验证统计: {stats}")
    
    return {
        "total_dialogs": len(dialogs),
        "valid_dialogs": len(valid_dialogs), 
        "pass_rate": pass_rate,
        "verification_stats": stats
    }


def run_full_pipeline(toolace, args, logger):
    """运行完整的ToolACE管道"""
    logger.info("🚀 开始完整的ToolACE数据生成管道")
    
    total_start_time = time.time()
    
    try:
        # 运行完整管道
        stats = toolace.generate_dataset(
            target_api_count=args.api_count,
            target_dialog_count=args.dialog_count
        )
        
        total_elapsed = time.time() - total_start_time
        
        logger.info("🎉 ToolACE管道执行完成!")
        logger.info(f"⏱️  总用时: {total_elapsed:.2f}秒")
        logger.info(f"📊 最终统计: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ 管道执行失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return None


def main():
    """主函数"""
    args = parse_arguments()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置环境
    logger = setup_environment(args, config)
    
    logger.info("🔧 初始化ToolACE")
    logger.info(f"📋 配置文件: {args.config}")
    logger.info(f"🎯 目标API数量: {args.api_count}")
    logger.info(f"🎯 目标对话数量: {args.dialog_count}")
    logger.info(f"📁 输出目录: {args.output_dir}")
    
    # 初始化ToolACE
    try:
        # Initialize model manager first
        initialize_global_model_manager(args.config)
        logger.info("✅ 全局模型管理器初始化成功")
        
        toolace = ToolACE(config_path=args.config)
    except Exception as e:
        logger.error(f"❌ ToolACE初始化失败: {e}")
        sys.exit(1)
    
    # 根据参数运行相应模块
    results = None
    
    if args.tss_only:
        results = run_tss_only(toolace, args, logger)
    elif args.sdg_only:
        results = run_sdg_only(toolace, args, logger)
    elif args.dlv_only or args.verify_only:
        results = run_dlv_only(toolace, args, logger)
    else:
        results = run_full_pipeline(toolace, args, logger)
    
    # 保存最终结果
    if results:
        results_path = os.path.join(args.output_dir, "generation_results.json")
        import json
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 结果已保存到: {results_path}")
    
    logger.info("🏁 程序执行完成")


if __name__ == "__main__":
    main()
