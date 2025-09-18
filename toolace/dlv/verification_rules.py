"""
Verification Rules Module

This module defines all verification rules and standards used by the
Dual-Layer Verification (DLV) system.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class VerificationRule:
    """Definition of a verification rule"""
    rule_id: str
    name: str
    description: str
    severity: ErrorSeverity
    category: str
    enabled: bool = True


class VerificationRules:
    """
    Container for all verification rules used in the DLV system
    """
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.thresholds = self._initialize_thresholds()
        
    def _initialize_rules(self) -> Dict[str, VerificationRule]:
        """Initialize all verification rules"""
        rules = {}
        
        # API Definition Rules
        rules["API_001"] = VerificationRule(
            rule_id="API_001",
            name="API名称必需",
            description="API定义必须包含有效的name字段",
            severity=ErrorSeverity.CRITICAL,
            category="api_definition"
        )
        
        rules["API_002"] = VerificationRule(
            rule_id="API_002", 
            name="API描述必需",
            description="API定义必须包含description字段",
            severity=ErrorSeverity.WARNING,
            category="api_definition"
        )
        
        rules["API_003"] = VerificationRule(
            rule_id="API_003",
            name="参数结构完整",
            description="API参数定义必须包含完整的type和properties",
            severity=ErrorSeverity.ERROR,
            category="api_definition"
        )
        
        rules["API_004"] = VerificationRule(
            rule_id="API_004",
            name="返回值定义完整",
            description="API返回值定义必须包含type字段",
            severity=ErrorSeverity.WARNING,
            category="api_definition"
        )
        
        # Function Call Rules
        rules["FUNC_001"] = VerificationRule(
            rule_id="FUNC_001",
            name="函数名称有效",
            description="函数调用必须使用有效的API名称",
            severity=ErrorSeverity.CRITICAL,
            category="function_call"
        )
        
        rules["FUNC_002"] = VerificationRule(
            rule_id="FUNC_002",
            name="必需参数完整",
            description="函数调用必须包含所有必需参数",
            severity=ErrorSeverity.CRITICAL,
            category="function_call"
        )
        
        rules["FUNC_003"] = VerificationRule(
            rule_id="FUNC_003",
            name="参数类型正确",
            description="函数调用参数类型必须符合API定义",
            severity=ErrorSeverity.ERROR,
            category="function_call"
        )
        
        rules["FUNC_004"] = VerificationRule(
            rule_id="FUNC_004",
            name="参数格式有效",
            description="函数调用参数格式必须符合约束条件",
            severity=ErrorSeverity.ERROR,
            category="function_call"
        )
        
        # Dialog Structure Rules
        rules["DIALOG_001"] = VerificationRule(
            rule_id="DIALOG_001",
            name="对话非空",
            description="对话必须包含至少一个有效轮次",
            severity=ErrorSeverity.CRITICAL,
            category="dialog_structure"
        )
        
        rules["DIALOG_002"] = VerificationRule(
            rule_id="DIALOG_002",
            name="轮次结构完整",
            description="每个对话轮次必须包含role和content字段",
            severity=ErrorSeverity.CRITICAL,
            category="dialog_structure"
        )
        
        rules["DIALOG_003"] = VerificationRule(
            rule_id="DIALOG_003",
            name="角色定义有效",
            description="对话角色必须是user、assistant或tool之一",
            severity=ErrorSeverity.ERROR,
            category="dialog_structure"
        )
        
        rules["DIALOG_004"] = VerificationRule(
            rule_id="DIALOG_004",
            name="内容非空",
            description="对话内容不能为空",
            severity=ErrorSeverity.ERROR,
            category="dialog_structure"
        )
        
        rules["DIALOG_005"] = VerificationRule(
            rule_id="DIALOG_005",
            name="对话流程合理",
            description="对话流程应该自然合理",
            severity=ErrorSeverity.WARNING,
            category="dialog_structure"
        )
        
        # Data Consistency Rules
        rules["CONSIST_001"] = VerificationRule(
            rule_id="CONSIST_001",
            name="必需字段完整",
            description="数据样本必须包含所有必需字段",
            severity=ErrorSeverity.CRITICAL,
            category="data_consistency"
        )
        
        rules["CONSIST_002"] = VerificationRule(
            rule_id="CONSIST_002",
            name="对话类型一致",
            description="声明的对话类型应与实际内容一致",
            severity=ErrorSeverity.WARNING,
            category="data_consistency"
        )
        
        rules["CONSIST_003"] = VerificationRule(
            rule_id="CONSIST_003",
            name="API使用合理",
            description="应合理使用可用的API",
            severity=ErrorSeverity.INFO,
            category="data_consistency"
        )
        
        # Content Quality Rules (for model checker)
        rules["QUALITY_001"] = VerificationRule(
            rule_id="QUALITY_001",
            name="无幻觉内容",
            description="函数调用参数不应包含编造的内容",
            severity=ErrorSeverity.ERROR,
            category="content_quality"
        )
        
        rules["QUALITY_002"] = VerificationRule(
            rule_id="QUALITY_002",
            name="响应一致性",
            description="助手响应应与用户请求一致",
            severity=ErrorSeverity.ERROR,
            category="content_quality"
        )
        
        rules["QUALITY_003"] = VerificationRule(
            rule_id="QUALITY_003",
            name="工具响应合理",
            description="工具响应应符合API定义且合理",
            severity=ErrorSeverity.WARNING,
            category="content_quality"
        )
        
        return rules
        
    def _initialize_thresholds(self) -> Dict[str, Any]:
        """Initialize verification thresholds"""
        return {
            # Score thresholds
            "hallucination_threshold": 0.3,    # Below this score indicates hallucination
            "consistency_threshold": 0.7,      # Minimum consistency score
            "tool_response_threshold": 0.6,    # Minimum tool response quality
            "overall_quality_threshold": 0.75, # Minimum overall quality
            
            # Count thresholds
            "max_critical_errors": 0,          # Maximum critical errors allowed
            "max_errors": 2,                   # Maximum errors allowed
            "max_warnings": 5,                 # Maximum warnings before flagging
            
            # Length thresholds
            "min_dialog_turns": 2,             # Minimum dialog turns
            "max_dialog_turns": 10,            # Maximum dialog turns
            "min_content_length": 5,           # Minimum content length
            "max_content_length": 2000,        # Maximum content length
            
            # Complexity thresholds
            "min_complexity_score": 0.1,       # Minimum complexity
            "max_complexity_score": 0.9,       # Maximum complexity
            
            # API usage thresholds
            "min_api_usage_rate": 0.1,         # Minimum API usage rate for tool dialogs
            "max_unused_apis": 3,              # Maximum unused APIs
        }
        
    def get_rule(self, rule_id: str) -> VerificationRule:
        """Get a specific rule by ID"""
        return self.rules.get(rule_id)
        
    def get_rules_by_category(self, category: str) -> List[VerificationRule]:
        """Get all rules in a specific category"""
        return [rule for rule in self.rules.values() if rule.category == category]
        
    def get_enabled_rules(self) -> List[VerificationRule]:
        """Get all enabled rules"""
        return [rule for rule in self.rules.values() if rule.enabled]
        
    def get_threshold(self, key: str) -> Any:
        """Get a specific threshold value"""
        return self.thresholds.get(key)
        
    def update_threshold(self, key: str, value: Any):
        """Update a threshold value"""
        self.thresholds[key] = value
        
    def enable_rule(self, rule_id: str):
        """Enable a specific rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            
    def disable_rule(self, rule_id: str):
        """Disable a specific rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            
    def get_rule_categories(self) -> List[str]:
        """Get all rule categories"""
        categories = set(rule.category for rule in self.rules.values())
        return sorted(list(categories))
        
    def get_severity_levels(self) -> List[str]:
        """Get all severity levels"""
        return [severity.value for severity in ErrorSeverity]
        
    def validate_error_counts(self, errors: List[str], warnings: List[str]) -> bool:
        """
        Validate if error and warning counts are within acceptable thresholds
        
        Args:
            errors: List of error messages
            warnings: List of warning messages
            
        Returns:
            True if counts are acceptable, False otherwise
        """
        # Count by severity (simplified - in real implementation would parse severity from messages)
        critical_count = len([e for e in errors if "critical" in e.lower() or "必须" in e])
        error_count = len(errors) - critical_count
        warning_count = len(warnings)
        
        return (
            critical_count <= self.thresholds["max_critical_errors"] and
            error_count <= self.thresholds["max_errors"] and
            warning_count <= self.thresholds["max_warnings"]
        )
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for DLV system"""
        return {
            "rule_checker": {
                "strict_mode": True,
                "error_tolerance": 0,
                "checks": {
                    "api_definition_clarity": True,
                    "function_call_executability": True,
                    "dialog_correctness": True,
                    "data_sample_consistency": True,
                    "parameter_format_validation": True
                }
            },
            "model_checker": {
                "thresholds": self.thresholds.copy(),
                "expert_agents": {
                    "hallucination_detector": {"enabled": True, "weight": 0.4},
                    "consistency_validator": {"enabled": True, "weight": 0.4},
                    "tool_response_checker": {"enabled": True, "weight": 0.2}
                }
            }
        }
        
    def export_rules(self) -> Dict[str, Any]:
        """Export all rules to a dictionary"""
        return {
            "rules": {
                rule_id: {
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity.value,
                    "category": rule.category,
                    "enabled": rule.enabled
                }
                for rule_id, rule in self.rules.items()
            },
            "thresholds": self.thresholds.copy(),
            "categories": self.get_rule_categories(),
            "severity_levels": self.get_severity_levels()
        }
        
    def import_rules(self, rules_data: Dict[str, Any]):
        """Import rules from a dictionary"""
        if "thresholds" in rules_data:
            self.thresholds.update(rules_data["thresholds"])
            
        if "rules" in rules_data:
            for rule_id, rule_data in rules_data["rules"].items():
                if rule_id in self.rules:
                    # Update existing rule
                    rule = self.rules[rule_id]
                    rule.enabled = rule_data.get("enabled", rule.enabled)
                    # Other fields are typically not updated to maintain consistency
