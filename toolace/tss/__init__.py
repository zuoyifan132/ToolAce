"""
Tool Self-Evolution Synthesis (TSS) Module

This module implements the Tool Self-Evolution Synthesis process for generating
diverse and high-quality API definitions through speciation, adaptation, and evolution.
"""

from .speciation import APIContextTree
from .adaptation import DomainAdapter
from .evolution import APIEvolver
from .api_pool import APIPool

__all__ = [
    'APIContextTree',
    'DomainAdapter', 
    'APIEvolver',
    'APIPool',
    'TSS'
]

class TSS:
    """
    Tool Self-Evolution Synthesis main class that orchestrates the three-step process:
    1. Speciation: Build hierarchical API context tree
    2. Adaptation: Specify domain and diversity levels
    3. Evolution: Continuous improvement and generation
    """
    
    def __init__(self, config_path: str = None):
        """Initialize TSS with configuration"""
        self.config_path = config_path
        self.context_tree = None
        self.domain_adapter = None
        self.api_evolver = None
        self.api_pool = APIPool()
        
    def initialize(self):
        """Initialize all TSS components"""
        # Initialize context tree
        self.context_tree = APIContextTree()
        
        # Initialize domain adapter
        self.domain_adapter = DomainAdapter(self.context_tree)
        
        # Initialize API evolver
        self.api_evolver = APIEvolver()
        
    def run_synthesis(self, pretraining_data_path: str, target_api_count: int = 26507):
        """Run the complete TSS synthesis process"""
        if not self.context_tree:
            self.initialize()
            
        # Step 1: Speciation - build context tree
        self.context_tree.build_from_pretraining_data(pretraining_data_path)
        
        # Step 2 & 3: Adaptation and Evolution - generate APIs
        generated_count = 0
        while generated_count < target_api_count:
            # Adaptation: sample subtree and specify diversity
            subtree = self.domain_adapter.sample_subtree()
            
            # Evolution: generate new API based on subtree
            new_api = self.api_evolver.generate_api(
                subtree=subtree,
                example_api=self.api_pool.sample_example()
            )
            
            # Add to pool if valid
            if self.api_pool.add_api(new_api):
                generated_count += 1
                
        return self.api_pool
