# Tool Self-Evolution Synthesis (TSS) Module

## 📖 Module Overview

Tool Self-Evolution Synthesis (TSS) is a core module of the ToolACE framework, responsible for automatically generating diverse, high-quality API definitions. This module simulates biological evolution to extract API domain knowledge from pre-training data and creates a comprehensive API pool through three steps: speciation, adaptation, and evolution.

## 🎯 Core Features

The TSS module supports:
- Nested parameter types (lists of lists, dictionaries of lists, etc.)
- Diverse data types and constraints
- Cross-domain API functionality coverage
- Self-evolution and continuous update mechanism

## 🏗️ Module Architecture

```
tss/
├── README.md                    # This document
├── __init__.py                 # Module initialization
├── speciation.py               # API context tree construction
├── adaptation.py               # Domain and diversity level specification
├── evolution.py                # API continuous improvement
└── api_pool.py                 # API pool management
```

## 🔄 Three-Step Evolution Process

### 1. Speciation
- **Goal**: Build hierarchical API context trees to guide synthesis
- **Input**: API-related documents from pre-training data
- **Process**: 
  - Extract API domains from technical manuals and documentation
  - Generate hierarchical structure of API functionalities
  - Create comprehensive context trees covering various applications
- **Output**: Hierarchical API context tree with nodes representing potential API functions

### 2. Adaptation
- **Goal**: Specify domain and diversity levels for each API
- **Process**:
  - Sample subtrees from API context tree
  - Obtain unique functionality combinations for each API
  - Control API complexity and specialization level
- **Diversity Control**:
  - Some APIs cover more nodes → more domain-specific capabilities
  - Some APIs contain single nodes → simple direct functions

### 3. Evolution
- **Goal**: Continuously improve APIs based on results and requirements
- **Process**:
  - Generate new APIs based on sampled subtrees and examples
  - Apply diversity metrics for mutations and improvements
  - Maintain API example buffer for iterations
- **Diversity Metrics**:
  - Add new functionalities or parameters
  - Include additional constraints
  - Mutate parameter types
  - Update return results

## 📁 File Details

### `speciation.py`
Core logic for building API context trees from pre-training data:

**Key Functions**:
- `APIContextTree`: Data structure for API context tree
- `extract_api_domains()`: Extract API domains from documents
- `build_context_tree()`: Build hierarchical context tree
- `get_api_functionalities()`: Get list of API functionalities

### `adaptation.py`
Handles domain adaptation and diversity level specification:

**Key Functions**:
- `DomainAdapter`: Domain adapter class
- `sample_subtree()`: Subtree sampling algorithm
- `assign_functionalities()`: Functionality assignment logic
- `calculate_diversity_level()`: Diversity level calculation

### `evolution.py`
Implements continuous API evolution mechanism:

**Key Functions**:
- `APIEvolver`: API evolution class
- `generate_api()`: Core API generation algorithm
- `apply_diversity_mutations()`: Apply diversity mutations
- `validate_api_definition()`: API definition validation

### `api_pool.py`
Manages the API pool:

**Key Functions**:
- `APIPool`: API pool manager class
- `add_api()`: Add API to pool
- `sample_apis()`: Sample APIs from pool
- `get_pool_statistics()`: Get pool statistics

## 🔧 Usage Example

```python
from toolace.tss import TSS
from toolace.tss.speciation import APIContextTree
from toolace.tss.adaptation import DomainAdapter
from toolace.tss.evolution import APIEvolver

# Initialize TSS module
tss = TSS(config_path="config/data_config.yaml")

# Build API context tree
context_tree = APIContextTree()
context_tree.build_from_pretraining_data("data/raw/pretraining_docs/")

# Domain adaptation
adapter = DomainAdapter(context_tree)
sampled_subtree = adapter.sample_subtree(diversity_level="medium")

# API evolution
evolver = APIEvolver()
new_api = evolver.generate_api(
    subtree=sampled_subtree,
    example_api=tss.api_pool.sample_example()
)

# Add to API pool
tss.api_pool.add_api(new_api)
```

## 📊 Output Format

Generated API definitions follow standard JSON Schema format:

```json
{
  "name": "get_weather_forecast",
  "description": "Get weather forecast for a specified location",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "Geographic location (city name or coordinates)"
      },
      "days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 14,
        "description": "Number of forecast days"
      },
      "include_hourly": {
        "type": "boolean",
        "description": "Whether to include hourly forecast"
      }
    },
    "required": ["location"]
  },
  "returns": {
    "type": "object",
    "description": "Weather forecast data"
  }
}
```

## 🎯 Design Principles

1. **Diversity First**: Ensure API diversity through self-evolution
2. **Quality Assurance**: Strict validation for API definition accuracy
3. **Extensibility**: Support for adding new API domains and functions
4. **Flexible Adaptation**: Adjust API complexity based on requirements

## 🔗 Integration with Other Modules

The API pool generated by TSS module is used by SDG module for dialogue generation, and the generated API definitions need to be validated by DLV module:

```
TSS (API Generation) → SDG (Dialog Generation) → DLV (Quality Verification)
```

## 🛠️ Configuration

Configure TSS parameters in `config/data_config.yaml`:

```yaml
tss:
  pretraining_data_path: "data/raw/pretraining_docs/"
  api_pool_size: 30000
  diversity_levels: ["low", "medium", "high"]
  evolution_iterations: 5
  context_tree_depth: 4
```