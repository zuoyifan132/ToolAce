#!/usr/bin/env python3
"""
ToolACE Data Generation Main Script

This script executes the complete ToolACE data generation pipeline, including:
1. Tool Self-Evolution Synthesis (TSS) - API Generation
2. Self-Guided Dialog Generation (SDG) - Dialog Generation
3. Dual-Layer Verification (DLV) - Quality Verification
"""

import argparse
import os
import sys
import dotenv
import time
import yaml
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from toolace import ToolACE
from toolace.utils.logger import setup_logger


dotenv.load_dotenv("../.env")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="ToolACE Data Generation Pipeline")
    
    # Basic parameters
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/data_config.yaml",
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--api_count",
        type=int,
        default=26507,
        help="Target number of APIs to generate"
    )
    
    parser.add_argument(
        "--dialog_count", 
        type=int,
        default=100000,
        help="Target number of dialogs to generate"
    )
    
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/generated/",
        help="Output directory path"
    )
    
    # Mode control
    parser.add_argument(
        "--tss_only",
        action="store_true",
        help="Run TSS module only"
    )
    
    parser.add_argument(
        "--sdg_only", 
        action="store_true",
        help="Run SDG module only"
    )
    
    parser.add_argument(
        "--dlv_only",
        action="store_true", 
        help="Run DLV module only"
    )
    
    parser.add_argument(
        "--verify_only",
        action="store_true",
        help="Only verify generated data"
    )
    
    # Debug parameters
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output mode"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="Debug mode"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    
    # Performance parameters
    parser.add_argument(
        "--num_workers",
        type=int,
        default=4,
        help="Number of parallel worker processes"
    )
    
    parser.add_argument(
        "--batch_size",
        type=int, 
        default=32,
        help="Batch size"
    )
    
    # Recovery parameters
    parser.add_argument(
        "--resume_from",
        type=str,
        help="Resume generation from checkpoint"
    )
    
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """Load configuration file"""
    try:
        print(Path(project_root / config_path))
        with open(Path(project_root / config_path), 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Configuration file format error: {e}")
        sys.exit(1)


def setup_environment(args, config):
    """Setup running environment"""
    # Set random seed
    import random
    import numpy as np
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Create output directories
    try:
        os.makedirs(Path(args.output_dir).parent, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    except Exception as e:
        print(f"❌ Failed to create output directories: {e}")
        sys.exit(1)
    
    # Setup logging
    log_level = "DEBUG" if args.debug else ("INFO" if args.verbose else "WARNING")
    logger = setup_logger("toolace_generation", log_level)
    
    return logger


def run_tss_only(toolace, args, logger):
    """Run TSS module only"""
    logger.info("🔧 Running TSS module (Tool Self-Evolution Synthesis)")
    
    start_time = time.time()
    api_pool = toolace.tss.run_synthesis(
        pretraining_data_path=toolace.config.get("tss", {}).get("pretraining_data_path"),
        target_api_count=args.api_count
    )
    
    # Save API pool
    api_output_path = os.path.join(args.output_dir, "apis")
    os.makedirs(api_output_path, exist_ok=True)
    api_pool.export_apis(f"{api_output_path}/api_pool.json")
    
    elapsed = time.time() - start_time
    logger.info(f"✅ TSS completed! Generated {len(api_pool.apis)} APIs in {elapsed:.2f} seconds")
    
    # Output statistics
    stats = api_pool.get_pool_statistics()
    logger.info(f"📊 API pool statistics: {stats}")
    
    return {"api_count": len(api_pool.apis), "api_stats": stats}


def run_sdg_only(toolace, args, logger):
    """Run SDG module only"""
    logger.info("💬 Running SDG module (Self-Guided Dialog Generation)")
    
    # Need to load API pool first
    api_pool_path = os.path.join(project_root, "data/generated/apis/tools_pool.jsonl")
    if not os.path.exists(api_pool_path):
        logger.error("❌ API pool file not found, please run TSS module first")
        return None
        
    # Load API pool (simplified here, actual loading logic needs to be implemented)
    logger.info(f"📥 Loading API pool from {api_pool_path}")
    
    dialogs = toolace.sdg.batch_generate_dialogs(
        api_pool=toolace.tss.api_pool,  # Should actually load from file
        count=args.dialog_count,
        save_path=args.output_dir
    )

def run_dlv_only(toolace, args, logger):
    """Run DLV module only"""
    logger.info("🔍 Running DLV module (Dual-Layer Verification)")
    
    # Need to load dialog data first
    dialog_path = os.path.join(args.output_dir, "dialogs/dialogs.json")
    if not os.path.exists(dialog_path):
        logger.error("❌ Dialog file not found, please run SDG module first")
        return None
        
    # Load dialog data
    import json
    logger.info(f"📥 Loading dialog data from {dialog_path}")
    with open(dialog_path, 'r', encoding='utf-8') as f:
        dialogs = json.load(f)
        
    start_time = time.time()
    verification_results = toolace.dlv.batch_verify(dialogs)
    
    # Filter verified dialogs
    valid_dialogs = [
        dialog for dialog, result in zip(dialogs, verification_results)
        if result["final_decision"] == "passed"
    ]
    
    # Save verified data
    verified_output_path = os.path.join(args.output_dir, "verified")
    os.makedirs(verified_output_path, exist_ok=True)
    
    with open(f"{verified_output_path}/verified_dialogs.json", 'w', encoding='utf-8') as f:
        json.dump(valid_dialogs, f, ensure_ascii=False, indent=2)
        
    # Save verification report
    with open(f"{verified_output_path}/verification_report.json", 'w', encoding='utf-8') as f:
        json.dump(verification_results, f, ensure_ascii=False, indent=2)
        
    elapsed = time.time() - start_time
    pass_rate = len(valid_dialogs) / len(dialogs) if dialogs else 0
    logger.info(f"✅ DLV completed! Verified {len(valid_dialogs)}/{len(dialogs)} dialogs ({pass_rate:.2%}) in {elapsed:.2f} seconds")
    
    # Statistics
    stats = toolace.dlv.get_verification_statistics(verification_results)
    logger.info(f"📊 Verification statistics: {stats}")
    
    return {
        "total_dialogs": len(dialogs),
        "valid_dialogs": len(valid_dialogs), 
        "pass_rate": pass_rate,
        "verification_stats": stats
    }


def run_full_pipeline(toolace, args, logger):
    """Run complete ToolACE pipeline"""
    logger.info("🚀 Starting complete ToolACE data generation pipeline")
    
    total_start_time = time.time()
    
    try:
        # Run complete pipeline
        stats = toolace.generate_dataset(
            target_api_count=args.api_count,
            target_dialog_count=args.dialog_count
        )
        
        total_elapsed = time.time() - total_start_time
        
        logger.info("🎉 ToolACE pipeline execution completed!")
        logger.info(f"⏱️  Total time: {total_elapsed:.2f} seconds")
        logger.info(f"📊 Final statistics: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return None


def main():
    """Main function"""
    args = parse_arguments()
    
    # Load configuration
    config_path = Path(project_root / args.config)
    config = load_config(config_path)
    
    # Setup environment
    logger = setup_environment(args, args.config)
    
    logger.info("🔧 Initializing ToolACE")
    logger.info(f"📋 Config file: {args.config}")
    logger.info(f"🎯 Target API count: {args.api_count}")
    logger.info(f"🎯 Target dialog count: {args.dialog_count}")
    logger.info(f"📁 Output directory: {args.output_dir}")
    
    # Initialize ToolACE
    try:
        # Initialize ToolACE
        toolace = ToolACE(config_path=config_path)
    except Exception as e:
        logger.error(f"❌ ToolACE initialization failed: {e}")
        sys.exit(1)
    
    # Run corresponding module based on parameters
    results = None
    
    if args.tss_only:
        results = run_tss_only(toolace, args, logger)
    elif args.sdg_only:
        results = run_sdg_only(toolace, args, logger)
    elif args.dlv_only or args.verify_only:
        results = run_dlv_only(toolace, args, logger)
    else:
        results = run_full_pipeline(toolace, args, logger)
    
    # Save final results
    if results:
        results_path = os.path.join(args.output_dir, "generation_results.json")
        import json
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 Results saved to: {results_path}")
    
    logger.info("🏁 Program execution completed")


if __name__ == "__main__":
    main()
