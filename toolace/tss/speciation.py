"""
Speciation Module - API Context Tree Construction

This module implements the speciation step of TSS, which builds a hierarchical
API context tree from pretraining data to guide the synthesis process.
"""

import os
import json
import importlib
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

from ..utils.model_manager import generate


@dataclass
class TreeNode:
    """Represents a node in the API context tree"""
    name: str
    description: str
    children: Dict[str, 'TreeNode']
    parent: Optional['TreeNode'] = None
    level: int = 0
    
    def add_child(self, child: 'TreeNode'):
        """Add a child node"""
        child.parent = self
        child.level = self.level + 1
        self.children[child.name] = child
        
    def get_all_descendants(self) -> List['TreeNode']:
        """Get all descendant nodes"""
        descendants = []
        for child in self.children.values():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


class APIContextTree:
    """
    Builds and manages the hierarchical API context tree that guides
    the API synthesis process across multiple domains and functionalities.
    """
    
    def __init__(self, model_key: str = "tss_model"):
        self.root = TreeNode("root", "API功能根节点", {})
        self.domain_nodes = {}  # domain_name -> TreeNode
        self.functionality_cache = {}  # Cache for extracted functionalities
        self.model_key = model_key  # Model to use for LLM calls
        
    def build_from_pretraining_data(self, data_path: str):
        """
        Build the context tree from pretraining data containing API-related documents
        
        Args:
            data_path: Path to directory containing API-related documents
        """
        print(f"构建API上下文树从预训练数据: {data_path}")
        
        # Extract API domains and functionalities from documents
        api_documents = self._load_api_documents(data_path)
        
        for doc in api_documents:
            domain_info = self._extract_domain_info(doc)
            if domain_info:
                self._add_domain_to_tree(domain_info)
                
        print(f"成功构建包含 {len(self.domain_nodes)} 个领域的API上下文树")
        
    def _load_api_documents(self, data_path: str) -> List[Dict]:
        """Load API-related documents from the data path"""
        documents = []
        
        # This would typically load from various sources:
        # - Technical manuals
        # - API documentation
        # - Product specifications
        # - User guides and tutorials
        
        # For demonstration, we'll create some example domains
        example_domains = [
            {
                "domain": "天气服务",
                "functionalities": [
                    "获取当前天气", "获取天气预报", "获取历史天气", 
                    "天气警报", "气候统计", "空气质量查询"
                ]
            },
            {
                "domain": "金融服务", 
                "functionalities": [
                    "股票价格查询", "汇率转换", "账户余额查询",
                    "交易记录", "投资组合分析", "风险评估"
                ]
            },
            {
                "domain": "娱乐服务",
                "functionalities": [
                    "音乐播放", "视频推荐", "游戏信息",
                    "电影查询", "直播服务", "社交分享"
                ]
            },
            {
                "domain": "交通出行",
                "functionalities": [
                    "路线规划", "实时交通", "公交查询",
                    "打车服务", "停车信息", "航班查询"
                ]
            },
            {
                "domain": "电商购物",
                "functionalities": [
                    "商品搜索", "价格比较", "订单管理",
                    "支付处理", "物流跟踪", "评价系统"
                ]
            }
        ]
        
        return example_domains
        
    def _extract_domain_info(self, document: Dict) -> Optional[Dict]:
        """Extract domain and functionality information from a document using LLM"""
        if "domain" in document and "functionalities" in document:
            return {
                "domain": document["domain"],
                "functionalities": document["functionalities"]
            }
            
        # Use LLM to extract domain info from raw document
        if "content" in document:
            return self._extract_domain_with_llm(document["content"])
            
        return None
        
    def _extract_domain_with_llm(self, document_content: str) -> Optional[Dict]:
        """Use LLM to extract API domain and functionalities from document content"""
        system_prompt = """你是一个API领域分析专家。请从给定的文档内容中提取API相关的领域信息和功能列表。

请按照以下格式返回JSON：
{
    "domain": "领域名称",
    "functionalities": ["功能1", "功能2", "功能3"]
}

要求：
1. 识别文档中涉及的主要API服务领域
2. 提取具体的API功能点，每个功能用简洁的中文描述
3. 如果文档与API无关，返回null
4. 功能列表应该包含3-8个具体功能点"""

        user_prompt = f"""请分析以下文档内容并提取API领域信息：

文档内容：
{document_content[:2000]}  # 限制内容长度

请返回JSON格式的结果。"""

        try:
            response = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=512
            )
            
            # Parse JSON response
            import json
            result = json.loads(response.strip())
            
            if result and "domain" in result and "functionalities" in result:
                return result
            else:
                return None
                
        except Exception as e:
            print(f"LLM提取领域信息失败: {e}")
            return None
        
    def _add_domain_to_tree(self, domain_info: Dict):
        """Add a domain and its functionalities to the context tree"""
        domain_name = domain_info["domain"]
        functionalities = domain_info["functionalities"]
        
        # Create domain node
        domain_node = TreeNode(
            name=domain_name,
            description=f"{domain_name}相关API功能",
            children={}
        )
        
        # Add domain to root
        self.root.add_child(domain_node)
        self.domain_nodes[domain_name] = domain_node
        
        # Add functionalities as children
        for func in functionalities:
            func_node = TreeNode(
                name=func,
                description=f"{func}功能实现",
                children={}
            )
            domain_node.add_child(func_node)
            
            # Add sub-functionalities if needed
            sub_funcs = self._generate_sub_functionalities(func)
            for sub_func in sub_funcs:
                sub_node = TreeNode(
                    name=sub_func,
                    description=f"{sub_func}子功能",
                    children={}
                )
                func_node.add_child(sub_node)
                
    def _generate_sub_functionalities(self, functionality: str) -> List[str]:
        """Generate sub-functionalities for a given functionality"""
        # This could be enhanced with LLM-based generation
        sub_func_mapping = {
            "获取当前天气": ["温度查询", "湿度查询", "风速查询", "降水概率"],
            "股票价格查询": ["实时价格", "历史价格", "价格变动", "市场指标"],
            "音乐播放": ["播放控制", "播放列表", "音质设置", "歌词显示"],
            "路线规划": ["最短路径", "避堵路线", "公交路线", "步行路线"],
            "商品搜索": ["关键词搜索", "分类搜索", "价格筛选", "品牌筛选"]
        }
        
        return sub_func_mapping.get(functionality, [])
        
    def get_subtree(self, domain: str = None, max_depth: int = 3) -> Optional[TreeNode]:
        """
        Get a subtree starting from a specific domain or random sampling
        
        Args:
            domain: Specific domain to get subtree from, None for random
            max_depth: Maximum depth of the subtree
            
        Returns:
            TreeNode representing the subtree root
        """
        if domain and domain in self.domain_nodes:
            return self._extract_subtree(self.domain_nodes[domain], max_depth)
        
        # Random sampling if no specific domain
        import random
        if self.domain_nodes:
            random_domain = random.choice(list(self.domain_nodes.values()))
            return self._extract_subtree(random_domain, max_depth)
            
        return None
        
    def _extract_subtree(self, root_node: TreeNode, max_depth: int) -> TreeNode:
        """Extract a subtree with limited depth"""
        if max_depth <= 0:
            return TreeNode(root_node.name, root_node.description, {})
            
        new_node = TreeNode(root_node.name, root_node.description, {})
        
        for child in root_node.children.values():
            if max_depth > 1:
                new_child = self._extract_subtree(child, max_depth - 1)
                new_node.add_child(new_child)
                
        return new_node
        
    def get_all_functionalities(self) -> List[str]:
        """Get all functionalities from the tree"""
        functionalities = []
        
        def collect_functionalities(node: TreeNode):
            if node.level >= 2:  # Functionality level or below
                functionalities.append(node.name)
            for child in node.children.values():
                collect_functionalities(child)
                
        collect_functionalities(self.root)
        return functionalities
        
    def save_tree(self, filepath: str):
        """Save the context tree to a JSON file"""
        tree_data = self._serialize_node(self.root)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
            
    def load_tree(self, filepath: str):
        """Load the context tree from a JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
        self.root = self._deserialize_node(tree_data)
        self._rebuild_domain_cache()
        
    def _serialize_node(self, node: TreeNode) -> Dict:
        """Serialize a tree node to dictionary"""
        return {
            "name": node.name,
            "description": node.description,
            "level": node.level,
            "children": {name: self._serialize_node(child) 
                        for name, child in node.children.items()}
        }
        
    def _deserialize_node(self, data: Dict, parent: TreeNode = None) -> TreeNode:
        """Deserialize a dictionary to tree node"""
        node = TreeNode(
            name=data["name"],
            description=data["description"],
            children={},
            parent=parent,
            level=data.get("level", 0)
        )
        
        for child_data in data.get("children", {}).values():
            child = self._deserialize_node(child_data, node)
            node.children[child.name] = child
            
        return node
        
    def _rebuild_domain_cache(self):
        """Rebuild the domain nodes cache after loading"""
        self.domain_nodes = {}
        for child in self.root.children.values():
            if child.level == 1:  # Domain level
                self.domain_nodes[child.name] = child
                
    def get_statistics(self) -> Dict:
        """Get statistics about the context tree"""
        total_nodes = len(self.root.get_all_descendants()) + 1
        domain_count = len(self.domain_nodes)
        functionality_count = sum(
            len(domain.children) for domain in self.domain_nodes.values()
        )
        
        return {
            "total_nodes": total_nodes,
            "domain_count": domain_count,
            "functionality_count": functionality_count,
            "max_depth": self._get_max_depth()
        }
        
    def _get_max_depth(self) -> int:
        """Get the maximum depth of the tree"""
        def get_depth(node: TreeNode) -> int:
            if not node.children:
                return node.level
            return max(get_depth(child) for child in node.children.values())
            
        return get_depth(self.root)
