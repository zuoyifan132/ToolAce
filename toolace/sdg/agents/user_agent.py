"""
User Agent Module

This module implements the user agent that generates user queries and responses
in the multi-agent dialog generation system.
"""
import re 
import random
import json
import importlib
from textwrap import dedent
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
        system_prompt = dedent(
            """你是一个用户，需要生成一个任务请求。

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
            """)

        api_info = self._format_apis_for_prompt(api_candidates)
        user_prompt = dedent(
            f"""可用API：
            {api_info}

            请生成第一个子任务："""
        )

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
        
        system_prompt = dedent(
            f"""你是一个用户，需要生成一个任务请求。

            当前任务类型：{task_type}
            任务要求：{task_instruction}

            要求：
            1. 生成明确、具体的任务请求  
            2. 任务应该可以通过给定的API完成
            3. 使用自然、口语化的表达
            4. 直接根据提供的api提供任务内容，不需要JSON格式
            """)

        api_info = self._format_apis_for_prompt(api_candidates)
        
        if is_related:
            context_str = [
                {
                    **{k: v for k, v in conv.items() if k != 'think'},
                }
                for conv in global_conversation
            ]

            user_prompt = dedent(
                f"""之前的对话情况：
                {context_str}

                可用API：
                {api_info}

                请生子任务：""")
        else:
            # For independent tasks, don't provide context
            user_prompt = dedent(
                f"""可用API：
                {api_info}

                请生成子任务：""")

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
