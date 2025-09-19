import re
import importlib
import json
from textwrap import dedent
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
from tenacity import RetryError

from ...utils.model_manager import generate


class AssistantAgent:
    """
    Assistant agent that processes user queries and generates appropriate responses
    """
    
    def __init__(self, model_key: str = "qwen3_32b", config: dict = None):
        self.model_key = model_key
        self.config = config
        self.conversation_history = []
        self.available_apis = []
        
    def initialize_conversation(self, api_candidates: List[Dict]):
        """
        Initialize conversation with available APIs
        
        Args:
            api_candidates: List of available API definitions
        """
        self.conversation_history = []
        self.available_apis = api_candidates

    def _format_apis_for_system(self) -> str:
        """Format APIs for system prompt"""
        api_lines = []
        for api in self.available_apis[:20]:  # Limit to 20 APIs
            name = api.get("name", "unknown")
            desc = api.get("description", "")
            params = api.get("parameters", {})
            
            param_desc = []
            if isinstance(params, dict) and "properties" in params:
                for param_name, param_info in params["properties"].items():
                    param_type = param_info.get("type", "any")
                    param_description = param_info.get("description", "")
                    param_desc.append(f"    - {param_name} ({param_type}): {param_description}")
            
            api_lines.append(f"- {name}: {desc}")
            if param_desc:
                api_lines.extend(param_desc)
                
        return "\n".join(api_lines)
        
    def _convert_apis_to_tools(self) -> List[Dict]:
        """Convert API definitions to OpenAI tools format"""
        tools = []
        for api in self.available_apis:
            tool = {
                "type": "function",
                "function": {
                    "name": api.get("name", ""),
                    "description": api.get("description", ""),
                    "parameters": api.get("parameters", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            tools.append(tool)
        return tools
        
    def _format_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Format tool calls from model response"""
        formatted_calls = []
        
        for call in tool_calls:
            if isinstance(call, dict):
                function_info = call.get("function", {})
                formatted_call = {
                    "name": function_info.get("name", ""),
                    "parameters": {}
                }
                
                # Parse arguments if they're in string format
                arguments = function_info.get("arguments", "{}")
                if isinstance(arguments, str):
                    try:
                        formatted_call["parameters"] = json.loads(arguments)
                    except:
                        formatted_call["parameters"] = {}
                else:
                    formatted_call["parameters"] = arguments
                    
                formatted_calls.append(formatted_call)
                
        return formatted_calls

    def react_step(self, subtask_conversation: List[Dict], api_candidates: List[Dict]) -> Dict[str, Any]:
        """
        Perform a single ReAct step: Think and Act based on current subtask context
        
        Args:
            subtask_conversation: Current subtask conversation history
            api_candidates: Available API definitions
            
        Returns:
            Assistant response with potential function calls
        """
        # Prepare system prompt for ReAct
        system_prompt = dedent(
            f"""你是一个AI助手，正在执行ReAct推理过程来帮助用户完成任务。

            可用工具：
            {self._format_apis_for_system_react(api_candidates)}

            ReAct推理步骤：
            1. **思考 (Think)**: 分析当前情况，确定下一步行动
            2. **行动 (Act)**: 如果需要，调用合适的工具；如果不需要工具，直接回答

            要求：
            - 仔细分析用户需求和当前上下文
            - 如果任务需要工具辅助，选择最合适的工具
            - 如果任务已完成或不需要工具，提供最终答案
            - 每次只关注当前任务，不要考虑其他任务"""
        )

        # Format conversation context
        # context_str = self._format_subtask_conversation(subtask_conversation)
        context_str = subtask_conversation
        
        user_prompt = f"""当前任务对话：
    {context_str}

    请根据上下文进行思考并决定下一步行动："""

        # Prepare tools
        # tools = self._convert_apis_to_tools_react(api_candidates)
        tools = api_candidates
        
        try:
            thinking_content, answer_content, tool_calls = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                tools=tools,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            )

            logger.info(
                f"assistant react_step:\n"
                f"[THINKING]: {thinking_content}\n\n"
                f"[ANSWER]: {answer_content}\n\n"
                f"[TOOL_CALLS]: {tool_calls}"
            )
            
            return {
                "role": "assistant",
                "think": thinking_content,
                "content": answer_content,
                "function_calls": tool_calls
            }
            
        except RetryError as e:
            # Handle retry failure case
            logger.error(f"ReAct step failed after multiple retries: {e}")
            raise RuntimeError(f"ReAct step generation failed: Model call still failed after multiple retries") from e
        except Exception as e:
            # Handle other exceptions
            logger.error(f"ReAct step generation failed: {e}")
            raise RuntimeError(f"ReAct step generation failed: {e}") from e
             
    def _format_apis_for_system_react(self, api_candidates: List[Dict]) -> str:
        """Format APIs for ReAct system prompt"""
        api_lines = []
        for api in api_candidates[:10]:  # Limit to 10 APIs for ReAct
            name = api.get("name", "unknown")
            desc = api.get("description", "")
            api_lines.append(f"- {name}: {desc}")
        return "\n".join(api_lines)