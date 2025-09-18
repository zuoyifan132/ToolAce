"""
Dual-Layer Verification (DLV) Module

This module implements the dual-layer verification system that ensures
the accuracy and reliability of synthesized function-calling data.
"""

from .rule_checker import RuleChecker
from .model_checker import ModelChecker
from .verification_rules import VerificationRules

__all__ = [
    'RuleChecker',
    'ModelChecker', 
    'VerificationRules',
    'DLV'
]

class DLV:
    """
    Dual-Layer Verification main class that orchestrates the verification
    process through rule-based and model-based checks.
    """
    
    def __init__(self, model_path: str = None, config: dict = None):
        """Initialize DLV with model and configuration"""
        self.model_path = model_path
        self.config = config or {}
        
        # Initialize verification components
        self.rule_checker = RuleChecker(self.config.get("rule_checker", {}))
        self.model_checker = ModelChecker(model_path, self.config.get("model_checker", {}))
        self.verification_rules = VerificationRules()
        
    def verify_dialog(self, dialog_data: dict) -> dict:
        """
        Verify a single dialog through the dual-layer system
        
        Args:
            dialog_data: Dialog data structure to verify
            
        Returns:
            Verification result with pass/fail status and details
        """
        # Step 1: Rule-based verification
        rule_result = self.rule_checker.verify(dialog_data)
        
        if not rule_result["passed"]:
            return {
                "dialog_id": dialog_data.get("dialog_id", "unknown"),
                "verification_status": "failed",
                "stage": "rule_check",
                "rule_check_result": rule_result,
                "model_check_result": None,
                "final_decision": "failed"
            }
            
        # Step 2: Model-based verification
        model_result = self.model_checker.verify(dialog_data)
        
        # Combine results
        overall_passed = rule_result["passed"] and model_result["passed"]
        
        return {
            "dialog_id": dialog_data.get("dialog_id", "unknown"),
            "verification_status": "passed" if overall_passed else "failed",
            "stage": "complete",
            "rule_check_result": rule_result,
            "model_check_result": model_result,
            "final_decision": "passed" if overall_passed else "failed"
        }
        
    def batch_verify(self, dialogs: list) -> list:
        """
        Verify multiple dialogs in batch
        
        Args:
            dialogs: List of dialog data structures
            
        Returns:
            List of verification results
        """
        results = []
        for dialog in dialogs:
            result = self.verify_dialog(dialog)
            results.append(result)
            
        return results
        
    def get_verification_statistics(self, results: list) -> dict:
        """Get statistics from verification results"""
        total = len(results)
        passed = sum(1 for r in results if r["final_decision"] == "passed")
        failed_rule = sum(1 for r in results if r["stage"] == "rule_check" and r["final_decision"] == "failed")
        failed_model = sum(1 for r in results if r["stage"] == "complete" and r["final_decision"] == "failed")
        
        return {
            "total_dialogs": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "failed_at_rule_check": failed_rule,
            "failed_at_model_check": failed_model,
            "rule_check_pass_rate": (total - failed_rule) / total if total > 0 else 0
        }
