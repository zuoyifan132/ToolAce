"""
Rule Checker Module

This module implements the rule-based verification layer that performs
structural and syntactic validation of dialog data.
"""

import re
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass


@dataclass
class RuleCheckResult:
    """Result of rule-based checking"""
    passed: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class RuleChecker:
    """
    Rule-based verification layer that performs structural and syntactic validation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.strict_mode = self.config.get("strict_mode", True)
        self.error_tolerance = self.config.get("error_tolerance", 0)
        
        # Load verification rules
        self.checks = self.config.get("checks", {
            "api_definition_clarity": True,
            "function_call_executability": True,
            "dialog_correctness": True,
            "data_sample_consistency": True,
            "parameter_format_validation": True
        })
        
    def verify(self, dialog_data: Dict) -> RuleCheckResult:
        """
        Perform comprehensive rule-based verification
        
        Args:
            dialog_data: Dialog data to verify
            
        Returns:
            RuleCheckResult with verification results
        """
        errors = []
        warnings = []
        details = {}
        
        # 1. API Definition Clarity Check
        if self.checks.get("api_definition_clarity", True):
            api_check_result = self.check_api_definition_clarity(dialog_data)
            errors.extend(api_check_result["errors"])
            warnings.extend(api_check_result["warnings"])
            details["api_definition"] = api_check_result
            
        # 2. Function Call Executability Check
        if self.checks.get("function_call_executability", True):
            func_check_result = self.check_function_call_executability(dialog_data)
            errors.extend(func_check_result["errors"])
            warnings.extend(func_check_result["warnings"])
            details["function_calls"] = func_check_result
            
        # 3. Dialog Correctness Check
        if self.checks.get("dialog_correctness", True):
            dialog_check_result = self.check_dialog_correctness(dialog_data)
            errors.extend(dialog_check_result["errors"])
            warnings.extend(dialog_check_result["warnings"])
            details["dialog"] = dialog_check_result
            
        # 4. Data Sample Consistency Check
        if self.checks.get("data_sample_consistency", True):
            consistency_check_result = self.check_data_sample_consistency(dialog_data)
            errors.extend(consistency_check_result["errors"])
            warnings.extend(consistency_check_result["warnings"])
            details["consistency"] = consistency_check_result
            
        # 5. Parameter Format Validation
        if self.checks.get("parameter_format_validation", True):
            param_check_result = self.check_parameter_format_validation(dialog_data)
            errors.extend(param_check_result["errors"])
            warnings.extend(param_check_result["warnings"])
            details["parameters"] = param_check_result
            
        # Determine if passed based on error tolerance
        passed = len(errors) <= self.error_tolerance
        
        return RuleCheckResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            details=details
        )
        
    def check_api_definition_clarity(self, dialog_data: Dict) -> Dict[str, Any]:
        """Check API definition clarity and completeness"""
        errors = []
        warnings = []
        checked_apis = []
        
        api_candidates = dialog_data.get("api_candidates", [])
        
        for i, api in enumerate(api_candidates):
            api_errors = []
            api_warnings = []
            
            # Check required fields
            if not api.get("name"):
                api_errors.append(f"API {i+1}: 缺少name字段")
            elif not isinstance(api["name"], str) or not api["name"].strip():
                api_errors.append(f"API {i+1}: name字段为空或格式错误")
                
            if not api.get("description"):
                api_warnings.append(f"API {i+1}: 缺少description字段")
            elif len(api["description"]) < 10:
                api_warnings.append(f"API {i+1}: description过于简短")
                
            # Check parameters structure
            parameters = api.get("parameters")
            if parameters is not None:
                param_errors = self._validate_parameters_structure(parameters, f"API {i+1}")
                api_errors.extend(param_errors)
            else:
                api_warnings.append(f"API {i+1}: 缺少parameters定义")
                
            # Check returns structure
            returns = api.get("returns")
            if returns is not None:
                return_errors = self._validate_returns_structure(returns, f"API {i+1}")
                api_errors.extend(return_errors)
            else:
                api_warnings.append(f"API {i+1}: 缺少returns定义")
                
            checked_apis.append({
                "name": api.get("name", f"api_{i+1}"),
                "errors": api_errors,
                "warnings": api_warnings
            })
            
            errors.extend(api_errors)
            warnings.extend(api_warnings)
            
        return {
            "errors": errors,
            "warnings": warnings,
            "checked_apis": checked_apis,
            "total_apis": len(api_candidates)
        }
        
    def check_function_call_executability(self, dialog_data: Dict) -> Dict[str, Any]:
        """Check function call executability"""
        errors = []
        warnings = []
        checked_calls = []
        
        api_candidates = dialog_data.get("api_candidates", [])
        api_map = {api.get("name"): api for api in api_candidates if api.get("name")}
        
        # Extract function calls from dialog turns
        function_calls = self._extract_function_calls_from_dialog(dialog_data)
        
        for i, call in enumerate(function_calls):
            call_errors = []
            call_warnings = []
            
            call_name = call.get("name")
            call_params = call.get("parameters", {})
            
            # Check if API name exists
            if not call_name:
                call_errors.append(f"函数调用 {i+1}: 缺少name字段")
            elif call_name not in api_map:
                call_errors.append(f"函数调用 {i+1}: API '{call_name}' 未在候选列表中找到")
            else:
                # Validate parameters against API definition
                api_def = api_map[call_name]
                param_errors = self._validate_call_parameters(call_params, api_def, f"函数调用 {i+1}")
                call_errors.extend(param_errors)
                
            checked_calls.append({
                "name": call_name,
                "parameters": call_params,
                "errors": call_errors,
                "warnings": call_warnings
            })
            
            errors.extend(call_errors)
            warnings.extend(call_warnings)
            
        return {
            "errors": errors,
            "warnings": warnings,
            "checked_calls": checked_calls,
            "total_calls": len(function_calls)
        }
        
    def check_dialog_correctness(self, dialog_data: Dict) -> Dict[str, Any]:
        """Check dialog structure and flow correctness"""
        errors = []
        warnings = []
        
        turns = dialog_data.get("turns", [])
        
        if not turns:
            errors.append("对话为空，没有任何轮次")
            return {"errors": errors, "warnings": warnings, "total_turns": 0}
            
        # Check turn structure
        for i, turn in enumerate(turns):
            turn_errors = []
            
            # Check required fields
            if "role" not in turn:
                turn_errors.append(f"轮次 {i+1}: 缺少role字段")
            elif turn["role"] not in ["user", "assistant", "tool"]:
                turn_errors.append(f"轮次 {i+1}: role字段值无效 '{turn['role']}'")
                
            if "content" not in turn:
                turn_errors.append(f"轮次 {i+1}: 缺少content字段")
            elif not isinstance(turn["content"], str):
                turn_errors.append(f"轮次 {i+1}: content字段必须是字符串")
            elif not turn["content"].strip():
                turn_errors.append(f"轮次 {i+1}: content字段为空")
                
            errors.extend(turn_errors)
            
        # Check dialog flow
        flow_errors = self._check_dialog_flow(turns)
        errors.extend(flow_errors)
        
        # Check dialog completeness
        user_turns = [t for t in turns if t.get("role") == "user"]
        assistant_turns = [t for t in turns if t.get("role") == "assistant"]
        
        if len(user_turns) == 0:
            errors.append("对话中没有用户发言")
        if len(assistant_turns) == 0:
            warnings.append("对话中没有助手回复")
            
        return {
            "errors": errors,
            "warnings": warnings,
            "total_turns": len(turns),
            "user_turns": len(user_turns),
            "assistant_turns": len(assistant_turns)
        }
        
    def check_data_sample_consistency(self, dialog_data: Dict) -> Dict[str, Any]:
        """Check internal consistency of the data sample"""
        errors = []
        warnings = []
        
        # Check basic structure
        required_fields = ["dialog_id", "dialog_type", "turns"]
        for field in required_fields:
            if field not in dialog_data:
                errors.append(f"缺少必需字段: {field}")
                
        # Check dialog_type validity
        dialog_type = dialog_data.get("dialog_type")
        valid_types = ["single", "parallel", "dependent", "non_tool"]
        if dialog_type and dialog_type not in valid_types:
            errors.append(f"无效的dialog_type: {dialog_type}")
            
        # Check consistency between dialog_type and actual function calls
        function_calls = self._extract_function_calls_from_dialog(dialog_data)
        actual_type = self._infer_dialog_type_from_calls(function_calls)
        
        if dialog_type and actual_type and dialog_type != actual_type:
            warnings.append(f"声明的dialog_type ({dialog_type}) 与实际类型 ({actual_type}) 不一致")
            
        # Check API candidates usage
        api_candidates = dialog_data.get("api_candidates", [])
        used_apis = {call.get("name") for call in function_calls if call.get("name")}
        available_apis = {api.get("name") for api in api_candidates if api.get("name")}
        
        unused_apis = available_apis - used_apis
        if len(unused_apis) == len(available_apis) and dialog_type != "non_tool":
            warnings.append("没有使用任何可用的API")
            
        return {
            "errors": errors,
            "warnings": warnings,
            "declared_type": dialog_type,
            "inferred_type": actual_type,
            "used_apis": list(used_apis),
            "unused_apis": list(unused_apis)
        }
        
    def check_parameter_format_validation(self, dialog_data: Dict) -> Dict[str, Any]:
        """Check parameter format validation using regex patterns"""
        errors = []
        warnings = []
        
        api_candidates = dialog_data.get("api_candidates", [])
        function_calls = self._extract_function_calls_from_dialog(dialog_data)
        
        for call in function_calls:
            call_name = call.get("name")
            call_params = call.get("parameters", {})
            
            # Find API definition
            api_def = None
            for api in api_candidates:
                if api.get("name") == call_name:
                    api_def = api
                    break
                    
            if not api_def:
                continue
                
            # Validate each parameter format
            param_definitions = api_def.get("parameters", {}).get("properties", {})
            
            for param_name, param_value in call_params.items():
                if param_name in param_definitions:
                    param_def = param_definitions[param_name]
                    format_errors = self._validate_parameter_format(
                        param_name, param_value, param_def, call_name
                    )
                    errors.extend(format_errors)
                    
        return {
            "errors": errors,
            "warnings": warnings,
            "validated_parameters": len([p for call in function_calls for p in call.get("parameters", {})])
        }
        
    def _validate_parameters_structure(self, parameters: Dict, context: str) -> List[str]:
        """Validate parameters structure"""
        errors = []
        
        if not isinstance(parameters, dict):
            errors.append(f"{context}: parameters必须是字典类型")
            return errors
            
        if "type" not in parameters:
            errors.append(f"{context}: parameters缺少type字段")
        elif parameters["type"] != "object":
            errors.append(f"{context}: parameters的type必须是'object'")
            
        properties = parameters.get("properties")
        if properties is not None:
            if not isinstance(properties, dict):
                errors.append(f"{context}: properties必须是字典类型")
            else:
                # Validate each property
                for prop_name, prop_def in properties.items():
                    if not isinstance(prop_def, dict):
                        errors.append(f"{context}: 属性 '{prop_name}' 定义必须是字典类型")
                    elif "type" not in prop_def:
                        errors.append(f"{context}: 属性 '{prop_name}' 缺少type字段")
                        
        return errors
        
    def _validate_returns_structure(self, returns: Dict, context: str) -> List[str]:
        """Validate returns structure"""
        errors = []
        
        if not isinstance(returns, dict):
            errors.append(f"{context}: returns必须是字典类型")
            return errors
            
        if "type" not in returns:
            errors.append(f"{context}: returns缺少type字段")
            
        return errors
        
    def _extract_function_calls_from_dialog(self, dialog_data: Dict) -> List[Dict]:
        """Extract all function calls from dialog turns"""
        function_calls = []
        
        turns = dialog_data.get("turns", [])
        for turn in turns:
            if turn.get("role") == "assistant":
                calls = turn.get("function_calls", [])
                if isinstance(calls, list):
                    function_calls.extend(calls)
                    
        return function_calls
        
    def _validate_call_parameters(self, call_params: Dict, api_def: Dict, context: str) -> List[str]:
        """Validate function call parameters against API definition"""
        errors = []
        
        api_params = api_def.get("parameters", {})
        required_params = api_params.get("required", [])
        param_properties = api_params.get("properties", {})
        
        # Check required parameters
        for required_param in required_params:
            if required_param not in call_params:
                errors.append(f"{context}: 缺少必需参数 '{required_param}'")
                
        # Check parameter types
        for param_name, param_value in call_params.items():
            if param_name in param_properties:
                param_def = param_properties[param_name]
                expected_type = param_def.get("type")
                
                if not self._check_parameter_type(param_value, expected_type):
                    errors.append(f"{context}: 参数 '{param_name}' 类型错误，期望 {expected_type}")
                    
        return errors
        
    def _check_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Check if parameter value matches expected type"""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        else:
            return True  # Unknown type, assume valid
            
    def _check_dialog_flow(self, turns: List[Dict]) -> List[str]:
        """Check dialog flow logic"""
        errors = []
        
        if not turns:
            return errors
            
        # Check if dialog starts with user
        if turns[0].get("role") != "user":
            errors.append("对话应该以用户发言开始")
            
        # Check alternating pattern (not strictly required but good practice)
        prev_role = None
        consecutive_count = 0
        
        for i, turn in enumerate(turns):
            role = turn.get("role")
            
            if role == prev_role:
                consecutive_count += 1
                if consecutive_count >= 3:
                    errors.append(f"轮次 {i+1}: 连续{consecutive_count}次相同角色发言")
            else:
                consecutive_count = 1
                
            prev_role = role
            
        return errors
        
    def _infer_dialog_type_from_calls(self, function_calls: List[Dict]) -> Optional[str]:
        """Infer dialog type from function calls"""
        if not function_calls:
            return "non_tool"
            
        # Count unique APIs called
        unique_apis = set(call.get("name") for call in function_calls if call.get("name"))
        
        if len(unique_apis) == 1 and len(function_calls) == 1:
            return "single"
        elif len(unique_apis) > 1:
            # Check if calls are in same turn (parallel) or different turns (dependent)
            # This is a simplified check - actual implementation would be more sophisticated
            return "parallel"  # Simplified assumption
        else:
            return "single"
            
    def _validate_parameter_format(self, param_name: str, param_value: Any, param_def: Dict, context: str) -> List[str]:
        """Validate parameter format using regex patterns"""
        errors = []
        
        # Check pattern constraint
        pattern = param_def.get("pattern")
        if pattern and isinstance(param_value, str):
            try:
                if not re.match(pattern, param_value):
                    errors.append(f"{context}: 参数 '{param_name}' 不符合格式要求 '{pattern}'")
            except re.error:
                errors.append(f"{context}: 参数 '{param_name}' 的格式模式无效")
                
        # Check numeric constraints
        if param_def.get("type") in ["integer", "number"]:
            if isinstance(param_value, (int, float)):
                minimum = param_def.get("minimum")
                maximum = param_def.get("maximum")
                
                if minimum is not None and param_value < minimum:
                    errors.append(f"{context}: 参数 '{param_name}' 值 {param_value} 小于最小值 {minimum}")
                if maximum is not None and param_value > maximum:
                    errors.append(f"{context}: 参数 '{param_name}' 值 {param_value} 大于最大值 {maximum}")
                    
        # Check string length constraints
        if param_def.get("type") == "string" and isinstance(param_value, str):
            min_length = param_def.get("minLength")
            max_length = param_def.get("maxLength")
            
            if min_length is not None and len(param_value) < min_length:
                errors.append(f"{context}: 参数 '{param_name}' 长度 {len(param_value)} 小于最小长度 {min_length}")
            if max_length is not None and len(param_value) > max_length:
                errors.append(f"{context}: 参数 '{param_name}' 长度 {len(param_value)} 大于最大长度 {max_length}")
                
        return errors
