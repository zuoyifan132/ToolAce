"""
API Pool Module - API Collection Management

This module manages the collection and maintenance of the entire API pool,
including storage, retrieval, quality assessment, and statistics collection.
"""

import json
import random
import hashlib
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from pathlib import Path

from .evolution import APIDefinition


@dataclass
class APIMetrics:
    """Metrics for API quality assessment"""
    completeness_score: float  # How complete the API definition is
    complexity_score: float    # Complexity level of the API
    uniqueness_score: float    # How unique compared to other APIs
    quality_score: float       # Overall quality score
    usage_frequency: int       # How often this API has been sampled
    
    
class APIPool:
    """
    Manages the comprehensive API pool containing all generated APIs
    with quality assessment, retrieval, and statistical analysis capabilities.
    """
    
    def __init__(self, max_size: int = 30000):
        self.max_size = max_size
        self.apis: Dict[str, APIDefinition] = {}  # api_id -> APIDefinition
        self.metrics: Dict[str, APIMetrics] = {}  # api_id -> APIMetrics
        self.domain_index: Dict[str, Set[str]] = defaultdict(set)  # domain -> api_ids
        self.functionality_index: Dict[str, Set[str]] = defaultdict(set)  # functionality -> api_ids
        self.complexity_index: Dict[float, Set[str]] = defaultdict(set)  # complexity -> api_ids
        self.example_buffer: List[APIDefinition] = []  # Buffer for API examples
        self.api_signatures: Set[str] = set()  # For uniqueness checking
        
    def add_api(self, api: APIDefinition) -> bool:
        """
        Add an API to the pool after validation and quality assessment
        
        Args:
            api: APIDefinition to add
            
        Returns:
            True if API was added successfully, False otherwise
        """
        # Generate unique ID for the API
        api_id = self._generate_api_id(api)
        
        # Check if API already exists
        if api_id in self.apis:
            return False
            
        # Check uniqueness
        signature = self._generate_api_signature(api)
        if signature in self.api_signatures:
            return False
            
        # Validate API
        if not self._validate_api(api):
            return False
            
        # Check pool capacity
        if len(self.apis) >= self.max_size:
            if not self._make_space_for_new_api(api):
                return False
                
        # Calculate metrics
        metrics = self._calculate_api_metrics(api)
        
        # Add to pool
        self.apis[api_id] = api
        self.metrics[api_id] = metrics
        self.api_signatures.add(signature)
        
        # Update indices
        self._update_indices(api_id, api)
        
        # Add to example buffer with some probability
        if random.random() < 0.1:  # 10% chance
            self._add_to_example_buffer(api)
            
        return True
        
    def _generate_api_id(self, api: APIDefinition) -> str:
        """Generate unique ID for an API"""
        content = f"{api.name}_{api.domain}_{len(api.functionalities)}_{api.complexity_score}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
        
    def _generate_api_signature(self, api: APIDefinition) -> str:
        """Generate signature for uniqueness checking"""
        # Create signature based on name, domain, and core functionalities
        func_signature = "_".join(sorted(api.functionalities))
        param_names = sorted(api.parameters.get("properties", {}).keys())
        param_signature = "_".join(param_names)
        
        return f"{api.name}_{api.domain}_{func_signature}_{param_signature}"
        
    def _validate_api(self, api: APIDefinition) -> bool:
        """Validate API definition for correctness"""
        # Check required fields
        if not api.name or not api.description:
            return False
            
        # Check parameters structure
        if not isinstance(api.parameters, dict):
            return False
            
        if "type" not in api.parameters or api.parameters["type"] != "object":
            return False
            
        # Check properties
        properties = api.parameters.get("properties", {})
        if not isinstance(properties, dict):
            return False
            
        # Validate each parameter
        for param_name, param_def in properties.items():
            if not self._validate_parameter(param_def):
                return False
                
        # Check returns structure
        if not isinstance(api.returns, dict):
            return False
            
        return True
        
    def _validate_parameter(self, param_def: Dict) -> bool:
        """Validate a single parameter definition"""
        if "type" not in param_def:
            return False
            
        valid_types = ["string", "integer", "number", "boolean", "array", "object"]
        if param_def["type"] not in valid_types:
            return False
            
        return True
        
    def _calculate_api_metrics(self, api: APIDefinition) -> APIMetrics:
        """Calculate quality metrics for an API"""
        # Completeness score
        completeness = self._calculate_completeness_score(api)
        
        # Complexity score (already available)
        complexity = api.complexity_score
        
        # Uniqueness score
        uniqueness = self._calculate_uniqueness_score(api)
        
        # Overall quality score
        quality = (completeness * 0.4 + complexity * 0.3 + uniqueness * 0.3)
        
        return APIMetrics(
            completeness_score=completeness,
            complexity_score=complexity,
            uniqueness_score=uniqueness,
            quality_score=quality,
            usage_frequency=0
        )
        
    def _calculate_completeness_score(self, api: APIDefinition) -> float:
        """Calculate how complete the API definition is"""
        score = 0.0
        
        # Check basic fields
        if api.name: score += 0.15
        if api.description: score += 0.15
        if api.domain: score += 0.1
        if api.functionalities: score += 0.1
        
        # Check parameters
        properties = api.parameters.get("properties", {})
        if properties:
            score += 0.2
            # Check parameter completeness
            param_completeness = sum(
                1 for param in properties.values()
                if "description" in param and "type" in param
            ) / len(properties)
            score += param_completeness * 0.1
            
        # Check returns
        if api.returns and "description" in api.returns:
            score += 0.1
            
        # Check examples
        if api.examples:
            score += 0.1
            
        return min(score, 1.0)
        
    def _calculate_uniqueness_score(self, api: APIDefinition) -> float:
        """Calculate how unique this API is compared to existing ones"""
        if not self.apis:
            return 1.0
            
        # Compare with existing APIs in the same domain
        domain_apis = [
            self.apis[api_id] for api_id in self.domain_index.get(api.domain, set())
        ]
        
        if not domain_apis:
            return 0.9  # High uniqueness for new domain
            
        # Calculate similarity with existing APIs
        similarities = []
        for existing_api in domain_apis:
            similarity = self._calculate_similarity(api, existing_api)
            similarities.append(similarity)
            
        # Uniqueness is inverse of maximum similarity
        max_similarity = max(similarities) if similarities else 0
        return 1.0 - max_similarity
        
    def _calculate_similarity(self, api1: APIDefinition, api2: APIDefinition) -> float:
        """Calculate similarity between two APIs"""
        # Functionality overlap
        func1 = set(api1.functionalities)
        func2 = set(api2.functionalities)
        func_similarity = len(func1 & func2) / len(func1 | func2) if (func1 | func2) else 0
        
        # Parameter overlap
        params1 = set(api1.parameters.get("properties", {}).keys())
        params2 = set(api2.parameters.get("properties", {}).keys())
        param_similarity = len(params1 & params2) / len(params1 | params2) if (params1 | params2) else 0
        
        # Name similarity (simple)
        name_similarity = 1.0 if api1.name == api2.name else 0.0
        
        return (func_similarity * 0.5 + param_similarity * 0.3 + name_similarity * 0.2)
        
    def _make_space_for_new_api(self, new_api: APIDefinition) -> bool:
        """Make space for a new API by removing lower quality APIs"""
        new_metrics = self._calculate_api_metrics(new_api)
        
        # Find APIs with lower quality scores
        candidates_for_removal = [
            (api_id, metrics.quality_score) 
            for api_id, metrics in self.metrics.items()
            if metrics.quality_score < new_metrics.quality_score
        ]
        
        if not candidates_for_removal:
            return False  # New API is not better than existing ones
            
        # Remove the lowest quality API
        api_to_remove = min(candidates_for_removal, key=lambda x: x[1])[0]
        self.remove_api(api_to_remove)
        return True
        
    def remove_api(self, api_id: str) -> bool:
        """Remove an API from the pool"""
        if api_id not in self.apis:
            return False
            
        api = self.apis[api_id]
        
        # Remove from main storage
        del self.apis[api_id]
        del self.metrics[api_id]
        
        # Remove signature
        signature = self._generate_api_signature(api)
        self.api_signatures.discard(signature)
        
        # Update indices
        self._remove_from_indices(api_id, api)
        
        return True
        
    def _update_indices(self, api_id: str, api: APIDefinition):
        """Update all indices when adding an API"""
        # Domain index
        self.domain_index[api.domain].add(api_id)
        
        # Functionality index
        for func in api.functionalities:
            self.functionality_index[func].add(api_id)
            
        # Complexity index
        complexity_bucket = round(api.complexity_score, 1)
        self.complexity_index[complexity_bucket].add(api_id)
        
    def _remove_from_indices(self, api_id: str, api: APIDefinition):
        """Remove from all indices when removing an API"""
        # Domain index
        self.domain_index[api.domain].discard(api_id)
        
        # Functionality index
        for func in api.functionalities:
            self.functionality_index[func].discard(api_id)
            
        # Complexity index
        complexity_bucket = round(api.complexity_score, 1)
        self.complexity_index[complexity_bucket].discard(api_id)
        
    def _add_to_example_buffer(self, api: APIDefinition):
        """Add API to example buffer for future use"""
        max_buffer_size = 1000
        
        if len(self.example_buffer) >= max_buffer_size:
            # Remove random old example
            self.example_buffer.pop(random.randint(0, len(self.example_buffer) - 1))
            
        self.example_buffer.append(api)
        
    def sample_example(self) -> Optional[APIDefinition]:
        """Sample an API example from the buffer"""
        if not self.example_buffer:
            return None
        return random.choice(self.example_buffer)
        
    def sample_apis(self, 
                   count: int,
                   domain: Optional[str] = None,
                   complexity_range: Optional[Tuple[float, float]] = None,
                   functionalities: Optional[List[str]] = None) -> List[APIDefinition]:
        """
        Sample APIs from the pool with specified criteria
        
        Args:
            count: Number of APIs to sample
            domain: Specific domain to sample from
            complexity_range: (min, max) complexity range
            functionalities: Required functionalities
            
        Returns:
            List of sampled APIs
        """
        # Get candidate API IDs based on criteria
        candidate_ids = self._get_candidate_ids(domain, complexity_range, functionalities)
        
        if not candidate_ids:
            return []
            
        # Sample without replacement
        sample_size = min(count, len(candidate_ids))
        sampled_ids = random.sample(list(candidate_ids), sample_size)
        
        # Update usage frequency
        for api_id in sampled_ids:
            if api_id in self.metrics:
                self.metrics[api_id].usage_frequency += 1
                
        return [self.apis[api_id] for api_id in sampled_ids]
        
    def _get_candidate_ids(self, 
                          domain: Optional[str],
                          complexity_range: Optional[Tuple[float, float]],
                          functionalities: Optional[List[str]]) -> Set[str]:
        """Get candidate API IDs based on filtering criteria"""
        candidate_ids = set(self.apis.keys())
        
        # Filter by domain
        if domain:
            domain_ids = self.domain_index.get(domain, set())
            candidate_ids &= domain_ids
            
        # Filter by complexity
        if complexity_range:
            min_complexity, max_complexity = complexity_range
            complexity_ids = set()
            for complexity, ids in self.complexity_index.items():
                if min_complexity <= complexity <= max_complexity:
                    complexity_ids.update(ids)
            candidate_ids &= complexity_ids
            
        # Filter by functionalities
        if functionalities:
            for functionality in functionalities:
                func_ids = self.functionality_index.get(functionality, set())
                candidate_ids &= func_ids
                
        return candidate_ids
        
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the API pool"""
        if not self.apis:
            return {"total_apis": 0}
            
        # Basic statistics
        total_apis = len(self.apis)
        total_domains = len(self.domain_index)
        total_functionalities = len(self.functionality_index)
        
        # Quality statistics
        quality_scores = [metrics.quality_score for metrics in self.metrics.values()]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        complexity_scores = [metrics.complexity_score for metrics in self.metrics.values()]
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        
        # Domain distribution
        domain_distribution = {
            domain: len(api_ids) 
            for domain, api_ids in self.domain_index.items()
        }
        
        # Complexity distribution
        complexity_distribution = Counter()
        for metrics in self.metrics.values():
            bucket = round(metrics.complexity_score, 1)
            complexity_distribution[bucket] += 1
            
        # Top functionalities
        functionality_counts = {
            func: len(api_ids)
            for func, api_ids in self.functionality_index.items()
        }
        top_functionalities = dict(Counter(functionality_counts).most_common(10))
        
        return {
            "total_apis": total_apis,
            "total_domains": total_domains,
            "total_functionalities": total_functionalities,
            "average_quality_score": round(avg_quality, 3),
            "average_complexity_score": round(avg_complexity, 3),
            "domain_distribution": domain_distribution,
            "complexity_distribution": dict(complexity_distribution),
            "top_functionalities": top_functionalities,
            "example_buffer_size": len(self.example_buffer)
        }
        
    def export_apis(self, filepath: str, format: str = "json"):
        """Export APIs to file in specified format"""
        if format == "json":
            self._export_to_json(filepath)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def _export_to_json(self, filepath: str):
        """Export APIs to JSON file"""
        export_data = {
            "apis": [
                {
                    "id": api_id,
                    "definition": asdict(api),
                    "metrics": asdict(self.metrics[api_id])
                }
                for api_id, api in self.apis.items()
            ],
            "statistics": self.get_pool_statistics()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
    def import_apis(self, filepath: str):
        """Import APIs from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
            
        for api_data in import_data.get("apis", []):
            api_def = api_data["definition"]
            # Convert dict back to APIDefinition
            api = APIDefinition(**api_def)
            self.add_api(api)
            
    def clear_pool(self):
        """Clear all APIs from the pool"""
        self.apis.clear()
        self.metrics.clear()
        self.domain_index.clear()
        self.functionality_index.clear()
        self.complexity_index.clear()
        self.example_buffer.clear()
        self.api_signatures.clear()
        
    def get_api_by_id(self, api_id: str) -> Optional[APIDefinition]:
        """Get a specific API by its ID"""
        return self.apis.get(api_id)
        
    def search_apis(self, query: str) -> List[Tuple[str, APIDefinition, float]]:
        """
        Search APIs by query with relevance scoring
        
        Returns:
            List of (api_id, api, relevance_score) tuples
        """
        results = []
        query_lower = query.lower()
        
        for api_id, api in self.apis.items():
            score = 0.0
            
            # Name match
            if query_lower in api.name.lower():
                score += 0.4
                
            # Description match
            if query_lower in api.description.lower():
                score += 0.3
                
            # Functionality match
            for func in api.functionalities:
                if query_lower in func.lower():
                    score += 0.2
                    break
                    
            # Domain match
            if query_lower in api.domain.lower():
                score += 0.1
                
            if score > 0:
                results.append((api_id, api, score))
                
        # Sort by relevance score
        results.sort(key=lambda x: x[2], reverse=True)
        return results
