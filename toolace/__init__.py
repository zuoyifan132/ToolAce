"""
ToolACE: Automated Agentic Pipeline for Tool Learning Data Generation

This package implements the ToolACE framework for generating accurate, complex,
and diverse tool-learning data specifically tailored to LLM capabilities.
"""

from .tss import TSS
from .sdg import SDG  
from .dlv import DLV

__version__ = "1.0.0"
__author__ = "ToolACE Team"

__all__ = [
    'TSS',
    'SDG', 
    'DLV',
    'ToolACE',
]

class ToolACE:
    """
    Main ToolACE class that orchestrates the complete data generation pipeline:
    1. Tool Self-Evolution Synthesis (TSS)
    2. Self-Guided Dialog Generation (SDG) 
    3. Dual-Layer Verification (DLV)
    """
    
    def __init__(self, config_path: str = None):
        """Initialize ToolACE with configuration"""
        self.config_path = config_path
        self.config = self._load_config(config_path) if config_path else {}
        
        # Initialize modules
        self.tss = TSS(config_path)
        self.sdg = SDG(config=self.config.get("sdg", {}))
        self.dlv = DLV(config=self.config.get("dlv", {}))
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        import yaml
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return {}
            
    def generate_dataset(self, 
                        target_api_count: int = 26507,
                        target_dialog_count: int = 100000) -> dict:
        """
        Generate complete dataset through the full ToolACE pipeline
        
        Args:
            target_api_count: Number of APIs to generate
            target_dialog_count: Number of dialogs to generate
            
        Returns:
            Dictionary with generated data statistics
        """
        print("🚀 开始ToolACE数据生成管道...")
        
        # Step 1: Tool Self-Evolution Synthesis
        print("📊 步骤1: 工具自演化合成 (TSS)")
        api_pool = self.tss.run_synthesis(
            pretraining_data_path=self.config.get("tss", {}).get("pretraining_data_path"),
            target_api_count=target_api_count
        )
        print(f"✅ 生成了 {len(api_pool.apis)} 个API")
        
        # Step 2: Self-Guided Dialog Generation  
        print("💬 步骤2: 自引导对话生成 (SDG)")
        dialogs = self.sdg.batch_generate_dialogs(
            api_pool=api_pool,
            count=target_dialog_count
        )
        print(f"✅ 生成了 {len(dialogs)} 个对话")
        
        # Step 3: Dual-Layer Verification
        print("🔍 步骤3: 双层验证 (DLV)")
        verification_results = self.dlv.batch_verify(dialogs)
        valid_dialogs = [
            dialog for dialog, result in zip(dialogs, verification_results)
            if result["final_decision"] == "passed"
        ]
        print(f"✅ 验证通过 {len(valid_dialogs)} 个对话")
        
        # Generate statistics
        stats = {
            "api_count": len(api_pool.apis),
            "total_dialogs": len(dialogs),
            "valid_dialogs": len(valid_dialogs),
            "verification_pass_rate": len(valid_dialogs) / len(dialogs) if dialogs else 0,
            "api_pool_stats": api_pool.get_pool_statistics(),
            "verification_stats": self.dlv.get_verification_statistics(verification_results)
        }
        
        # Save results
        self._save_results(api_pool, valid_dialogs, stats)
        
        print("🎉 ToolACE数据生成完成!")
        return stats
        
    def _save_results(self, api_pool, dialogs: list, stats: dict):
        """Save generated results to files"""
        import json
        import os
        
        # Create output directories
        output_paths = self.config.get("general", {}).get("output_paths", {})
        
        # Save API pool
        api_path = output_paths.get("generated_apis", "data/generated/apis/")
        os.makedirs(api_path, exist_ok=True)
        api_pool.export_apis(f"{api_path}/api_pool.json")
        
        # Save dialogs
        dialog_path = output_paths.get("verified_data", "data/generated/verified/")
        os.makedirs(dialog_path, exist_ok=True)
        with open(f"{dialog_path}/dialogs.json", 'w', encoding='utf-8') as f:
            json.dump(dialogs, f, ensure_ascii=False, indent=2)
            
        # Save statistics
        with open(f"{dialog_path}/statistics.json", 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
            
        print(f"📁 结果已保存到: {dialog_path}")
