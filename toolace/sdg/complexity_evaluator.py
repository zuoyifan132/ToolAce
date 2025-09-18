"""
Complexity Evaluator Module

This module implements the complexity evaluation system that uses the target LLM
to assess data complexity and establish appropriate complexity ranges.
"""

import torch
import numpy as np
import importlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

from ..utils.model_manager import generate

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
except ImportError:
    AutoTokenizer = None
    AutoModelForCausalLM = None


@dataclass
class ComplexityRange:
    """Represents the complexity range for the target LLM"""
    lower_bound: float
    upper_bound: float
    optimal_range: Tuple[float, float]
    confidence: float


@dataclass
class ComplexityFactors:
    """Factors that influence dialog complexity"""
    num_candidate_apis: int
    num_used_apis: int
    query_api_dissimilarity: float
    parameter_complexity: float
    dialog_length: int
    
    
class ComplexityEvaluator:
    """
    Evaluates dialog complexity using the target LLM as the evaluator.
    Uses loss values to measure how difficult a data sample is for the model.
    """
    
    def __init__(self, model_key: str = "sdg_evaluator_model"):
        self.model_key = model_key
        self.model = None
        self.tokenizer = None
        self.complexity_range = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.use_unified_interface = True  # Flag to use unified model interface
        
        # For backwards compatibility, still support direct model loading
        if hasattr(self, 'model_path') and self.model_path:
            self.use_unified_interface = False
            self.load_model()
            
    def load_model(self):
        """Load the target LLM for complexity evaluation"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            # Set pad token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logging.info(f"成功加载模型: {self.model_path}")
            
        except Exception as e:
            logging.error(f"加载模型失败: {e}")
            raise
            
    def calculate_loss(self, input_text: str, target_text: str) -> float:
        """
        Calculate the loss for a given input-target pair using the target LLM
        
        Args:
            input_text: Input query/context
            target_text: Target response
            
        Returns:
            Loss value (higher means more difficult)
        """
        if self.use_unified_interface:
            return self._calculate_loss_unified(input_text, target_text)
        else:
            return self._calculate_loss_direct(input_text, target_text)
            
    def _calculate_loss_unified(self, input_text: str, target_text: str) -> float:
        """Calculate loss using unified model interface"""
        try:
            # Use the model to evaluate complexity through a complexity assessment prompt
            system_prompt = """你是一个模型复杂度评估专家。请评估给定对话的复杂度，返回0.0到1.0之间的数值。

评估标准：
- 0.0-0.3: 简单对话，直接回答，无需工具调用
- 0.3-0.5: 中等复杂度，可能需要1-2个工具调用
- 0.5-0.7: 较复杂，需要多个工具调用或复杂推理
- 0.7-1.0: 非常复杂，需要复杂的工具链或高级推理

请只返回数值，不要其他内容。"""

            user_prompt = f"""请评估以下对话的复杂度：

输入内容：
{input_text[:1000]}

目标响应：
{target_text[:1000]}

复杂度分数："""

            response = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=50
            )
            
            # Extract numerical score
            import re
            score_match = re.search(r'0\.\d+|1\.0|0\.0', response)
            if score_match:
                return float(score_match.group())
            else:
                # Fallback to heuristic calculation
                return self._calculate_heuristic_complexity(input_text, target_text)
                
        except Exception as e:
            logging.error(f"统一接口复杂度计算失败: {e}")
            return self._calculate_heuristic_complexity(input_text, target_text)
            
    def _calculate_loss_direct(self, input_text: str, target_text: str) -> float:
        """Calculate loss using direct model access (original method)"""
        if not self.model or not self.tokenizer:
            raise ValueError("模型未加载，请先调用load_model()")
            
        try:
            # Combine input and target
            full_text = input_text + target_text
            
            # Tokenize
            inputs = self.tokenizer(
                full_text,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
                padding=True
            ).to(self.device)
            
            # Get input length for proper loss calculation
            input_ids = inputs["input_ids"]
            input_length = len(self.tokenizer(input_text)["input_ids"])
            
            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs, labels=input_ids)
                
            # Calculate loss only on the target portion
            shift_logits = outputs.logits[..., input_length-1:-1, :].contiguous()
            shift_labels = input_ids[..., input_length:].contiguous()
            
            # Calculate token-wise loss
            loss_fct = torch.nn.CrossEntropyLoss(reduction='none')
            token_losses = loss_fct(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1)
            )
            
            # Average loss over target tokens
            valid_tokens = (shift_labels != self.tokenizer.pad_token_id).sum()
            if valid_tokens > 0:
                avg_loss = token_losses.sum() / valid_tokens
                return avg_loss.item()
            else:
                return 0.0
                
        except Exception as e:
            logging.error(f"直接计算损失失败: {e}")
            return 0.0
            
    def _calculate_heuristic_complexity(self, input_text: str, target_text: str) -> float:
        """Fallback heuristic complexity calculation"""
        base_complexity = 0.3
        
        # Text length factor
        text_length = len(input_text) + len(target_text)
        length_factor = min(text_length / 1000.0, 0.3)
        
        # Function call factor
        function_call_count = target_text.count("function_calls")
        function_factor = min(function_call_count * 0.2, 0.4)
        
        return min(base_complexity + length_factor + function_factor, 1.0)
            
    def establish_complexity_range(self, sample_dialogs: List[Dict]) -> ComplexityRange:
        """
        Establish appropriate complexity range using sample dialogs
        
        Args:
            sample_dialogs: List of sample dialogs with varying complexity
            
        Returns:
            ComplexityRange object with bounds and optimal range
        """
        if not sample_dialogs:
            return ComplexityRange(0.0, 1.0, (0.3, 0.7), 0.5)
            
        losses = []
        correctly_generated = []
        
        for dialog in sample_dialogs:
            # Calculate loss for this dialog
            input_text = self._extract_input_from_dialog(dialog)
            target_text = self._extract_target_from_dialog(dialog)
            
            loss = self.calculate_loss(input_text, target_text)
            losses.append(loss)
            
            # Check if model can generate this correctly
            can_generate = self._check_generation_capability(dialog)
            correctly_generated.append(can_generate)
            
        # Sort by loss
        sorted_indices = np.argsort(losses)
        sorted_losses = [losses[i] for i in sorted_indices]
        sorted_generated = [correctly_generated[i] for i in sorted_indices]
        
        # Find bounds
        lower_bound = self._find_lower_bound(sorted_losses, sorted_generated)
        upper_bound = self._find_upper_bound(sorted_losses, sorted_generated)
        
        # Set optimal range (slightly above current capability)
        optimal_lower = lower_bound + (upper_bound - lower_bound) * 0.2
        optimal_upper = lower_bound + (upper_bound - lower_bound) * 0.7
        
        # Calculate confidence based on sample size and spread
        confidence = min(len(sample_dialogs) / 100.0, 1.0) * 0.8
        
        complexity_range = ComplexityRange(
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            optimal_range=(optimal_lower, optimal_upper),
            confidence=confidence
        )
        
        self.complexity_range = complexity_range
        return complexity_range
        
    def _find_lower_bound(self, sorted_losses: List[float], sorted_generated: List[bool]) -> float:
        """Find lower bound - losses of dialogs the model can already generate"""
        generated_indices = [i for i, can_gen in enumerate(sorted_generated) if can_gen]
        
        if generated_indices:
            # Use 75th percentile of successfully generated dialogs
            percentile_idx = int(len(generated_indices) * 0.75)
            if percentile_idx < len(generated_indices):
                return sorted_losses[generated_indices[percentile_idx]]
                
        # Fallback to 25th percentile of all losses
        return np.percentile(sorted_losses, 25) if sorted_losses else 0.0
        
    def _find_upper_bound(self, sorted_losses: List[float], sorted_generated: List[bool]) -> float:
        """Find upper bound - losses too high for the model to learn effectively"""
        # Use 90th percentile as upper bound
        return np.percentile(sorted_losses, 90) if sorted_losses else 1.0
        
    def evaluate_dialog_complexity(self, dialog: Dict) -> float:
        """
        Evaluate the complexity of a complete dialog
        
        Args:
            dialog: Dialog data structure
            
        Returns:
            Complexity score (0.0 - 1.0)
        """
        # Extract text for loss calculation
        input_text = self._extract_input_from_dialog(dialog)
        target_text = self._extract_target_from_dialog(dialog)
        
        # Calculate loss-based complexity
        loss = self.calculate_loss(input_text, target_text)
        
        # Analyze complexity factors
        factors = self._analyze_complexity_factors(dialog)
        
        # Combine loss and factors for final complexity score
        complexity_score = self._combine_complexity_measures(loss, factors)
        
        return complexity_score
        
    def _analyze_complexity_factors(self, dialog: Dict) -> ComplexityFactors:
        """Analyze factors that contribute to dialog complexity"""
        api_candidates = dialog.get("api_candidates", [])
        turns = dialog.get("turns", [])
        
        # Count used APIs
        used_apis = set()
        for turn in turns:
            if "function_calls" in turn:
                for call in turn["function_calls"]:
                    used_apis.add(call.get("name", ""))
                    
        # Calculate query-API dissimilarity
        dissimilarity = self._calculate_query_api_dissimilarity(dialog)
        
        # Calculate parameter complexity
        param_complexity = self._calculate_parameter_complexity(dialog)
        
        return ComplexityFactors(
            num_candidate_apis=len(api_candidates),
            num_used_apis=len(used_apis),
            query_api_dissimilarity=dissimilarity,
            parameter_complexity=param_complexity,
            dialog_length=len(turns)
        )
        
    def _calculate_query_api_dissimilarity(self, dialog: Dict) -> float:
        """Calculate dissimilarity between user query and API descriptions"""
        turns = dialog.get("turns", [])
        api_candidates = dialog.get("api_candidates", [])
        
        if not turns or not api_candidates:
            return 0.0
            
        # Get user queries
        user_queries = [turn["content"] for turn in turns if turn.get("role") == "user"]
        if not user_queries:
            return 0.0
            
        # Simple keyword-based dissimilarity (can be enhanced with embeddings)
        query_text = " ".join(user_queries).lower()
        
        similarities = []
        for api in api_candidates:
            api_desc = api.get("description", "").lower()
            api_name = api.get("name", "").lower()
            api_text = f"{api_name} {api_desc}"
            
            # Simple overlap measure
            query_words = set(query_text.split())
            api_words = set(api_text.split())
            
            if query_words and api_words:
                overlap = len(query_words & api_words) / len(query_words | api_words)
                similarities.append(overlap)
                
        # Return average dissimilarity
        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            return 1.0 - avg_similarity
        else:
            return 0.5
            
    def _calculate_parameter_complexity(self, dialog: Dict) -> float:
        """Calculate complexity based on function call parameters"""
        turns = dialog.get("turns", [])
        
        total_params = 0
        complex_types = 0
        
        for turn in turns:
            if "function_calls" in turn:
                for call in turn["function_calls"]:
                    params = call.get("parameters", {})
                    total_params += len(params)
                    
                    # Count complex parameter types
                    for value in params.values():
                        if isinstance(value, (dict, list)):
                            complex_types += 1
                            
        if total_params == 0:
            return 0.0
            
        return min(total_params * 0.1 + complex_types * 0.2, 1.0)
        
    def _combine_complexity_measures(self, loss: float, factors: ComplexityFactors) -> float:
        """Combine loss and factors into final complexity score"""
        # Normalize loss to 0-1 range using complexity range if available
        if self.complexity_range:
            loss_normalized = min(max(
                (loss - self.complexity_range.lower_bound) / 
                (self.complexity_range.upper_bound - self.complexity_range.lower_bound),
                0.0), 1.0)
        else:
            # Simple normalization
            loss_normalized = min(loss / 10.0, 1.0)
            
        # Factor-based complexity
        factor_score = (
            factors.num_candidate_apis * 0.1 +
            factors.num_used_apis * 0.2 +
            factors.query_api_dissimilarity * 0.3 +
            factors.parameter_complexity * 0.2 +
            min(factors.dialog_length * 0.1, 0.2)
        )
        
        # Combine with weights
        final_score = loss_normalized * 0.6 + factor_score * 0.4
        return min(final_score, 1.0)
        
    def _extract_input_from_dialog(self, dialog: Dict) -> str:
        """Extract input text from dialog for loss calculation"""
        turns = dialog.get("turns", [])
        
        # Extract user queries and context
        input_parts = []
        
        # Add API candidates as context
        api_candidates = dialog.get("api_candidates", [])
        if api_candidates:
            input_parts.append("可用工具:")
            for api in api_candidates[:3]:  # Limit to first 3 for length
                input_parts.append(f"- {api.get('name', '')}: {api.get('description', '')}")
                
        # Add user queries
        for turn in turns:
            if turn.get("role") == "user":
                input_parts.append(f"用户: {turn['content']}")
                
        return "\n".join(input_parts)
        
    def _extract_target_from_dialog(self, dialog: Dict) -> str:
        """Extract target text from dialog for loss calculation"""
        turns = dialog.get("turns", [])
        
        target_parts = []
        for turn in turns:
            if turn.get("role") == "assistant":
                target_parts.append(f"助手: {turn['content']}")
                
                # Add function calls if present
                if "function_calls" in turn:
                    for call in turn["function_calls"]:
                        target_parts.append(f"调用: {call.get('name', '')}({call.get('parameters', {})})")
                        
        return "\n".join(target_parts)
        
    def _check_generation_capability(self, dialog: Dict) -> bool:
        """Check if the model can currently generate this dialog correctly"""
        # This would involve actually generating with the model and checking quality
        # For now, return a simplified check based on complexity factors
        factors = self._analyze_complexity_factors(dialog)
        
        # Simple heuristic: model can handle if not too many factors are complex
        complexity_indicators = [
            factors.num_candidate_apis > 5,
            factors.num_used_apis > 3,
            factors.query_api_dissimilarity > 0.7,
            factors.parameter_complexity > 0.5,
            factors.dialog_length > 6
        ]
        
        # If more than 2 indicators are true, consider it too complex
        return sum(complexity_indicators) <= 2
        
    def get_complexity_guidance(self, current_complexity: float) -> Dict[str, Any]:
        """
        Get guidance on how to adjust complexity
        
        Args:
            current_complexity: Current complexity score
            
        Returns:
            Guidance dictionary with adjustment instructions
        """
        if not self.complexity_range:
            return {"action": "maintain", "reason": "无复杂度范围参考"}
            
        optimal_lower, optimal_upper = self.complexity_range.optimal_range
        
        if current_complexity < optimal_lower:
            return {
                "action": "increase",
                "reason": "当前复杂度过低",
                "target_complexity": optimal_lower + 0.1,
                "suggestions": [
                    "增加候选API数量",
                    "使用更多API",
                    "增加查询与API描述的差异性"
                ]
            }
        elif current_complexity > optimal_upper:
            return {
                "action": "decrease", 
                "reason": "当前复杂度过高",
                "target_complexity": optimal_upper - 0.1,
                "suggestions": [
                    "减少候选API数量",
                    "简化查询内容",
                    "减少参数复杂度"
                ]
            }
        else:
            return {
                "action": "maintain",
                "reason": "复杂度适中",
                "target_complexity": current_complexity,
                "suggestions": ["保持当前复杂度水平"]
            }
