"""
Tool Agent Module

This module implements the tool agent that simulates API execution
and generates realistic responses for function calls.
"""

import json
import random
import importlib
from textwrap import dedent
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from tenacity import RetryError

from ...utils.model_manager import generate


class ToolAgent:
    """
    Tool agent that simulates API execution and generates realistic responses
    """
    
    def __init__(self, model_key: str = "sdg_tool_agent_model", config: dict = None):
        self.model_key = model_key
        self.config = config
        self.execution_history = []
        self.error_rate = config.get("error_rate", 0.2)

    def execute_single_function(
        self, 
        function_call: Dict,
        api_definitions: List[Dict], 
        content: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a single function call
        
        Args:
            function_call: Function call dictionary with name and parameters
            api_definitions: Available API definitions
            
        Returns:
            Execution result dictionary
        """
        # Handle case when no function but steps is less than mini_react_steps
        if not function_call and content:
            return self._handle_no_function_scenario(content, api_definitions)

        call_name = function_call.get("name")
        call_params = function_call.get("parameters", {})
        
        # Find API definition
        api_def = self._find_api_definition(call_name, api_definitions)
        if not api_def:
            return self._generate_error_response(f"API '{call_name}' not found")
            
        # Simulate random errors
        if random.random() < self.error_rate:
            return self._generate_error_response("API execution failed")
            
        # Validate parameters
        validation_result = self._validate_parameters(call_params, api_def)
        if not validation_result["valid"]:
            return self._generate_error_response(validation_result["error"])
            
        # Generate realistic response
        response = self._generate_api_response(call_name, call_params, api_def)
        
        # Record execution
        self.execution_history.append({
            "function": call_name,
            "parameters": call_params,
            "response": response,
        })
        
        return {
            "function": call_name,
            "status": "success",
            "result": response
        }
        
    def _handle_no_function_scenario(self, conversation: List[Dict], api_definitions: List[Dict]) -> str:
        """
        Handle scenario when no function call exists but more steps are needed
        
        Args:
            conversation: Current conversation history
            api_definitions: Available API definitions
            
        Returns:
            Simulated tool response
        """
        # Analyze task and generate appropriate response in one LLM call
        response_data = self._analyze_and_generate_response(conversation, api_definitions)

        return response_data["response_message"]

    def _analyze_and_generate_response(self, conversation: List[Dict], api_definitions: List[Dict]) -> Dict[str, Any]:
        """
        Analyze task completion and generate appropriate response in one LLM call
        
        Args:
            conversation: Conversation history
            api_definitions: Available API definitions
            
        Returns:
            Combined analysis and response data
        """
        system_prompt = dedent(
            """你就是当前的用户，你需要分析当前对话的任务状态，模拟用户并生成相应的响应。

            分析步骤：
            1. 判断任务是否已经完成
            2. 如果完成，生成后续的问题
            3. 如果未完成，生成澄清请求

            任务完成的判断标准：
            - 用户的需求是否已经得到满足
            - 助手的回复是否已经提供了完整的解决方案
            - 最近的工具调用结果是否已经满足需求

            响应要求：
            - 如果任务完成：提供相关的后续建议，建议应该与可用的API功能相关
            - 如果任务未完成：明确指出缺失的信息，并提供澄清

            ## 示例1：任务已完成
            对话历史：
            用户: 帮我查询北京今天的天气
            助手: 我来帮您查询北京今天的天气。[调用: get_weather]
            工具[get_weather]: {"city": "北京", "date": "2024-01-15", "weather": "晴", "temperature": "5-15°C", "humidity": "45%"}
            助手: 北京今天天气晴朗，温度5-15°C，湿度45%。出行记得适当增减衣物。

            分析返回：
            ```json
            {
                "task_status": "completed",
                "response_message": "谢谢！那明天的天气怎么样呢？需要带伞吗？",
                "related_apis": ["get_weather", "get_weather_forecast"]
            }
            ```

            ## 示例2：任务已完成，询问相关功能
            对话历史：
            用户: 帮我订一张明天从上海到北京的机票
            助手: 我来帮您搜索明天上海到北京的航班。[调用: search_flights]
            工具[search_flights]: {"flights": [{"flight_no": "CA1234", "time": "08:00-10:30", "price": 1200}, {"flight_no": "MU5678", "time": "14:00-16:30", "price": 980}]}
            助手: 找到了两个航班：CA1234早上8点起飞，票价1200元；MU5678下午2点起飞，票价980元。您想预订哪个航班？
            用户: 订下午2点的MU5678
            助手: 好的，我来为您预订MU5678航班。[调用: book_flight]
            工具[book_flight]: {"status": "success", "booking_id": "BK20240115001", "flight": "MU5678", "price": 980}
            助手: 已成功预订！订单号：BK20240115001，MU5678航班，票价980元。

            分析返回：
            ```json
            {
                "task_status": "completed", 
                "response_message": "太好了，订票成功！对了，我需要从市区去机场，能帮我查一下机场大巴的时刻表吗？",
                "related_apis": ["get_airport_shuttle", "get_taxi_estimate"]
            }
            ```

            ## 示例3：需要澄清信息
            对话历史：
            用户: 帮我订酒店
            助手: 好的，我来帮您预订酒店。请问您想在哪个城市订酒店？

            分析返回：
            ```json
            {
                "task_status": "needs_clarification",
                "response_message": "我想在杭州订酒店，大概这周五入住，住两晚。",
                "related_apis": ["search_hotels"]
            }
            ```

            ## 示例4：需要更多信息
            对话历史：
            用户: 我想买点东西
            助手: 请问您想购买什么类型的商品呢？我可以帮您搜索电子产品、服装、日用品等各类商品。

            分析返回：
            ```json
            {
                "task_status": "needs_clarification",
                "response_message": "我想买个新的笔记本电脑，预算在5000-8000元左右，主要用于办公和轻度游戏。",
                "related_apis": ["search_products", "get_product_reviews"]
            }
            ```

            ## 示例5：部分完成，需要确认
            对话历史：
            用户: 帮我查一下我的快递
            助手: 我来帮您查询快递信息。[调用: get_delivery_status]
            工具[get_delivery_status]: {"error": "需要提供快递单号或手机号"}
            助手: 抱歉，查询快递需要您提供快递单号或收件人手机号，请问您方便提供吗？

            分析返回：
            ```json
            {
                "task_status": "needs_clarification",
                "response_message": "快递单号是SF1234567890，是昨天下的单。",
                "related_apis": ["get_delivery_status"]
            }
            ```

            返回JSON格式：
            ```json
            {
                "task_status": "completed" 或 "needs_clarification",
                "response_message": "模拟的用户回复",
                "related_apis": ["相关API名称，可选"]
            }
            ```"""
        )

        # Format conversation and API information
        formatted_conversation = conversation
        api_info = api_definitions
        
        user_prompt = dedent(
            f"""对话历史：
            {formatted_conversation}

            可用的API功能：
            {api_info}

            请分析任务状态并生成相应的响应："""
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
                f"_analyze_and_generate_response:\n"
                f"[THINKING]: {thinking_content}\n\n"
                f"[ANSWER]: {answer_content}\n\n"
                f"[TOOL_CALLS]: {tool_calls}"
            )

            json_content = self._extract_json_from_response(answer_content)
            result = json.loads(json_content)
            
            # Validate required fields
            if "task_status" not in result or "response_message" not in result:
                raise ValueError("Missing required fields")
            
            return result
            
        except Exception as e:
            raise(f"data analysis and response generation failed: {e}")

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from response that might contain markdown code blocks
        
        Args:
            response: Raw response string that might contain ```json``` blocks
            
        Returns:
            Extracted JSON string
        """
        # Try to find JSON within code blocks
        import re
        
        # Pattern to match ```json``` code blocks
        json_pattern = r'```json\s*\n(.*?)\n```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Pattern to match ``` code blocks without json marker
        code_pattern = r'```\s*\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            # Check if the content looks like JSON
            content = matches[0].strip()
            if content.startswith('{') or content.startswith('['):
                return content
        
        # If no code blocks found, try to extract JSON directly
        # Look for content between first { and last }
        try:
            first_brace = response.find('{')
            last_brace = response.rfind('}')
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                return response[first_brace:last_brace + 1]
        except:
            pass
        
        # Return original response as fallback
        return response.strip()

    def _find_api_definition(self, api_name: str, api_definitions: List[Dict]) -> Optional[Dict]:
        """Find API definition by name"""
        for api in api_definitions:
            if api.get("name") == api_name:
                return api
        return None
        
    def _validate_parameters(self, parameters: Dict, api_definition: Dict) -> Dict[str, Any]:
        """Validate function call parameters against API definition"""
        api_params = api_definition.get("parameters", {})
        required_params = api_params.get("required", [])
        param_properties = api_params.get("properties", {})
        
        # Check required parameters
        for required_param in required_params:
            if required_param not in parameters:
                return {
                    "valid": False,
                    "error": f"Missing required parameter: {required_param}"
                }
                
        # Check parameter types (basic validation)
        for param_name, param_value in parameters.items():
            if param_name in param_properties:
                expected_type = param_properties[param_name].get("type")
                if not self._check_parameter_type(param_value, expected_type):
                    return {
                        "valid": False,
                        "error": f"Invalid type for parameter {param_name}: expected {expected_type}"
                    }
                    
        return {"valid": True}

    def _check_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Check if parameter value matches expected type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Default to valid if type not recognized

    def _generate_api_response(self, api_name: str, parameters: Dict, api_definition: Dict) -> Dict[str, Any]:
        """Generate realistic API response using LLM or templates"""
        
        # Try LLM generation first
        llm_response = self._generate_response_with_llm(api_name, parameters, api_definition)
        if llm_response:
            return llm_response
        
    def _generate_response_with_llm(self, api_name: str, parameters: Dict, api_definition: Dict) -> Optional[Dict]:
        """Generate API response using LLM"""
        system_prompt = dedent(
            """你是一个API模拟器，需要根据API定义和输入参数生成真实的API响应。

            要求：
            1. 响应要符合API的返回值定义
            2. 数据要真实、合理，不要明显虚假
            3. 如果是查询类API，返回相关的数据
            4. 如果是操作类API，返回操作结果
            5. 返回JSON格式的数据，不要其他说明
            6. 数据要有适当的变化，不要总是相同的值

            ```json
            {
                "api_return": your mock up api return
            }
            ```
            """
        )

        api_info = {
            "name": api_name,
            "description": api_definition.get("description", ""),
            "parameters": parameters,
            "returns": api_definition.get("returns", {})
        }
        
        user_prompt = dedent(
            f"""API信息：
            {json.dumps(api_info, ensure_ascii=False, indent=2)}

            请生成符合API定义的响应数据："""
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
                f"_generate_response_with_llm:\n"
                f"[THINKING]: {thinking_content}\n\n"
                f"[ANSWER]: {answer_content}\n\n"
                f"[TOOL_CALLS]: {tool_calls}"
            )
            
            # Parse JSON response
            json_content = self._extract_json_from_response(answer_content)
            result = json.loads(json_content)
            return result
        except RetryError as e:
            # handle retry failure case
            logger.error(f"Tool simulation failed after multiple retries: {e}")
            raise RuntimeError(f"Tool simulation generation failed: Model call still failed after multiple retries") from e
        except Exception as e:
            print(f"LLM API response generation failed: {e}")
            return None

    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "status": "error",
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
