# Dual-Layer Verification (DLV) Module

## 📖 Module Overview

Dual-Layer Verification (DLV) is the quality assurance module of the ToolACE framework. Through a dual-layer verification system consisting of rule checker and model checker, it ensures the accuracy and reliability of synthesized data. This module serves as the final quality gate for function calling data, ensuring training data executability and consistency.

## 🎯 Core Features

- **Dual-Layer Architecture**: Combines rule and model checking for comprehensive data quality verification
- **Automated Verification**: Automated quality checking process without manual intervention
- **Multi-Dimensional Checks**: Covers syntax, semantics, consistency, executability, and more
- **Configurable Rules**: Supports custom validation rules and thresholds
- **Expert Supervision**: Final supervision of verification results by human experts

## 🏗️ Module Architecture

```
dlv/
├── README.md                    # This document
├── __init__.py                 # Module initialization
├── rule_checker.py            # Rule checker implementation
├── model_checker.py           # Model checker implementation
└── verification_rules.py      # Verification rules definition
```

## 🔍 Dual-Layer Verification System

### Layer 1: Rule Verification
Structured and syntax checking based on predefined rules:

**Check Dimensions**:
1. **API Definition Clarity**: API name, description, parameter completeness
2. **Function Call Executability**: Parameter format, type, constraint validation
3. **Dialog Correctness**: Dialog flow, role consistency
4. **Data Sample Consistency**: Internal logic consistency check

**Verification Process**:
- API name matches tool list
- Required parameter completeness check
- Parameter format and pattern validation
- Efficiency validation without actual execution

### Layer 2: Model Verification
Semantic and content quality checking using LLM:

**Check Dimensions**:
1. **Hallucination Detection**: Identify fabricated parameter values
2. **Consistency Validation**: Response consistency with user tasks
3. **Tool Response Check**: Reasonability of simulated tool responses

**Expert Agents**:
- **Hallucination Detection Expert**: Identify fabricated parameter values
- **Consistency Validation Expert**: Check dialogue content consistency
- **Tool Response Expert**: Validate API response reasonability

## 📁 File Details

### `rule_checker.py`
Implements first-layer rule-based verification:

**Key Functions**:
- `RuleChecker`: Main rule checker class
- `validate_api_definition()`: API definition validation
- `validate_function_call()`: Function call validation
- `validate_dialog_structure()`: Dialog structure validation

### `model_checker.py`
Implements second-layer model-based verification:

**Key Functions**:
- `ModelChecker`: Main model checker class
- `detect_hallucination()`: Hallucination detection
- `verify_consistency()`: Consistency verification
- `check_tool_response()`: Tool response checking

### `verification_rules.py`
Defines all verification rules and standards:

**Rule Categories**:
- Structure rules (syntax, format)
- Content rules (semantics, logic)
- Quality rules (completeness, accuracy)

## 🔧 Usage Example

```python
from toolace.dlv import DLV
from toolace.dlv.rule_checker import RuleChecker
from toolace.dlv.model_checker import ModelChecker

# Initialize DLV module
dlv = DLV(model_path="models/verification-llm")

# Verify single dialog
dialog_data = {
    "turns": [...],
    "function_calls": [...],
    "api_candidates": [...]
}

verification_result = dlv.verify_dialog(dialog_data)

if verification_result.is_valid:
    print("Dialog passed verification")
else:
    print(f"Verification failed: {verification_result.errors}")

# Batch verification
dialogs = [...]
results = dlv.batch_verify(dialogs)
valid_dialogs = [d for d, r in zip(dialogs, results) if r.is_valid]
```

## 📊 Verification Rules Detail

### API Definition Clarity Check
```python
def validate_api_definition(api_def):
    checks = [
        api_def.get("name") is not None,
        api_def.get("description") is not None,
        api_def.get("parameters") is not None,
        isinstance(api_def.get("parameters"), dict)
    ]
    return all(checks)
```

### Function Call Executability Check
```python
def validate_function_call(call, api_list):
    # 1. API name matching
    api_names = [api["name"] for api in api_list]
    if call["name"] not in api_names:
        return False
        
    # 2. Required parameter check
    api_def = find_api_by_name(call["name"], api_list)
    required_params = api_def["parameters"].get("required", [])
    provided_params = call.get("parameters", {}).keys()
    
    if not all(param in provided_params for param in required_params):
        return False
        
    # 3. Parameter format validation
    return validate_parameter_formats(call["parameters"], api_def)
```

## 📋 Verification Report Format

```json
{
  "dialog_id": "dialog_001",
  "verification_status": "passed/failed",
  "rule_check_result": {
    "passed": true,
    "errors": [],
    "warnings": ["Parameter description could be more detailed"]
  },
  "model_check_result": {
    "hallucination_score": 0.1,
    "consistency_score": 0.9,
    "tool_response_score": 0.85,
    "overall_score": 0.85
  },
  "human_review": {
    "required": false,
    "status": "not_reviewed",
    "comments": ""
  },
  "final_decision": "passed",
  "processing_time": 5.2
}
```

## 🛠️ Configuration

Configure DLV parameters in `config/data_config.yaml`:

```yaml
dlv:
  rule_checker:
    strict_mode: true
    custom_rules_path: "rules/custom_rules.yaml"
    error_tolerance: 0
    
  model_checker:
    model_path: "models/verification-llm"
    hallucination_threshold: 0.3
    consistency_threshold: 0.7
    batch_size: 16
    
  human_review:
    sampling_rate: 0.05  # 5% sampling for human review
    priority_errors: ["hallucination", "inconsistency"]
    
  output:
    save_reports: true
    report_path: "data/verification_reports/"
    save_failed_cases: true
```

## 🔗 Integration with Other Modules

DLV module is the final stage in the data generation pipeline:

```
TSS (API Generation) → SDG (Dialog Generation) → DLV (Quality Verification) → Output Data
```

Verified data is saved to `data/generated/verified/` directory for model training use.