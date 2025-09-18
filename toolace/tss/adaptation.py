"""
Adaptation Module - Domain and Diversity Level Specification

This module implements the adaptation step of TSS, which specifies the domain
and diversity level for each API by sampling subtrees from the context tree.
"""

import random
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .speciation import APIContextTree, TreeNode


class DiversityLevel(Enum):
    """Enumeration for API diversity levels"""
    LOW = "low"          # Simple, single-function APIs
    MEDIUM = "medium"    # Moderate complexity with related functions
    HIGH = "high"        # Complex APIs with multiple domains


@dataclass
class APISpec:
    """Specification for an API including domain and diversity info"""
    name: str
    domain: str
    functionalities: List[str]
    diversity_level: DiversityLevel
    complexity_score: float
    subtree: TreeNode


class DomainAdapter:
    """
    Handles the adaptation step of TSS by sampling subtrees and specifying
    domain and diversity levels for each individual API.
    """
    
    def __init__(self, context_tree: APIContextTree):
        self.context_tree = context_tree
        self.used_functionality_combinations = set()
        
    def sample_subtree(self, 
                      diversity_level: Optional[DiversityLevel] = None,
                      target_domain: Optional[str] = None) -> APISpec:
        """
        Sample a subtree from the context tree and create API specification
        
        Args:
            diversity_level: Target diversity level, random if None
            target_domain: Target domain, random if None
            
        Returns:
            APISpec with sampled subtree and specifications
        """
        # Determine diversity level
        if diversity_level is None:
            diversity_level = random.choice(list(DiversityLevel))
            
        # Sample based on diversity level
        if diversity_level == DiversityLevel.LOW:
            return self._sample_low_diversity(target_domain)
        elif diversity_level == DiversityLevel.MEDIUM:
            return self._sample_medium_diversity(target_domain)
        else:  # HIGH
            return self._sample_high_diversity(target_domain)
            
    def _sample_low_diversity(self, target_domain: Optional[str]) -> APISpec:
        """Sample for low diversity - single functionality focus"""
        # Select a single domain
        domain = self._select_domain(target_domain)
        domain_node = self.context_tree.domain_nodes[domain]
        
        # Select a single functionality
        if domain_node.children:
            func_name = random.choice(list(domain_node.children.keys()))
            func_node = domain_node.children[func_name]
            
            # Create minimal subtree with just this functionality
            subtree = TreeNode(domain, f"{domain}领域", {})
            func_copy = TreeNode(func_name, func_node.description, {})
            subtree.add_child(func_copy)
            
            return APISpec(
                name=f"{func_name}_api",
                domain=domain,
                functionalities=[func_name],
                diversity_level=DiversityLevel.LOW,
                complexity_score=self._calculate_complexity_score([func_name]),
                subtree=subtree
            )
        
        # Fallback if no functionalities
        return self._create_fallback_spec(domain, DiversityLevel.LOW)
        
    def _sample_medium_diversity(self, target_domain: Optional[str]) -> APISpec:
        """Sample for medium diversity - multiple related functionalities"""
        # Select a domain
        domain = self._select_domain(target_domain)
        domain_node = self.context_tree.domain_nodes[domain]
        
        # Select 2-4 related functionalities
        available_funcs = list(domain_node.children.keys())
        num_funcs = min(random.randint(2, 4), len(available_funcs))
        selected_funcs = random.sample(available_funcs, num_funcs)
        
        # Create subtree with selected functionalities
        subtree = TreeNode(domain, f"{domain}领域", {})
        for func_name in selected_funcs:
            func_node = domain_node.children[func_name]
            func_copy = TreeNode(func_name, func_node.description, {})
            
            # Include some sub-functionalities for complexity
            sub_funcs = list(func_node.children.keys())
            if sub_funcs:
                num_sub = min(random.randint(1, 3), len(sub_funcs))
                for sub_func in random.sample(sub_funcs, num_sub):
                    sub_node = func_node.children[sub_func]
                    sub_copy = TreeNode(sub_func, sub_node.description, {})
                    func_copy.add_child(sub_copy)
                    
            subtree.add_child(func_copy)
            
        return APISpec(
            name=f"{domain}_综合_api",
            domain=domain,
            functionalities=selected_funcs,
            diversity_level=DiversityLevel.MEDIUM,
            complexity_score=self._calculate_complexity_score(selected_funcs),
            subtree=subtree
        )
        
    def _sample_high_diversity(self, target_domain: Optional[str]) -> APISpec:
        """Sample for high diversity - cross-domain functionalities"""
        # Select multiple domains
        available_domains = list(self.context_tree.domain_nodes.keys())
        num_domains = min(random.randint(2, 3), len(available_domains))
        
        if target_domain and target_domain in available_domains:
            selected_domains = [target_domain]
            other_domains = [d for d in available_domains if d != target_domain]
            selected_domains.extend(random.sample(other_domains, num_domains - 1))
        else:
            selected_domains = random.sample(available_domains, num_domains)
            
        # Create cross-domain subtree
        main_domain = selected_domains[0]
        subtree = TreeNode(f"跨域_{main_domain}", "跨领域综合API", {})
        all_functionalities = []
        
        for domain in selected_domains:
            domain_node = self.context_tree.domain_nodes[domain]
            # Select 1-2 functionalities from each domain
            available_funcs = list(domain_node.children.keys())
            if available_funcs:
                num_funcs = min(random.randint(1, 2), len(available_funcs))
                selected_funcs = random.sample(available_funcs, num_funcs)
                all_functionalities.extend(selected_funcs)
                
                for func_name in selected_funcs:
                    func_node = domain_node.children[func_name]
                    func_copy = TreeNode(
                        f"{domain}_{func_name}", 
                        f"{domain}领域的{func_node.description}", 
                        {}
                    )
                    subtree.add_child(func_copy)
                    
        return APISpec(
            name=f"跨域_{main_domain}_api",
            domain=main_domain,
            functionalities=all_functionalities,
            diversity_level=DiversityLevel.HIGH,
            complexity_score=self._calculate_complexity_score(all_functionalities),
            subtree=subtree
        )
        
    def _select_domain(self, target_domain: Optional[str]) -> str:
        """Select a domain, either specified or random"""
        if target_domain and target_domain in self.context_tree.domain_nodes:
            return target_domain
        
        available_domains = list(self.context_tree.domain_nodes.keys())
        return random.choice(available_domains) if available_domains else "默认领域"
        
    def _calculate_complexity_score(self, functionalities: List[str]) -> float:
        """Calculate complexity score based on number and type of functionalities"""
        base_score = len(functionalities) * 0.3
        
        # Add complexity based on functionality types
        complex_keywords = ["查询", "分析", "处理", "管理", "统计"]
        complexity_bonus = sum(
            0.2 for func in functionalities 
            for keyword in complex_keywords 
            if keyword in func
        )
        
        return min(base_score + complexity_bonus, 1.0)
        
    def _create_fallback_spec(self, domain: str, diversity_level: DiversityLevel) -> APISpec:
        """Create a fallback API spec when sampling fails"""
        return APISpec(
            name=f"{domain}_默认_api",
            domain=domain,
            functionalities=[f"{domain}基本功能"],
            diversity_level=diversity_level,
            complexity_score=0.5,
            subtree=TreeNode(domain, f"{domain}默认功能", {})
        )
        
    def ensure_unique_functionality_combination(self, spec: APISpec) -> APISpec:
        """
        Ensure the functionality combination is unique by modifying if necessary
        
        Args:
            spec: Original API specification
            
        Returns:
            Modified spec with unique functionality combination
        """
        func_key = tuple(sorted(spec.functionalities))
        
        if func_key in self.used_functionality_combinations:
            # Modify the specification to make it unique
            spec = self._modify_for_uniqueness(spec)
            func_key = tuple(sorted(spec.functionalities))
            
        self.used_functionality_combinations.add(func_key)
        return spec
        
    def _modify_for_uniqueness(self, spec: APISpec) -> APISpec:
        """Modify API spec to ensure uniqueness"""
        # Add a suffix or modify functionalities
        modified_funcs = [f"{func}_变体" for func in spec.functionalities]
        
        return APISpec(
            name=f"{spec.name}_变体",
            domain=spec.domain,
            functionalities=modified_funcs,
            diversity_level=spec.diversity_level,
            complexity_score=spec.complexity_score,
            subtree=spec.subtree
        )
        
    def get_adaptation_statistics(self) -> Dict:
        """Get statistics about the adaptation process"""
        diversity_counts = {level.value: 0 for level in DiversityLevel}
        domain_counts = {}
        
        # This would track actual sampling statistics in a real implementation
        return {
            "unique_combinations": len(self.used_functionality_combinations),
            "diversity_distribution": diversity_counts,
            "domain_distribution": domain_counts
        }
        
    def reset_adaptation_state(self):
        """Reset the adaptation state for a new synthesis run"""
        self.used_functionality_combinations.clear()
        
    def batch_sample_subtrees(self, 
                             count: int,
                             diversity_distribution: Optional[Dict[DiversityLevel, float]] = None) -> List[APISpec]:
        """
        Sample multiple subtrees in batch with specified diversity distribution
        
        Args:
            count: Number of subtrees to sample
            diversity_distribution: Distribution of diversity levels
            
        Returns:
            List of APISpec objects
        """
        if diversity_distribution is None:
            # Default equal distribution
            diversity_distribution = {
                DiversityLevel.LOW: 0.4,
                DiversityLevel.MEDIUM: 0.4,
                DiversityLevel.HIGH: 0.2
            }
            
        specs = []
        for _ in range(count):
            # Select diversity level based on distribution
            diversity_level = self._weighted_choice_diversity(diversity_distribution)
            spec = self.sample_subtree(diversity_level=diversity_level)
            spec = self.ensure_unique_functionality_combination(spec)
            specs.append(spec)
            
        return specs
        
    def _weighted_choice_diversity(self, distribution: Dict[DiversityLevel, float]) -> DiversityLevel:
        """Make a weighted random choice of diversity level"""
        choices = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(choices, weights=weights)[0]
