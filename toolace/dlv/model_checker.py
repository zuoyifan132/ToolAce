"""
Model Checker Module

This module implements the model-based verification layer that uses LLMs
to check content quality, detect hallucinations, and verify consistency.
"""

import json
import importlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from ..utils.model_manager import generate


@dataclass
class ModelCheckResult:
    """Result of model-based checking"""
    passed: bool
    scores: Dict[str, float]
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class ModelChecker:
    """
    Model-based verification layer that uses LLMs to check content quality
    """
    
    def __init__(self, model_key: str = "dlv_model_checker_model", config: Dict[str, Any] = None):
        self.model_key = model_key
        self.config = config or {}
        self.thresholds = self.config.get("thresholds", {
            "hallucination_threshold": 0.3,
            "consistency_threshold": 0.7,
            "tool_response_threshold": 0.6,
            "overall_quality_threshold": 0.75
        })
        
    def verify(self, dialog_data: Dict) -> ModelCheckResult:
        """
        Perform comprehensive model-based verification
        
        Args:
            dialog_data: Dialog data to verify
            
        Returns:
            ModelCheckResult with verification results
        """
        scores = {}
        errors = []
        warnings = []
        details = {}
        
        # 1. Hallucination Detection
        hallucination_result = self.detect_hallucination(dialog_data)
        scores["hallucination_score"] = hallucination_result["score"]
        if hallucination_result["detected"]:
            errors.extend(hallucination_result["issues"])
        details["hallucination"] = hallucination_result
        
        # 2. Consistency Validation
        consistency_result = self.verify_consistency(dialog_data)
        scores["consistency_score"] = consistency_result["score"]
        if consistency_result["score"] < self.thresholds["consistency_threshold"]:
            errors.extend(consistency_result["issues"])
        details["consistency"] = consistency_result
        
        # 3. Tool Response Check
        tool_response_result = self.check_tool_response(dialog_data)
        scores["tool_response_score"] = tool_response_result["score"]
        if tool_response_result["score"] < self.thresholds["tool_response_threshold"]:
            warnings.extend(tool_response_result["issues"])
        details["tool_response"] = tool_response_result
        
        # Calculate overall score
        overall_score = (
            scores["hallucination_score"] * 0.4 +
            scores["consistency_score"] * 0.4 +
            scores["tool_response_score"] * 0.2
        )
        scores["overall_score"] = overall_score
        
        # Determine if passed
        passed = (
            overall_score >= self.thresholds["overall_quality_threshold"] and
            scores["hallucination_score"] >= self.thresholds["hallucination_threshold"] and
            scores["consistency_score"] >= self.thresholds["consistency_threshold"]
        )
        
        return ModelCheckResult(
            passed=passed,
            scores=scores,
            errors=errors,
            warnings=warnings,
            details=details
        )
        
    def detect_hallucination(self, dialog_data: Dict) -> Dict[str, Any]:
        """
        Detect hallucinations in function call parameters
        
        Args:
            dialog_data: Dialog data to check
            
        Returns:
            Hallucination detection result
        """
        system_prompt = """你是一个幻觉检测专家。请检查对话中的函数调用参数是否存在幻觉（编造的内容）。

幻觉定义：
1. 参数值在用户查询中未提及
2. 参数值明显是编造的（如虚假的ID、不存在的地址等）
3. 参数值与用户意图不符

请按照以下格式返回JSON：
{
    "detected": true/false,
    "score": 0.0-1.0,  // 1.0表示无幻觉，0.0表示严重幻觉
    "issues": ["具体的幻觉问题描述"],
    "analysis": "详细分析说明"
}"""

        dialog_text = self._format_dialog_for_analysis(dialog_data)
        user_prompt = f"""请检测以下对话中的幻觉：

{dialog_text}

请返回检测结果："""

        try:
            response = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=512
            )
            
            result = json.loads(response.strip())
            
            # Validate result format
            if not all(key in result for key in ["detected", "score", "issues"]):
                return self._fallback_hallucination_check(dialog_data)
                
            return result
            
        except Exception as e:
            print(f"幻觉检测失败: {e}")
            return self._fallback_hallucination_check(dialog_data)
            
    def verify_consistency(self, dialog_data: Dict) -> Dict[str, Any]:
        """
        Verify consistency between user requests and assistant responses
        
        Args:
            dialog_data: Dialog data to check
            
        Returns:
            Consistency verification result
        """
        system_prompt = """你是一个对话一致性验证专家。请检查助手的回复是否与用户请求一致。

检查要点：
1. 助手是否正确理解了用户意图
2. 函数调用是否符合用户需求
3. 回复内容是否回答了用户问题
4. 对话流程是否自然合理

请按照以下格式返回JSON：
{
    "score": 0.0-1.0,  // 1.0表示完全一致，0.0表示完全不一致
    "issues": ["一致性问题描述"],
    "analysis": "详细分析说明"
}"""

        dialog_text = self._format_dialog_for_analysis(dialog_data)
        user_prompt = f"""请验证以下对话的一致性：

{dialog_text}

请返回验证结果："""

        try:
            response = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=512
            )
            
            result = json.loads(response.strip())
            
            # Validate result format
            if "score" not in result:
                return self._fallback_consistency_check(dialog_data)
                
            return result
            
        except Exception as e:
            print(f"一致性验证失败: {e}")
            return self._fallback_consistency_check(dialog_data)
            
    def check_tool_response(self, dialog_data: Dict) -> Dict[str, Any]:
        """
        Check if tool responses are reasonable and align with API definitions
        
        Args:
            dialog_data: Dialog data to check
            
        Returns:
            Tool response check result
        """
        system_prompt = """你是一个工具响应验证专家。请检查工具/API的响应是否合理。

检查要点：
1. 响应格式是否符合API定义
2. 响应内容是否合理真实
3. 响应是否与输入参数匹配
4. 数据类型和结构是否正确

请按照以下格式返回JSON：
{
    "score": 0.0-1.0,  // 1.0表示响应完全合理，0.0表示响应不合理
    "issues": ["响应问题描述"],
    "analysis": "详细分析说明"
}"""

        # Extract function calls and tool responses
        function_calls = self._extract_function_calls(dialog_data)
        tool_responses = self._extract_tool_responses(dialog_data)
        
        if not function_calls and not tool_responses:
            return {"score": 1.0, "issues": [], "analysis": "无工具调用，无需检查"}
            
        analysis_text = self._format_tool_calls_for_analysis(function_calls, tool_responses)
        user_prompt = f"""请检查以下工具调用和响应：

{analysis_text}

请返回检查结果："""

        try:
            response = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=512
            )
            
            result = json.loads(response.strip())
            
            # Validate result format
            if "score" not in result:
                return self._fallback_tool_response_check(dialog_data)
                
            return result
            
        except Exception as e:
            print(f"工具响应检查失败: {e}")
            return self._fallback_tool_response_check(dialog_data)
            
    def _format_dialog_for_analysis(self, dialog_data: Dict) -> str:
        """Format dialog for LLM analysis"""
        lines = []
        
        # Add API candidates
        api_candidates = dialog_data.get("api_candidates", [])
        if api_candidates:
            lines.append("可用API:")
            for api in api_candidates[:3]:  # Limit to 3 APIs
                lines.append(f"- {api.get('name', '')}: {api.get('description', '')}")
            lines.append("")
            
        # Add dialog turns
        turns = dialog_data.get("turns", [])
        for turn in turns:
            role = turn.get("role", "")
            content = turn.get("content", "")
            
            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"助手: {content}")
                
                # Add function calls if present
                function_calls = turn.get("function_calls", [])
                if function_calls:
                    lines.append("函数调用:")
                    for call in function_calls:
                        lines.append(f"  - {call.get('name', '')}({call.get('parameters', {})})")
                        
            elif role == "tool":
                lines.append(f"工具响应: {content}")
                
        return "\n".join(lines)
        
    def _extract_function_calls(self, dialog_data: Dict) -> List[Dict]:
        """Extract all function calls from dialog"""
        function_calls = []
        
        turns = dialog_data.get("turns", [])
        for turn in turns:
            if turn.get("role") == "assistant":
                calls = turn.get("function_calls", [])
                function_calls.extend(calls)
                
        return function_calls
        
    def _extract_tool_responses(self, dialog_data: Dict) -> List[Dict]:
        """Extract all tool responses from dialog"""
        tool_responses = []
        
        turns = dialog_data.get("turns", [])
        for turn in turns:
            if turn.get("role") == "tool":
                tool_responses.append({
                    "content": turn.get("content", ""),
                    "tool_response": turn.get("tool_response", {})
                })
                
        return tool_responses
        
    def _format_tool_calls_for_analysis(self, function_calls: List[Dict], tool_responses: List[Dict]) -> str:
        """Format tool calls and responses for analysis"""
        lines = []
        
        if function_calls:
            lines.append("函数调用:")
            for i, call in enumerate(function_calls):
                lines.append(f"{i+1}. {call.get('name', '')}({call.get('parameters', {})})")
                
        if tool_responses:
            lines.append("\n工具响应:")
            for i, response in enumerate(tool_responses):
                lines.append(f"{i+1}. {response.get('content', '')}")
                if response.get("tool_response"):
                    lines.append(f"   数据: {response['tool_response']}")
                    
        return "\n".join(lines)
        
    def _fallback_hallucination_check(self, dialog_data: Dict) -> Dict[str, Any]:
        """Fallback hallucination check using heuristics"""
        # Simple heuristic: check if function parameters are reasonable
        function_calls = self._extract_function_calls(dialog_data)
        
        issues = []
        for call in function_calls:
            params = call.get("parameters", {})
            for param_name, param_value in params.items():
                if isinstance(param_value, str) and len(param_value) > 50:
                    issues.append(f"参数 {param_name} 值过长，可能是编造的")
                    
        score = 1.0 - (len(issues) * 0.2)
        return {
            "detected": len(issues) > 0,
            "score": max(score, 0.0),
            "issues": issues,
            "analysis": "基于启发式规则的幻觉检测"
        }
        
    def _fallback_consistency_check(self, dialog_data: Dict) -> Dict[str, Any]:
        """Fallback consistency check using heuristics"""
        turns = dialog_data.get("turns", [])
        
        # Simple check: ensure assistant responds to user queries
        user_turns = [t for t in turns if t.get("role") == "user"]
        assistant_turns = [t for t in turns if t.get("role") == "assistant"]
        
        issues = []
        if len(assistant_turns) == 0 and len(user_turns) > 0:
            issues.append("用户有查询但助手没有回复")
            
        score = 0.8 if len(issues) == 0 else 0.5
        return {
            "score": score,
            "issues": issues,
            "analysis": "基于启发式规则的一致性检查"
        }
        
    def _fallback_tool_response_check(self, dialog_data: Dict) -> Dict[str, Any]:
        """Fallback tool response check using heuristics"""
        tool_responses = self._extract_tool_responses(dialog_data)
        
        issues = []
        for response in tool_responses:
            content = response.get("content", "")
            if "error" in content.lower() or "失败" in content:
                issues.append("工具执行出现错误")
                
        score = 0.8 if len(issues) == 0 else 0.6
        return {
            "score": score,
            "issues": issues,
            "analysis": "基于启发式规则的工具响应检查"
        }
