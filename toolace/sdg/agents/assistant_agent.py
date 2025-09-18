import re
import importlib
import json
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
        
    # def process_user_query(self, user_query: str, dialog_type: str) -> Dict[str, Any]:
    #     """
    #     Process user query and generate appropriate response
        
    #     Args:
    #         user_query: User's query/message
    #         dialog_type: Expected dialog type
            
    #     Returns:
    #         Response dictionary containing content and function calls
    #     """
    #     # Add user query to history
    #     self.conversation_history.append({"role": "user", "content": user_query})
        
    #     # Generate response with model
    #     response = self._generate_response_with_actions(user_query, dialog_type)
        
    #     # Add assistant response to history
    #     self.conversation_history.append({
    #         "role": "assistant", 
    #         "think": response.get("think", ""),
    #         "content": response.get("content", ""),
    #         "function_calls": response.get("function_calls", [])
    #     })
        
    #     return response
        
    # def _generate_response_with_actions(self, user_query: str, dialog_type: str) -> Dict[str, Any]:
    #     """Generate response with appropriate actions"""
        
    #     if dialog_type == "non_tool":
    #         return self._generate_non_tool_response(user_query)
    #     else:
    #         return self._generate_tool_response(user_query, dialog_type)

    #     def _generate_tool_response(self, user_query: str, dialog_type: str) -> Dict[str, Any]:
#         """Generate response with function calls"""
#         system_prompt = f"""你是一个AI助手，需要根据用户需求调用相应的API来帮助用户。

# 可用的API列表：
# {self._format_apis_for_system()}

# 要求：
# 1. 仔细分析用户需求，选择最合适的API
# 2. 正确提取参数
# 3. 回复要自然友好
# 4. 确保API调用准确"""

#         # Prepare tools for function calling
#         tools = self._convert_apis_to_tools()
        
#         conversation_context = self._format_conversation_for_context()
#         user_prompt = f"""对话历史：
# {conversation_context}

# 用户当前查询：{user_query}

# 请根据用户需求调用相应的API并生成回复。"""

#         try:
#             thinking_content, answer_content, tool_calls = generate(
#                 model_key=self.model_key,
#                 system=system_prompt,
#                 user=user_prompt,
#                 tools=tools,
#                 temperature=self.config["temperature"],
#                 max_tokens=self.config["max_tokens"]
#             )
            
#             # Validate and format tool calls
#             formatted_tool_calls = self._format_tool_calls(tool_calls)
            
#             return {
#                 "think": thinking_content,
#                 "content": answer_content,
#                 "function_calls": formatted_tool_calls
#             }
            
#         except Exception as e:
#             print(f"工具响应生成失败: {e}")
#             return self._generate_fallback_tool_response(user_query)
            
#     def _generate_non_tool_response(self, user_query: str) -> Dict[str, Any]:
#         """Generate response without function calls"""
#         system_prompt = """你是一个知识渊博的AI助手，请直接回答用户的问题。

# 要求：
# 1. 提供准确、有用的信息
# 2. 回答要详细且易懂
# 3. 使用友好的语调
# 4. 如果是复杂问题，可以分点说明"""

#         conversation_context = self._format_conversation_for_context()
#         user_prompt = f"""对话历史：
# {conversation_context}

# 用户当前问题：{user_query}

# 请生成回复："""

#         try:
#             thinking_content, answer_content, tool_calls = generate(
#                 system=system_prompt,
#                 user=user_prompt,
#                 temperature=self.config["temperature"],
#                 max_tokens=self.config["max_tokens"]
#             )
            
#             return {
#                 "think": thinking_content,
#                 "content": answer_content,
#                 "function_calls": []
#             }
            
#         except Exception as e:
#             print(f"非工具响应生成失败: {e}")
#             return {
#                 "think": "无法生成思考过程",
#                 "content": "我理解您的问题，但目前无法提供详细回答。请您提供更多信息或换个方式询问。",
#                 "function_calls": []
#             }

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
        
    # def _format_conversation_for_context(self) -> str:
    #     """Format conversation history for context"""
    #     context_lines = []
    #     for turn in self.conversation_history:
    #         role = "用户" if turn["role"] == "user" else "助手"
    #         content = turn.get("content", "")
            
    #         # For assistant turns, include function calls info if present
    #         if turn["role"] == "assistant" and turn.get("function_calls"):
    #             func_names = [fc.get("name", "") for fc in turn["function_calls"]]
    #             if func_names:
    #                 content += f" [调用了: {', '.join(func_names)}]"
                    
    #         context_lines.append(f"{role}: {content}")
            
    #     return "\n".join(context_lines)
        
    # def _generate_fallback_tool_response(self, user_query: str) -> Dict[str, Any]:
    #     """Generate fallback tool response"""
    #     # Try to use the first available API
    #     if self.available_apis:
    #         api = self.available_apis[0]
    #         return {
    #             "think": "无法正常生成思考过程，使用备选方案",
    #             "content": f"我来帮您处理这个请求，让我调用{api.get('name', 'API')}来获取信息。",
    #             "function_calls": [{
    #                 "name": api.get("name", "unknown_api"),
    #                 "parameters": {}
    #             }]
    #         }
    #     else:
    #         return {
    #             "think": "无可用API",
    #             "content": "我理解您的需求，但目前无法调用相关工具来处理。",
    #             "function_calls": []
    #         }

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
        system_prompt = f"""你是一个AI助手，正在执行ReAct推理过程来帮助用户完成任务。

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

        # Format conversation context
        # context_str = self._format_subtask_conversation(subtask_conversation)
        context_str = subtask_conversation
        
        user_prompt = f"""当前任务对话：
    {context_str}

    请根据上下文进行思考并决定下一步行动："""

        # Prepare tools
        tools = self._convert_apis_to_tools_react(api_candidates)
        
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
            # 处理重试失败的情况
            logger.error(f"ReAct步骤在多次重试后失败: {e}")
            raise RuntimeError(f"ReAct步骤生成失败: 模型调用在重试多次后仍然失败") from e
        except Exception as e:
            # 处理其他异常
            logger.error(f"ReAct步骤生成失败: {e}")
            raise RuntimeError(f"ReAct步骤生成失败: {e}") from e
             
    def _format_apis_for_system_react(self, api_candidates: List[Dict]) -> str:
        """Format APIs for ReAct system prompt"""
        api_lines = []
        for api in api_candidates[:10]:  # Limit to 10 APIs for ReAct
            name = api.get("name", "unknown")
            desc = api.get("description", "")
            api_lines.append(f"- {name}: {desc}")
        return "\n".join(api_lines)
    
    def _normalize_tool_name(self, name: str) -> str:
        """
        Normalize tool name to match pattern '^[a-zA-Z0-9_-]{1,128}$'
        
        Args:
            name: Original tool name
            
        Returns:
            Normalized tool name
        """
        # 1. 替换不允许的字符为下划线
        normalized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        
        # 2. 移除连续的下划线
        normalized = re.sub(r'_+', '_', normalized)
        
        # 3. 移除开头和结尾的下划线
        normalized = normalized.strip('_-')
        
        # 4. 如果为空，使用默认名称
        if not normalized:
            normalized = "tool"
        
        # 5. 限制长度为128个字符
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
                    # 转换类型名称
                    if value == "dict":
                        converted[key] = "object"
                    elif value in ["int", "float"]:
                        converted[key] = "number"
                    elif value == "list":
                        converted[key] = "array"
                    else:
                        converted[key] = value
                else:
                    # 递归处理嵌套结构
                    converted[key] = self._convert_type_to_json_schema(value)
            return converted
        elif isinstance(schema, list):
            # 处理列表中的每个元素
            return [self._convert_type_to_json_schema(item) for item in schema]
        else:
            # 原样返回其他类型
            return schema

    def _convert_apis_to_tools_react(self, api_candidates: List[Dict]) -> List[Dict]:
        """Convert APIs to tools format for ReAct"""
        if self.model_key == "claude_3d7":
            tools = []
            for tool_desc in api_candidates:
                # 创建工具副本以避免修改原始数据
                tool = {}
                for k, v in tool_desc.items():
                    if k == "name":
                        # 规范化工具名称
                        tool["name"] = self._normalize_tool_name(v)
                    elif k == "parameters":
                        # 转换参数类型并重命名为input_schema
                        tool["input_schema"] = self._convert_type_to_json_schema(v)
                    elif k not in ["returns", "required"]:
                        tool[k] = v
                tools.append(tool)
            return tools
        else:
            return self._convert_apis_to_tools()  # Reuse existing method