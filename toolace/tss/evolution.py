"""
Evolution Module - API Continuous Improvement and Generation

This module implements the evolution step of TSS, which continuously improves
and adapts APIs based on outcomes and new requirements through various diversity indicators.
"""

import json
import random
import importlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .speciation import TreeNode
from .adaptation import APISpec, DiversityLevel
from ..utils.model_manager import generate


class DiversityMutation(Enum):
    """Types of diversity mutations for API evolution"""
    ADD_FUNCTIONALITY = "add_functionality"
    ADD_PARAMETER = "add_parameter" 
    ADD_CONSTRAINT = "add_constraint"
    MUTATE_PARAMETER_TYPE = "mutate_parameter_type"
    UPDATE_RETURN_TYPE = "update_return_type"
    MODIFY_DESCRIPTION = "modify_description"


@dataclass
class APIDefinition:
    """Complete API definition with all necessary components"""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    domain: str
    functionalities: List[str]
    complexity_score: float
    constraints: List[str]
    examples: List[Dict]
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "returns": self.returns,
            "metadata": {
                "domain": self.domain,
                "functionalities": self.functionalities,
                "complexity_score": self.complexity_score,
                "constraints": self.constraints
            },
            "examples": self.examples
        }


class APIEvolver:
    """
    Implements the evolution step of TSS, generating and improving APIs
    through continuous adaptation and diversity mutations.
    """
    
    def __init__(self, model_key: str = "tss_model"):
        self.model_key = model_key
        self.parameter_types = [
            "string", "integer", "number", "boolean", "array", "object"
        ]
        self.common_constraints = [
            "minimum", "maximum", "minLength", "maxLength", 
            "pattern", "enum", "format"
        ]
        self.mutation_probabilities = {
            DiversityMutation.ADD_FUNCTIONALITY: 0.2,
            DiversityMutation.ADD_PARAMETER: 0.25,
            DiversityMutation.ADD_CONSTRAINT: 0.15,
            DiversityMutation.MUTATE_PARAMETER_TYPE: 0.15,
            DiversityMutation.UPDATE_RETURN_TYPE: 0.15,
            DiversityMutation.MODIFY_DESCRIPTION: 0.1
        }
        
    def generate_api(self, 
                    subtree: TreeNode, 
                    example_api: Optional[APIDefinition] = None) -> APIDefinition:
        """
        Generate a new API definition based on a subtree and optional example
        
        Args:
            subtree: Sampled subtree from context tree
            example_api: Optional example API for reference
            
        Returns:
            Complete API definition
        """
        # Extract information from subtree
        domain = subtree.name
        functionalities = [child.name for child in subtree.children.values()]
        
        # Generate base API structure
        base_api = self._create_base_api(domain, functionalities, subtree)
        
        # Apply diversity mutations if example provided
        if example_api:
            base_api = self._apply_example_mutations(base_api, example_api)
            
        # Apply random diversity mutations
        evolved_api = self._apply_diversity_mutations(base_api)
        
        # Validate and refine
        return self._validate_and_refine(evolved_api)
        
    def _create_base_api(self, 
                        domain: str, 
                        functionalities: List[str],
                        subtree: TreeNode) -> APIDefinition:
        """Create a base API definition from domain and functionalities using LLM"""
        # Use LLM to generate comprehensive API definition
        llm_api = self._generate_api_with_llm(domain, functionalities, subtree)
        
        if llm_api:
            return llm_api
        
        # Fallback to rule-based generation
        return self._create_base_api_fallback(domain, functionalities, subtree)
        
    def _generate_api_with_llm(self, domain: str, functionalities: List[str], subtree: TreeNode) -> Optional[APIDefinition]:
        """Use LLM to generate complete API definition"""
        system_prompt = """你是一个API设计专家。请根据给定的领域和功能列表，设计一个完整的API定义。

请按照以下JSON Schema格式返回API定义：
{
    "name": "api_name",
    "description": "API功能描述",
    "parameters": {
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string|integer|boolean|array|object",
                "description": "参数描述",
                "minimum": 1,  // 可选约束
                "maximum": 100,  // 可选约束
                "pattern": "^[a-z]+$"  // 可选约束
            }
        },
        "required": ["required_param"]
    },
    "returns": {
        "type": "object",
        "description": "返回值描述",
        "properties": {
            "result": {"type": "object", "description": "结果数据"}
        }
    }
}

要求：
1. API名称使用英文，遵循RESTful命名规范
2. 参数设计要合理，包含必要的约束条件
3. 返回值结构要清晰，符合实际使用场景
4. 描述要准确且专业"""

        functionality_list = ", ".join(functionalities)
        user_prompt = f"""请为以下领域和功能设计API：

领域: {domain}
功能列表: {functionality_list}

子功能树:
{self._format_subtree_for_llm(subtree)}

请返回完整的JSON格式API定义。"""

        try:
            response = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=1024
            )
            
            # Parse JSON response
            api_data = json.loads(response.strip())
            
            # Convert to APIDefinition
            api_def = APIDefinition(
                name=api_data.get("name", "unknown_api"),
                description=api_data.get("description", ""),
                parameters=api_data.get("parameters", {}),
                returns=api_data.get("returns", {}),
                domain=domain,
                functionalities=functionalities,
                complexity_score=self._calculate_complexity_from_api_data(api_data),
                constraints=self._extract_constraints_from_api_data(api_data),
                examples=[]
            )
            
            return api_def
            
        except Exception as e:
            print(f"LLM API生成失败: {e}")
            return None
            
    def _format_subtree_for_llm(self, subtree: TreeNode) -> str:
        """Format subtree information for LLM prompt"""
        lines = [f"- {subtree.name}: {subtree.description}"]
        
        for child in subtree.children.values():
            lines.append(f"  - {child.name}: {child.description}")
            for subchild in child.children.values():
                lines.append(f"    - {subchild.name}")
                
        return "\n".join(lines)
        
    def _calculate_complexity_from_api_data(self, api_data: Dict) -> float:
        """Calculate complexity score from API data"""
        base_score = 0.3
        
        # Add complexity based on parameters
        params = api_data.get("parameters", {}).get("properties", {})
        param_score = len(params) * 0.1
        
        # Add complexity based on nested structures
        nested_score = 0
        for param in params.values():
            if param.get("type") in ["object", "array"]:
                nested_score += 0.1
                
        return min(base_score + param_score + nested_score, 1.0)
        
    def _extract_constraints_from_api_data(self, api_data: Dict) -> List[str]:
        """Extract constraints from API data"""
        constraints = []
        params = api_data.get("parameters", {}).get("properties", {})
        
        for param_name, param_def in params.items():
            if "minimum" in param_def:
                constraints.append(f"{param_name}最小值: {param_def['minimum']}")
            if "maximum" in param_def:
                constraints.append(f"{param_name}最大值: {param_def['maximum']}")
            if "pattern" in param_def:
                constraints.append(f"{param_name}格式: {param_def['pattern']}")
                
        return constraints
        
    def _create_base_api_fallback(self, 
                        domain: str, 
                        functionalities: List[str],
                        subtree: TreeNode) -> APIDefinition:
        """Fallback method for creating base API definition"""
        # Generate API name based on main functionality
        main_func = functionalities[0] if functionalities else "通用功能"
        api_name = self._generate_api_name(main_func, domain)
        
        # Generate description
        description = self._generate_description(domain, functionalities)
        
        # Generate parameters based on functionalities
        parameters = self._generate_parameters(functionalities, subtree)
        
        # Generate return type
        returns = self._generate_return_type(functionalities)
        
        # Calculate complexity score
        complexity_score = len(functionalities) * 0.3 + len(parameters.get("properties", {})) * 0.1
        complexity_score = min(complexity_score, 1.0)
        
        return APIDefinition(
            name=api_name,
            description=description,
            parameters=parameters,
            returns=returns,
            domain=domain,
            functionalities=functionalities,
            complexity_score=complexity_score,
            constraints=[],
            examples=[]
        )
        
    def _generate_api_name(self, main_functionality: str, domain: str) -> str:
        """Generate API name based on functionality and domain"""
        # Convert Chinese functionality to English-style API name
        name_mapping = {
            "获取": "get",
            "查询": "query", 
            "搜索": "search",
            "创建": "create",
            "更新": "update",
            "删除": "delete",
            "处理": "process",
            "分析": "analyze",
            "管理": "manage"
        }
        
        name_parts = []
        for chinese, english in name_mapping.items():
            if chinese in main_functionality:
                name_parts.append(english)
                break
        else:
            name_parts.append("process")
            
        # Add domain-specific suffix
        domain_suffix = domain.replace("服务", "").replace("系统", "")
        name_parts.append(domain_suffix.lower())
        
        return "_".join(name_parts)
        
    def _generate_description(self, domain: str, functionalities: List[str]) -> str:
        """Generate API description"""
        if len(functionalities) == 1:
            return f"在{domain}领域实现{functionalities[0]}功能"
        else:
            func_list = "、".join(functionalities[:3])  # Limit to first 3
            return f"在{domain}领域提供{func_list}等综合功能"
            
    def _generate_parameters(self, functionalities: List[str], subtree: TreeNode) -> Dict[str, Any]:
        """Generate parameter schema based on functionalities"""
        properties = {}
        required = []
        
        # Add common parameters based on functionality types
        for func in functionalities:
            params = self._get_parameters_for_functionality(func, subtree)
            properties.update(params["properties"])
            required.extend(params.get("required", []))
            
        # Remove duplicates from required
        required = list(set(required))
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
    def _get_parameters_for_functionality(self, functionality: str, subtree: TreeNode) -> Dict[str, Any]:
        """Get parameters specific to a functionality"""
        # Find the functionality node in subtree
        func_node = None
        for child in subtree.children.values():
            if child.name == functionality:
                func_node = child
                break
                
        if not func_node:
            return {"properties": {}, "required": []}
            
        # Generate parameters based on functionality type
        if "查询" in functionality or "获取" in functionality:
            return self._generate_query_parameters(functionality, func_node)
        elif "创建" in functionality or "添加" in functionality:
            return self._generate_create_parameters(functionality, func_node)
        elif "更新" in functionality or "修改" in functionality:
            return self._generate_update_parameters(functionality, func_node)
        elif "删除" in functionality:
            return self._generate_delete_parameters(functionality, func_node)
        else:
            return self._generate_generic_parameters(functionality, func_node)
            
    def _generate_query_parameters(self, functionality: str, func_node: TreeNode) -> Dict[str, Any]:
        """Generate parameters for query/get operations"""
        properties = {}
        required = []
        
        # Common query parameters
        if "天气" in functionality:
            properties["location"] = {
                "type": "string",
                "description": "地理位置（城市名或坐标）"
            }
            required.append("location")
            
            if "预报" in functionality:
                properties["days"] = {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 14,
                    "description": "预报天数"
                }
                
        elif "股票" in functionality or "价格" in functionality:
            properties["symbol"] = {
                "type": "string",
                "description": "股票代码或商品标识"
            }
            required.append("symbol")
            
        elif "音乐" in functionality:
            properties["query"] = {
                "type": "string",
                "description": "搜索关键词"
            }
            properties["limit"] = {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 20,
                "description": "返回结果数量限制"
            }
            
        # Add sub-functionality specific parameters
        for sub_func in func_node.children.values():
            if "详细" in sub_func.name:
                properties["include_details"] = {
                    "type": "boolean",
                    "default": False,
                    "description": "是否包含详细信息"
                }
                
        return {"properties": properties, "required": required}
        
    def _generate_create_parameters(self, functionality: str, func_node: TreeNode) -> Dict[str, Any]:
        """Generate parameters for create operations"""
        properties = {
            "data": {
                "type": "object",
                "description": "要创建的数据对象"
            }
        }
        required = ["data"]
        
        return {"properties": properties, "required": required}
        
    def _generate_update_parameters(self, functionality: str, func_node: TreeNode) -> Dict[str, Any]:
        """Generate parameters for update operations"""
        properties = {
            "id": {
                "type": "string",
                "description": "要更新的对象ID"
            },
            "data": {
                "type": "object", 
                "description": "更新数据"
            }
        }
        required = ["id", "data"]
        
        return {"properties": properties, "required": required}
        
    def _generate_delete_parameters(self, functionality: str, func_node: TreeNode) -> Dict[str, Any]:
        """Generate parameters for delete operations"""
        properties = {
            "id": {
                "type": "string",
                "description": "要删除的对象ID"
            }
        }
        required = ["id"]
        
        return {"properties": properties, "required": required}
        
    def _generate_generic_parameters(self, functionality: str, func_node: TreeNode) -> Dict[str, Any]:
        """Generate generic parameters for other operations"""
        properties = {
            "options": {
                "type": "object",
                "description": "操作选项配置"
            }
        }
        
        return {"properties": properties, "required": []}
        
    def _generate_return_type(self, functionalities: List[str]) -> Dict[str, Any]:
        """Generate return type based on functionalities"""
        # Simple return type generation
        if any("查询" in func or "获取" in func for func in functionalities):
            return {
                "type": "object",
                "description": "查询结果数据",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "结果数据列表"
                    },
                    "total": {
                        "type": "integer",
                        "description": "总数量"
                    }
                }
            }
        else:
            return {
                "type": "object", 
                "description": "操作结果",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "操作是否成功"
                    },
                    "message": {
                        "type": "string",
                        "description": "结果消息"
                    }
                }
            }
            
    def _apply_example_mutations(self, base_api: APIDefinition, example_api: APIDefinition) -> APIDefinition:
        """Apply mutations based on example API"""
        # Inherit some structure from example
        if example_api.parameters.get("properties"):
            # Add some parameters from example
            example_props = example_api.parameters["properties"]
            base_props = base_api.parameters.get("properties", {})
            
            # Select 1-2 compatible parameters
            compatible_params = self._find_compatible_parameters(base_api, example_props)
            base_props.update(compatible_params)
            
            base_api.parameters["properties"] = base_props
            
        return base_api
        
    def _find_compatible_parameters(self, base_api: APIDefinition, example_props: Dict) -> Dict:
        """Find parameters from example that are compatible with base API"""
        compatible = {}
        
        # Simple compatibility check - add generic parameters
        for param_name, param_def in example_props.items():
            if param_name in ["limit", "offset", "format", "sort_by"]:
                compatible[param_name] = param_def
                
        return compatible
        
    def _apply_diversity_mutations(self, api: APIDefinition) -> APIDefinition:
        """Apply diversity mutations to evolve the API"""
        # Apply multiple mutations based on probabilities
        for mutation_type, probability in self.mutation_probabilities.items():
            if random.random() < probability:
                api = self._apply_single_mutation(api, mutation_type)
                
        return api
        
    def _apply_single_mutation(self, api: APIDefinition, mutation_type: DiversityMutation) -> APIDefinition:
        """Apply a single type of mutation"""
        if mutation_type == DiversityMutation.ADD_PARAMETER:
            return self._add_parameter_mutation(api)
        elif mutation_type == DiversityMutation.ADD_CONSTRAINT:
            return self._add_constraint_mutation(api)
        elif mutation_type == DiversityMutation.MUTATE_PARAMETER_TYPE:
            return self._mutate_parameter_type(api)
        elif mutation_type == DiversityMutation.UPDATE_RETURN_TYPE:
            return self._update_return_type(api)
        elif mutation_type == DiversityMutation.ADD_FUNCTIONALITY:
            return self._add_functionality_mutation(api)
        elif mutation_type == DiversityMutation.MODIFY_DESCRIPTION:
            return self._modify_description_mutation(api)
        
        return api
        
    def _add_parameter_mutation(self, api: APIDefinition) -> APIDefinition:
        """Add a new parameter to the API"""
        properties = api.parameters.get("properties", {})
        
        # Common additional parameters
        new_params = {
            "timeout": {
                "type": "integer",
                "minimum": 1,
                "maximum": 300,
                "default": 30,
                "description": "请求超时时间（秒）"
            },
            "callback_url": {
                "type": "string",
                "format": "uri",
                "description": "回调URL地址"
            },
            "include_metadata": {
                "type": "boolean",
                "default": False,
                "description": "是否包含元数据"
            }
        }
        
        # Add a random new parameter
        param_name, param_def = random.choice(list(new_params.items()))
        if param_name not in properties:
            properties[param_name] = param_def
            
        return api
        
    def _add_constraint_mutation(self, api: APIDefinition) -> APIDefinition:
        """Add constraints to existing parameters"""
        properties = api.parameters.get("properties", {})
        
        for param_name, param_def in properties.items():
            if param_def.get("type") == "string" and "pattern" not in param_def:
                if random.random() < 0.3:  # 30% chance to add pattern
                    param_def["pattern"] = "^[a-zA-Z0-9_-]+$"
            elif param_def.get("type") == "integer" and "minimum" not in param_def:
                if random.random() < 0.3:
                    param_def["minimum"] = 0
                    
        return api
        
    def _mutate_parameter_type(self, api: APIDefinition) -> APIDefinition:
        """Mutate parameter types for evolution"""
        properties = api.parameters.get("properties", {})
        
        # Convert some string parameters to more specific types
        for param_name, param_def in properties.items():
            if param_def.get("type") == "string" and random.random() < 0.2:
                if "id" in param_name.lower():
                    param_def["format"] = "uuid"
                elif "url" in param_name.lower():
                    param_def["format"] = "uri"
                elif "email" in param_name.lower():
                    param_def["format"] = "email"
                    
        return api
        
    def _update_return_type(self, api: APIDefinition) -> APIDefinition:
        """Update and enhance return type"""
        returns = api.returns
        
        # Add pagination info for list returns
        if returns.get("properties", {}).get("data", {}).get("type") == "array":
            if "pagination" not in returns["properties"]:
                returns["properties"]["pagination"] = {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "per_page": {"type": "integer"},
                        "total": {"type": "integer"}
                    }
                }
                
        return api
        
    def _add_functionality_mutation(self, api: APIDefinition) -> APIDefinition:
        """Add new functionality to the API"""
        # This would be more sophisticated in a real implementation
        api.complexity_score = min(api.complexity_score + 0.1, 1.0)
        return api
        
    def _modify_description_mutation(self, api: APIDefinition) -> APIDefinition:
        """Modify API description for clarity"""
        # Add more details to description
        if "综合" not in api.description:
            api.description += "，提供综合性服务"
            
        return api
        
    def _validate_and_refine(self, api: APIDefinition) -> APIDefinition:
        """Validate and refine the generated API"""
        # Ensure required fields exist
        if "properties" not in api.parameters:
            api.parameters["properties"] = {}
            
        if "required" not in api.parameters:
            api.parameters["required"] = []
            
        # Generate examples
        api.examples = self._generate_examples(api)
        
        # Add final constraints
        api.constraints = self._extract_constraints(api)
        
        return api
        
    def _generate_examples(self, api: APIDefinition) -> List[Dict]:
        """Generate usage examples for the API"""
        examples = []
        
        # Generate example request
        properties = api.parameters.get("properties", {})
        example_params = {}
        
        for param_name, param_def in properties.items():
            example_params[param_name] = self._generate_example_value(param_def)
            
        examples.append({
            "description": f"{api.name}调用示例",
            "parameters": example_params,
            "expected_return": self._generate_example_return(api.returns)
        })
        
        return examples
        
    def _generate_example_value(self, param_def: Dict) -> Any:
        """Generate example value for a parameter"""
        param_type = param_def.get("type", "string")
        
        if param_type == "string":
            return "示例值"
        elif param_type == "integer":
            return param_def.get("default", 10)
        elif param_type == "boolean":
            return param_def.get("default", True)
        elif param_type == "array":
            return ["示例项1", "示例项2"]
        elif param_type == "object":
            return {"key": "value"}
        else:
            return "默认值"
            
    def _generate_example_return(self, returns: Dict) -> Dict:
        """Generate example return value"""
        return {"example": "返回示例"}
        
    def _extract_constraints(self, api: APIDefinition) -> List[str]:
        """Extract constraints from the API definition"""
        constraints = []
        
        properties = api.parameters.get("properties", {})
        for param_name, param_def in properties.items():
            if "minimum" in param_def:
                constraints.append(f"{param_name}最小值: {param_def['minimum']}")
            if "maximum" in param_def:
                constraints.append(f"{param_name}最大值: {param_def['maximum']}")
            if "pattern" in param_def:
                constraints.append(f"{param_name}格式约束: {param_def['pattern']}")
                
        return constraints
