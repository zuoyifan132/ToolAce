"""
API Pool Module - API Collection Management

This module manages the collection and maintenance of the entire API pool,
including storage, retrieval, quality assessment, and statistics collection.
Now simplified to load directly from JSONL files.
"""

import json
import random
from typing import Dict, List, Optional, Any
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent.parent


class APIPool:
    """
    Simplified API pool that loads tools from JSONL file
    """

    def __init__(self, tools_pool_path: str = None):
        if tools_pool_path is None:
            self.tools_pool_path = PROJECT_DIR / "data/generated/apis/tools_pool.jsonl"
        else:
            self.tools_pool_path = Path(tools_pool_path)
        self.apis: List[Dict[str, Any]] = []
        self._load_from_jsonl()

    def _load_from_jsonl(self):
        """Load APIs from JSONL file"""
        try:
            with open(self.tools_pool_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        api_data = json.loads(line)
                        self.apis.append(api_data)
            print(f"✅ 从 {self.tools_pool_path} 加载了 {len(self.apis)} 个工具")
        except FileNotFoundError:
            print(f"❌ 工具池文件未找到: {self.tools_pool_path}")
            self.apis = []
        except Exception as e:
            print(f"❌ 加载工具池文件失败: {e}")
            self.apis = []

    def sample_apis(self,
                   count: int = 5,
                   **kwargs) -> List[Dict[str, Any]]:
        """
        Sample APIs from the pool

        Args:
            count: Number of APIs to sample
            **kwargs: Additional filtering criteria (ignored for simplicity)

        Returns:
            List of sampled API dictionaries
        """
        if not self.apis:
            return []

        # Sample without replacement
        sample_size = min(count, len(self.apis))
        return random.sample(self.apis, sample_size)
 
    def sample_example(self) -> Optional[Dict[str, Any]]:
        """Sample a random API example"""
        if not self.apis:
            return None
        return random.choice(self.apis)

    def add_api(self, api_data: Dict[str, Any]) -> bool:
        """Add an API to the pool (for compatibility)"""
        self.apis.append(api_data)
        return True

    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about the API pool"""
        if not self.apis:
            return {"total_apis": 0}

        # Count different types of tools
        domains = set()
        for api in self.apis:
            # Extract domain from description or name
            name = api.get('name', '').lower()
            desc = api.get('description', '').lower()

            # Simple domain classification
            if any(word in name or word in desc for word in ['weather', 'climate']):
                domains.add('weather')
            elif any(word in name or word in desc for word in ['market', 'stock', 'finance', 'price']):
                domains.add('finance')
            elif any(word in name or word in desc for word in ['crypto', 'ethereum', 'bitcoin']):
                domains.add('crypto')
            elif any(word in name or word in desc for word in ['data', 'api', 'database']):
                domains.add('data')
            else:
                domains.add('general')

        return {
            "total_apis": len(self.apis),
            "estimated_domains": len(domains),
            "domains": list(domains),
            "sample_tools": [api.get('name', 'unknown') for api in self.apis[:5]]
        }

    def export_apis(self, filepath: str):
        """Export APIs to JSON file (for compatibility)"""
        export_data = {
            "apis": self.apis,
            "statistics": self.get_pool_statistics()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def clear_pool(self):
        """Clear all APIs from the pool"""
        self.apis.clear()

    def __len__(self):
        """Return number of APIs in pool"""
        return len(self.apis)

    def reload(self):
        """Reload APIs from JSONL file"""
        self.apis.clear()
        self._load_from_jsonl()