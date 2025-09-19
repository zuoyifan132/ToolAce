"""
Self-Guided Dialog Generation (SDG) Module

This module implements multi-subtask dialog generation with ReAct loops.
Each dialog contains 1-N subtasks, and each subtask has a complete ReAct cycle.
"""

import json
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import List, Dict, Any, Optional

from loguru import logger
from .complexity_evaluator import ComplexityEvaluator
from .agents import UserAgent, AssistantAgent, ToolAgent
from ..utils.io_utils import save_to_json

__all__ = [
    'ComplexityEvaluator',
    'UserAgent',
    'AssistantAgent', 
    'ToolAgent',
    'SDG'
]

class SDG:
    """
    Multi-Subtask Dialog Generation with ReAct loops.
    Generates dialogs containing multiple subtasks, each with complete ReAct cycles.
    """

    def __init__(self, config: dict = None):
        """Initialize SDG with target model and configuration"""
        self.config = config or {}
        
        # Default config values
        self.default_config = {
            "min_subtasks": 1,
            "max_subtasks": 5,
            "max_react_steps": 5,
            "max_apis_per_dialog": 5,
            "batch_concurrency": 4,  # Number of concurrent tasks
            "batch_timeout": 300,    # Timeout in seconds
            "retry_attempts": 3      # Number of retry attempts
        }
        
        # Merge with user config
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value

        # Initialize components
        self.complexity_evaluator = ComplexityEvaluator()
        self.user_agent = UserAgent(
            model_key=self.config["user_model"], 
            config=config["agents"]["user_agent"]
        )
        self.assistant_agent = AssistantAgent(
            model_key=self.config["assistant_model"], 
            config=config["agents"]["assistant_agent"]
        )
        self.tool_agent = ToolAgent(
            model_key=self.config["tool_model"], 
            config=config["agents"]["tool_agent"]
        )

    def _convert_apis_to_tools_react(self, api_candidates: List[Dict]) -> List[Dict]:
        """Convert APIs to tools format for ReAct"""
        if self.config["assistant_model"] == "claude_3d7":
            tools = []
            for tool_desc in api_candidates:
                # Create a copy of the tool to avoid modifying original data
                tool = {}
                for k, v in tool_desc.items():
                    if k == "name":
                        # Normalize tool name
                        tool["name"] = self._normalize_tool_name(v)
                    elif k == "parameters":
                        # Convert parameter types and rename to input_schema
                        tool["input_schema"] = self._convert_type_to_json_schema(v)
                    elif k not in ["returns", "required"]:
                        tool[k] = v
                tools.append(tool)
            return tools
        elif self.config["assistant_model"] == "openai_gpt":
            tools = []
            for tool_desc in api_candidates:
                # Create a copy of the tool to avoid modifying original data
                function_def = {}
                
                # Convert name and description
                function_def["name"] = self._normalize_tool_name(tool_desc["name"])
                function_def["description"] = tool_desc.get("description", "")
                
                # Convert parameters
                if "parameters" in tool_desc:
                    params = tool_desc["parameters"]
                    if params["type"] == "dict":
                        function_def["parameters"] = {
                            "type": "object",
                            "properties": {},
                            "required": params.get("required", [])
                        }
                        
                        # Convert each parameter
                        for param_name, param_info in params.get("properties", {}).items():
                            param_schema = {}
                            
                            # Convert type
                            if param_info.get("type") in ["int", "float"]:
                                param_schema["type"] = "number"
                            elif param_info.get("type") == "dict":
                                param_schema["type"] = "object"
                            elif param_info.get("type") == "list":
                                param_schema["type"] = "array"
                            else:
                                param_schema["type"] = param_info.get("type", "string")
                            
                            # Copy other fields
                            for key in ["description", "default", "enum", "format"]:
                                if key in param_info:
                                    param_schema[key] = param_info[key]
                            
                            function_def["parameters"]["properties"][param_name] = param_schema
                
                # Wrap in OpenAI tool format
                tool = {
                    "type": "function",
                    "function": function_def
                }
                
                tools.append(tool)
            return tools
        else:
            raise NotImplementedError(f"Model {self.model_key} not supported")
        
    def _normalize_tool_name(self, name: str) -> str:
        """
        Normalize tool name to match pattern '^[a-zA-Z0-9_-]{1,128}$'
        
        Args:
            name: Original tool name
            
        Returns:
            Normalized tool name
        """
        # 1. Replace disallowed characters with underscores
        normalized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        
        # 2. Remove consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        
        # 3. Remove leading and trailing underscores
        normalized = normalized.strip('_-')
        
        # 4. Use default name if empty
        if not normalized:
            normalized = "tool"
        
        # 5. Limit length to 128 characters
        if len(normalized) > 128:
            normalized = normalized[:128]
        
        return normalized

    def _convert_type_to_json_schema(self, schema: Any) -> Any:
        """
        Convert Python type names to JSON Schema type names recursively
        
        Args:
            schema: Schema to convert
            
        Returns:
            Converted schema
        """
        if isinstance(schema, dict):
            converted = {}
            for key, value in schema.items():
                if key == "type":
                    # Convert type names
                    if value == "dict":
                        converted[key] = "object"
                    elif value in ["int", "float"]:
                        converted[key] = "number"
                    elif value == "list":
                        converted[key] = "array"
                    else:
                        converted[key] = value
                else:
                    # Recursively process nested structures
                    converted[key] = self._convert_type_to_json_schema(value)
            return converted
        elif isinstance(schema, list):
            # Process each element in the list
            return [self._convert_type_to_json_schema(item) for item in schema]
        else:
            # Return other types as is
            return schema

    def generate_multi_subtask_dialog(self, 
                                     api_candidates: list,
                                     num_subtasks: int = None,
                                     target_complexity: float = None,
                                     save_path: str = None) -> dict:
        """
        Generate a multi-subtask dialog with ReAct loops
        
        Args:
            api_candidates: List of API definitions to use
            num_subtasks: Number of subtasks (if None, randomly choose from config range)
            target_complexity: Target complexity score
            
        Returns:
            Complete dialog data structure with multiple subtasks
        """
        # Determine number of subtasks
        if num_subtasks is None:
            num_subtasks = random.randint(
                self.config["min_subtasks"], 
                self.config["max_subtasks"]
            )
        
        # Initialize global conversation history
        global_conversation = []
        subtask_breakdown = []

        # convert tool to standard format
        api_candidates = self._convert_apis_to_tools_react(api_candidates)
        
        logger.info(f"Sampled api_candidates:")
        logger.info(json.dumps(api_candidates, ensure_ascii=False, indent=2))

        # Generate each subtask
        for subtask_idx in range(num_subtasks):
            # Generate user query for this subtask (can see global context)
            user_query = self.user_agent.generate_subtask_query(
                subtask_idx, 
                global_conversation,
                api_candidates
            )
            
            # Generate single subtask with ReAct loop (independent context)
            subtask_dialog = self._generate_single_subtask(
                api_candidates,
                user_query
            )
            
            # Record subtask breakdown
            subtask_breakdown.append({
                "subtask_id": subtask_idx,
                "turns": len(subtask_dialog),
                "react_steps": self._count_react_steps(subtask_dialog),
                "tool_calls_used": self._count_tool_calls(subtask_dialog)
            })
            
            # Add to global conversation
            global_conversation.extend(subtask_dialog)
        
        # Build final dialog structure
        final_dialog = [{
            "dialog_id": f"multi_subtask_{hash(str(global_conversation)) % 1000000}",
            "dialog_type": "multi_subtask",
            "api_candidates": api_candidates,
            "global_conversation": global_conversation,
            "metadata": {
                "num_subtasks": num_subtasks,
                "total_turns": len(global_conversation),
                "subtask_breakdown": subtask_breakdown,
                "generation_config": self.config
            }
        }]
        
        # Evaluate complexity if needed
        if target_complexity:
            complexity_score = self.complexity_evaluator.evaluate_dialog_complexity(final_dialog)
            final_dialog["metadata"]["complexity_score"] = complexity_score

        # save the data to path
        save_to_json(data=final_dialog, file_name=save_path, mode="a")
            
        return final_dialog

    def _generate_single_subtask(self, api_candidates: list, initial_user_query: str) -> list:
        """
        Generate a single subtask with complete ReAct loop
        
        Args:
            api_candidates: Available API definitions
            initial_user_query: Initial user query for this subtask
            
        Returns:
            List of dialog turns for this subtask
        """
        # Initialize subtask conversation with user query
        subtask_conversation = [
            {"role": "user", "content": initial_user_query}
        ]
        
        max_react_steps = self.config["max_react_steps"]
        
        # ReAct loop for this subtask
        for step in range(max_react_steps):
            # Assistant generates response with potential tool calls
            assistant_response = self.assistant_agent.react_step(
                subtask_conversation,
                api_candidates
            )
            
            subtask_conversation.append(assistant_response)
            
            # Execute tool calls if present
            if assistant_response.get("function_calls") or step < self.config["mini_react_steps"]:
                tool_responses = []

                # no function but steps is less than mini_react_steps
                if not assistant_response.get("function_calls"):
                    tool_response = self.tool_agent.execute_single_function([], api_candidates, content=subtask_conversation)
                    tool_responses.append(tool_response)

                for call in assistant_response["function_calls"]:
                    tool_response = self.tool_agent.execute_single_function(call, api_candidates)
                    tool_responses.append(tool_response)
                
                # Add tool responses to conversation
                subtask_conversation.append({
                    "role": "tool",
                    "tool_responses": tool_responses
                })
            else:
                # No tool calls, ReAct loop ends
                break
            
        return subtask_conversation
        
    def _count_react_steps(self, dialog_turns: list) -> int:
        """Count the number of ReAct steps (assistant responses) in a dialog"""
        return sum(1 for turn in dialog_turns if turn.get("role") == "assistant")
        
    def _count_tool_calls(self, dialog_turns: list) -> int:
        """Count total number of tool calls in a dialog"""
        count = 0
        for turn in dialog_turns:
            if turn.get("role") == "assistant" and turn.get("function_calls"):
                count += len(turn["function_calls"])
        return count

    def batch_generate_dialogs(self, 
                              api_pool,
                              count: int,
                              save_path: str = None) -> list:
        """
        Generate multiple multi-subtask dialogs in batch (synchronous version)
        
        Args:
            api_pool: API pool to sample from
            count: Number of dialogs to generate
            
        Returns:
            List of generated multi-subtask dialogs
        """
        for i in range(count):
            # Sample APIs for this dialog
            apis_candidates_count = random.randint(
                self.config["min_apis_per_dialog"],
                self.config["max_apis_per_dialog"]
            )
            api_candidates = api_pool.sample_apis(apis_candidates_count)
            
            # Generate multi-subtask dialog
            try:
                dialog = self.generate_multi_subtask_dialog(
                    api_candidates=api_candidates,
                    save_path=save_path
                )
            except Exception as e:
                logger.error(f"Failed to generate data for index {i}, skipping due to {e}")
                continue
