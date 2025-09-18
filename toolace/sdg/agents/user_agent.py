"""
User Agent Module

This module implements the user agent that generates user queries and responses
in the multi-agent dialog generation system.
"""
import re 
import random
import json
import importlib
from typing import Dict, List, Optional, Any

from loguru import logger

from ...utils.model_manager import generate


class UserAgent:
    """
    User agent that simulates user behavior in dialog generation
    """
    
    def __init__(self, model_key: str = "qwen3_32b", config: dict = None):
        self.model_key = model_key
        self.config = config or {}
        self.conversation_history = []
        self.current_apis = []
        self.complexity_guidance = None
        
    # def initialize_conversation(self, api_candidates: List[Dict], dialog_type: str):
    #     """
    #     Initialize a new conversation context
        
    #     Args:
    #         api_candidates: Available APIs for this conversation
    #         dialog_type: Type of dialog to generate
    #     """
    #     self.conversation_history = []
    #     self.current_apis = api_candidates
    #     self.dialog_type = dialog_type

    # def _extract_json_from_response(self, response: str) -> Optional[Dict]:
    #     """
    #     Extract JSON from response, handling both raw JSON and JSON in code blocks
        
    #     Args:
    #         response: The response string that may contain JSON
            
    #     Returns:
    #         Parsed JSON as dict or None if extraction fails
    #     """
    #     # First try to find JSON in code block
    #     json_block_pattern = r'```json\s*([\s\S]*?)\s*```'
    #     match = re.search(json_block_pattern, response)
        
    #     if match:
    #         json_str = match.group(1).strip()
    #     else:
    #         # Try to find raw JSON
    #         json_str = response.strip()
            
    #     try:
    #         return json.loads(json_str)
    #     except json.JSONDecodeError:
    #         # Try to find JSON-like structure in the text
    #         json_pattern = r'\{[^{}]*\}'
    #         matches = re.findall(json_pattern, response)
    #         for match in matches:
    #             try:
    #                 return json.loads(match)
    #             except json.JSONDecodeError:
    #                 continue
        
    #     return None
        
#     def generate_initial_query(self, api_candidates: List[Dict], dialog_type: str) -> str:
#         """
#         Generate the initial user query that starts the conversation
        
#         Args:
#             api_candidates: Available APIs
#             dialog_type: Type of dialog (single/parallel/dependent/non_tool)
            
#         Returns:
#             Initial user query string
#         """
#         system_prompt = f"""你是一个真实的用户，需要根据可用的API生成自然的查询请求。

# 对话类型：{dialog_type}
# - single: 需要单个API调用的查询
# - parallel: 需要同时调用多个API的查询  
# - dependent: 需要依赖调用多个API的查询
# - non_tool: 不需要调用API的一般性问题

# 要求：
# 1. 生成自然、真实的用户查询
# 2. 查询应该符合指定的对话类型
# 3. 查询内容要与可用API相关但不要过于明显
# 4. 使用日常口语化的表达
# 5. 必须返回JSON格式，格式如下：

# ```json
# {{
#     "query": "用户的查询内容",
#     "intent": "查询意图简述",
#     "expected_apis": ["期望使用的API名称列表"]
# }}
# ```"""

#         # Format API information
#         api_info = self._format_apis_for_prompt(api_candidates)
        
#         user_prompt = f"""可用API信息：
# {api_info}

# 请生成一个{dialog_type}类型的用户查询，返回JSON格式："""

#         try:
#             thinking_content, answer_content, tool_calls = generate(
#                 model_key=self.model_key,
#                 system_prompt=system_prompt,
#                 user_prompt=user_prompt,
#                 temperature=self.config["temperature"],
#                 max_tokens=self.config["max_tokens"]
#             )
            
#             # Parse JSON response
#             try:
#                 result = self._extract_json_from_response(answer_content)
#                 query = result.get("query", "")
#                 if query:
#                     self.conversation_history.append({"role": "user", "content": query})
#                     return query
#             except json.JSONDecodeError:
#                 # Fallback: extract query from text if JSON parsing fails
#                 if "query" in answer_content:
#                     import re
#                     match = re.search(r'"query":\s*"([^"]+)"', answer_content)
#                     if match:
#                         query = match.group(1)
#                         self.conversation_history.append({"role": "user", "content": query})
#                         return query
            
#             return self._generate_fallback_query(api_candidates, dialog_type)
            
#         except Exception as e:
#             print(f"用户代理查询生成失败: {e}")
#             return self._generate_fallback_query(api_candidates, dialog_type)

#     def generate_response(self, assistant_message: str, complexity_guidance: Optional[Dict] = None) -> Optional[str]:
#         """
#         Generate user response to assistant message
        
#         Args:
#             assistant_message: Assistant's previous message
#             complexity_guidance: Guidance for adjusting complexity
            
#         Returns:
#             User response or None if conversation should end
#         """
#         self.complexity_guidance = complexity_guidance
        
#         # Decide whether to continue conversation
#         if self._should_end_conversation():
#             return None
            
#         # Generate response based on assistant message
#         system_prompt = """你是一个真实的用户，正在与AI助手对话。请根据助手的回复生成自然的用户响应。

# 响应类型：
# 1. 如果助手询问澄清问题，提供具体信息
# 2. 如果助手提供了结果，可以表示感谢或提出进一步问题
# 3. 如果助手的回复不完整，可以要求更多信息
# 4. 保持对话的自然流程

# 要求：
# 1. 使用自然、口语化的表达
# 2. 响应要简洁且相关
# 3. 必须返回JSON格式，格式如下：

# ```json
# {
#     "response": "用户的回复内容",
#     "continue": true/false,  // 是否继续对话
#     "satisfaction": "satisfied/partial/unsatisfied",  // 满意度
#     "follow_up": "后续需求说明（可选）"
# }
# ```"""

#         # Apply complexity guidance if provided
#         if complexity_guidance:
#             system_prompt += f"\n\n复杂度指导：{complexity_guidance.get('reason', '')}"
#             if complexity_guidance.get('action') == 'increase':
#                 system_prompt += "\n请生成更复杂的查询，比如增加额外要求或约束条件。"
#             elif complexity_guidance.get('action') == 'decrease':
#                 system_prompt += "\n请生成更简单直接的回复。"

#         conversation_context = self.conversation_history
#         user_prompt = f"""对话历史：
# {conversation_context}

# 助手最新回复：{assistant_message}

# 请生成用户回复，返回JSON格式："""

#         try:
#             response = generate(
#                 model_key=self.model_key,
#                 system_prompt=system_prompt,
#                 user_prompt=user_prompt,
#                 temperature=self.config["temperature"],
#                 max_tokens=self.config["max_tokens"]
#             )
            
#             # Parse JSON response
#             try:
#                 result = json.loads(response.strip())
#                 user_response = result.get("response", "")
                
#                 # Check if should continue
#                 if not result.get("continue", True):
#                     return None
                    
#                 if user_response:
#                     self.conversation_history.append({"role": "user", "content": user_response})
#                     return user_response
                    
#             except json.JSONDecodeError:
#                 # Fallback: extract response from text if JSON parsing fails
#                 if "response" in response:
#                     import re
#                     match = re.search(r'"response":\s*"([^"]+)"', response)
#                     if match:
#                         user_response = match.group(1)
#                         self.conversation_history.append({"role": "user", "content": user_response})
#                         return user_response
            
#             return self._generate_fallback_response()
            
#         except Exception as e:
#             raise(f"用户代理响应生成失败: {e}")

    def _format_apis_for_prompt(self, api_candidates: List[Dict]) -> str:
        """Format API information for prompt"""
        api_lines = []
        for i, api in enumerate(api_candidates[:5], 1):  # Limit to 5 APIs
            name = api.get("name", f"api_{i}")
            desc = api.get("description", "")
            api_lines.append(f"{i}. {name}: {desc}")
        return "\n".join(api_lines)
        
    def _should_end_conversation(self) -> bool:
        """Decide whether to end the conversation"""
        # Simple heuristic: end after 3-6 turns
        user_turns = len([t for t in self.conversation_history if t["role"] == "user"])
        
        if user_turns >= 6:
            return True
        elif user_turns >= 3:
            return random.random() < 0.3  # 30% chance to end
        else:
            return False
        
    def generate_subtask_query(self, subtask_idx: int, global_conversation: List[Dict], api_candidates: List[Dict]) -> str:
        """
        Generate a new subtask query based on global conversation context
        
        Args:
            subtask_idx: Index of current subtask (0-based)
            global_conversation: Previous subtasks' conversation history
            api_candidates: Available APIs for this dialog
            
        Returns:
            User query for this subtask
        """
        if subtask_idx == 0:
            # First subtask - generate initial query
            return self._generate_initial_subtask_query(api_candidates)
        else:
            # Subsequent subtasks - can be related or independent
            return self._generate_followup_subtask_query(subtask_idx, global_conversation, api_candidates)
            
    def _generate_initial_subtask_query(self, api_candidates: List[Dict]) -> str:
        """Generate the first subtask query"""
        system_prompt = """你是一个用户，需要生成一个任务请求。

要求：
1. 生成一个明确、具体的任务请求
2. 任务应该可以通过给定的API来完成
3. 需要提供接口所需要的所有参数
4. 使用自然、口语化的表达
5. 任务应该有一定的复杂度，可能需要多步操作
6. 直接返回任务内容，不需要JSON格式

示例：
- "请帮我查找北京明天的天气，然后根据天气情况推荐合适的活动"
- "我需要搜索关于Python编程的资料，并整理成一个学习计划"
- "帮我查看我的日程安排，然后创建一个新的会议"
"""

        api_info = self._format_apis_for_prompt(api_candidates)
        user_prompt = f"""可用API：
{api_info}

请生成第一个子任务："""

        try:
            thinking_content, answer_content, tool_calls = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            )

            logger.info(
                f"user_agent _generate_initial_subtask_query:\n"
                f"[THINKING]: {thinking_content}\n\n"
                f"[ANSWER]: {answer_content}\n\n"
                f"[TOOL_CALLS]: {tool_calls}"
            )
            
            # Clean up the response
            query = answer_content.strip().strip('"').strip("'")
            return query
            
        except Exception as e:
            print(f"初始子任务查询生成失败: {e}")
            return "请帮我处理一个任务"

    def _generate_followup_subtask_query(self, subtask_idx: int, global_conversation: List[Dict], api_candidates: List[Dict]) -> str:
        """Generate a follow-up subtask query"""
        # Get probability from config, default to 50%
        related_prob = self.config.get("related_prob", 0.5)
        is_related = random.random() < related_prob
        
        if is_related:
            task_type = "相关任务"
            task_instruction = "生成与之前任务相关的后续任务"
        else:
            task_type = "独立任务"
            task_instruction = "生成一个完全独立的新任务，不要考虑之前的任务内容"
        
        system_prompt = f"""你是一个用户，需要生成一个任务请求。

当前任务类型：{task_type}
任务要求：{task_instruction}

要求：
1. 生成明确、具体的任务请求  
2. 任务应该可以通过给定的API完成
3. 使用自然、口语化的表达
4. 直接根据提供的api提供任务内容，不需要JSON格式
"""

        api_info = self._format_apis_for_prompt(api_candidates)
        
        if is_related:
            context_str = [
                {
                    **{k: v for k, v in conv.items() if k != 'think'},
                }
                for conv in global_conversation
            ]

            user_prompt = f"""之前的对话情况：
{context_str}

可用API：
{api_info}

请生子任务："""
        else:
            # For independent tasks, don't provide context
            user_prompt = f"""可用API：
{api_info}

请生成子任务："""

        try:
            thinking_content, answer_content, tool_calls = generate(
                model_key=self.model_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            )

            logger.info(
                f"user_agent _generate_followup_subtask_query:\n"
                f"[THINKING]: {thinking_content}\n\n"
                f"[ANSWER]: {answer_content}\n\n"
                f"[TOOL_CALLS]: {tool_calls}"
            )
        
            # Clean up the response
            query = answer_content.strip().strip('"').strip("'")
            return query
            
        except Exception as e:
            raise(f"后续子任务查询生成失败: {e}")
