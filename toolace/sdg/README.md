# Self-Guided Dialog Generation (SDG) Module

## 📖 Module Overview

Self-Guided Dialog Generation (SDG) is a core module of the ToolACE framework, responsible for generating function calling dialogue data suitable for target LLM capabilities. The module combines a complexity evaluator with a multi-agent generator to ensure generated dialogue data has appropriate complexity and effectively fills model capability gaps.

## 🎯 Core Features

- **Adaptive Complexity**: Dynamically adjust dialogue complexity based on target LLM capabilities
- **Multi-Agent Collaboration**: Generate dialogues through user, assistant, and tool agent role-playing
- **Multi-Type Support**: Generate single, parallel, dependent, and non-tool usage dialogues
- **Quality Assurance**: Multi-instance consistency checks ensure response quality
- **Structured Thinking**: Thought process specifically designed for function calling

## 🏗️ Module Architecture

```
sdg/
├── README.md                    # This document
├── __init__.py                 # Module initialization
├── complexity_evaluator.py     # Complexity evaluator
├── agents/                     # Agent implementations
│   ├── __init__.py
│   ├── user_agent.py          # User agent implementation
│   ├── assistant_agent.py     # Assistant agent implementation
│   └── tool_agent.py          # Tool agent implementation
```

## 🔄 Workflow

### 1. Complexity Evaluation
Uses target LLM as evaluator to calculate data sample complexity:

**Complexity Formula**:
```
H_M(x, y) = -1/n_y * Σ(i=1 to n_y) log p(t_i | x, t_1, ..., t_{i-1})
```

**Complexity Factors**:
- Number of candidate APIs - Selection difficulty
- Number of APIs used - Query complexity
- Query-API description similarity - Reasoning difficulty

### 2. Multi-Agent Dialog Generation
Generate four types of dialogues through three agent collaboration:

**Agent Roles**:
- **User Agent**: Initiates requests, provides additional information
- **Assistant Agent**: Processes queries, calls APIs, summarizes results
- **Tool Agent**: Executes APIs, returns simulated results

**Dialog Types**:
- **Single Function Call**: Simple direct API calls
- **Parallel Function Calls**: Multiple simultaneous API calls
- **Dependent Function Calls**: Sequential API calls based on previous results
- **Non-Tool Usage**: Dialogues without API calls

### 3. Self-Guided Complication
Dynamically adjust dialogues based on complexity evaluation:

- **Too Simple**: Guide user agent to generate more complex queries
- **Too Complex**: Guide user agent to simplify queries
- **Appropriate Complexity**: Maintain current complexity level

## 📁 File Details

### `complexity_evaluator.py`
Core logic for complexity evaluation:

**Key Functions**:
- `ComplexityEvaluator`: Main complexity evaluator class
- `calculate_loss()`: Calculate sample loss value
- `establish_complexity_range()`: Establish complexity range
- `analyze_complexity_factors()`: Analyze complexity factors

### `agents/user_agent.py`
User agent implementation:

**Key Functions**:
- Generate initial query requests
- Respond to assistant inquiries
- Implement complication strategies
- Provide additional information and clarification

### `agents/assistant_agent.py`
Assistant agent implementation:

**Key Functions**:
- Analyze user query intent
- Select and call appropriate APIs
- Process API return results
- Generate final responses

### `agents/tool_agent.py`
Tool agent implementation:

**Key Functions**:
- Parse API call parameters
- Simulate API execution process
- Generate return results conforming to API definitions
- Handle exceptions and error cases

## 🔧 Usage Example

```python
from toolace.sdg import SDG
from toolace.sdg.complexity_evaluator import ComplexityEvaluator
from toolace.sdg.agents import UserAgent, AssistantAgent, ToolAgent

# Initialize SDG module
sdg = SDG(target_model_path="models/llama3.1-8b")

# Set API candidates
api_candidates = api_pool.sample_apis(count=5)

# Generate dialogue
dialog = sdg.generate_dialog(
    api_candidates=api_candidates,
    dialog_type="parallel",
    target_turns=4
)

# Output dialogue
for turn in dialog.turns:
    print(f"{turn.role}: {turn.content}")
```

## 📊 Output Format

Generated dialogue data uses standardized JSON format:

```json
{
  "dialog_id": "dialog_001",
  "dialog_type": "parallel",
  "api_candidates": [...],
  "turns": [
    {
      "role": "user",
      "content": "I want to check both Beijing weather and stock prices",
      "turn_id": 1
    },
    {
      "role": "assistant", 
      "content": "I'll help you get both pieces of information...",
      "function_calls": [
        {
          "name": "get_weather",
          "parameters": {"location": "Beijing"}
        },
        {
          "name": "get_stock_price", 
          "parameters": {"symbol": "000001"}
        }
      ],
      "turn_id": 2
    }
  ],
  "complexity_score": 0.65,
  "quality_metrics": {
    "consistency_score": 0.9,
    "completeness_score": 0.85
  }
}
```

## 🎯 Quality Assurance

### Multi-Instance Consistency Check
- Generate multiple candidate responses
- Check decision consistency
- Select responses with highest consistency

### Structured Thinking Process
```
1. Understand user query
2. Analyze required functionality
3. Select appropriate APIs
4. Plan call sequence
5. Execute and process results
```

### Error Handling and Retry
- Regenerate on parameter validation failure
- Automatic retry on API call errors
- Regenerate on substandard response quality

## 🔗 Integration with Other Modules

SDG module receives API pool from TSS, and generated dialogue data is sent to DLV module for validation:

```
TSS (API Pool) → SDG (Dialog Generation) → DLV (Quality Verification)
```

## 🛠️ Configuration

Configure SDG parameters in `config/data_config.yaml`:

```yaml
sdg:
  target_model_path: "models/llama3.1-8b"
  max_dialog_turns: 6
  complexity_range: [0.3, 0.8]
  consistency_threshold: 0.8
  dialog_types:
    - "single"
    - "parallel" 
    - "dependent"
    - "non_tool"
  agent_configs:
    user_agent:
      temperature: 0.8
      max_retries: 3
    assistant_agent:
      temperature: 0.7
      thinking_steps: 5
    tool_agent:
      simulation_mode: "realistic"
```