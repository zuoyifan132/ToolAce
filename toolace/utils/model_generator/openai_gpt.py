"""
@File   : openai_gpt.py
@Time   : 2025/09/17 14:19
@Author : toolace
@Desc   : OpenAI GPT model interface for generating responses with thinking process and function calls
"""

import os
import json
import dotenv
import openai
from typing import Tuple, List, Dict, Any
from loguru import logger


dotenv.load_dotenv("../../../.env")


def generate(system: str, user: str, **kwargs) -> Tuple[Dict[str, Any], str, List[Dict[str, Any]]]:
    """
    Generate response using OpenAI GPT model with thinking process and function calls support.
    
    Args:
        system: System prompt
        user: User input
        **kwargs: Additional parameters:
            - model_name: Model to use (default: o4-mini-2025-04-16)
            - temperature: Sampling temperature (default: 1.0)
            - max_tokens: Maximum tokens to generate (default: 4096)
            - tools: List of available tools/functions (default: [])
    
    Returns:
        Tuple containing:
        - thinking_block: Dict with model's thinking process
        - answer: Generated text response
        - function_calls: List of function calls made by the model
    """
    if openai is None:
        raise ImportError("OpenAI package not installed. Please install with: pip install openai")
    
    # Get configuration
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    model_name = kwargs.get("model_name", "gpt-5")
    temperature = kwargs.get("temperature", 1.0)
    max_tokens = kwargs.get("max_tokens", 4096)
    tools = kwargs.get("tools", [])
    
    # Initialize client
    client = openai.OpenAI(api_key=api_key)
    
    # Prepare messages with special prompt for reasoning extraction
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
        
    try:
        # Make API call
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=temperature,
            max_completion_tokens=max_tokens,
            tools=tools,
            tool_choice="auto"
        )
        
        # Extract response components and usage information
        message = response.choices[0].message
        content = message.content
        usage = response.usage
        finish_reason = response.choices[0].finish_reason
        
        # Process function calls first
        function_calls = []
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    function_calls.append({
                        "name": tool_call.function.name,
                        "parameters": json.loads(tool_call.function.arguments)
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse function arguments: {e}")
        
        # Extract thinking and answer from structured response
        thinking = ""
        answer = ""
        
        # For function calls, we need to handle the response differently
        if finish_reason == "tool_calls":
            # Generate thinking based on function calls and reasoning tokens
            thinking = ""
            
            # Answer will be generated after function execution
            answer = ""
        else:
            # Regular response parsing
            if "<thinking>" in content and "</thinking>" in content:
                thinking = content.split("<thinking>")[1].split("</thinking>")[0].strip()
            if "<answer>" in content and "</answer>" in content:
                answer = content.split("<answer>")[1].split("</answer>")[0].strip()
            
            # If no structured format found, use the whole content as answer
            if not thinking and not answer:
                # Check if we have reasoning tokens in the usage stats
                if (hasattr(usage, 'completion_tokens_details') and 
                    hasattr(usage.completion_tokens_details, 'reasoning_tokens') and 
                    usage.completion_tokens_details.reasoning_tokens > 0):
                    # Split content based on reasoning tokens proportion
                    total_tokens = usage.completion_tokens
                    reasoning_tokens = usage.completion_tokens_details.reasoning_tokens
                    reasoning_ratio = reasoning_tokens / total_tokens
                    content_words = content.split()
                    split_point = int(len(content_words) * reasoning_ratio)
                    
                    thinking = " ".join(content_words[:split_point])
                    answer = " ".join(content_words[split_point:])
                else:
                    answer = content
                    thinking = "No explicit reasoning provided by the model"
        
        # Process function calls
        function_calls = []
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    function_calls.append({
                        "name": tool_call.function.name,
                        "parameters": json.loads(tool_call.function.arguments)
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse function arguments: {e}")
        
        return thinking, answer, function_calls
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise RuntimeError(f"OpenAI API call failed: {e}")


def stream_generate(system: str, user: str, **kwargs) -> str:
    """
    Stream generate response using OpenAI GPT model with thinking process support.
    
    Args:
        system: System prompt
        user: User input
        **kwargs: Additional parameters:
            - model_name: Model to use (default: o4-mini-2025-04-16)
            - temperature: Sampling temperature (default: 1.0)
            - max_tokens: Maximum tokens to generate (default: 4096)
            - tools: List of available tools/functions (default: [])
    
    Returns:
        Generated text response as a stream, including thinking process
    """
    if openai is None:
        raise ImportError("OpenAI package not installed. Please install with: pip install openai")
    
    # Get configuration
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    model_name = kwargs.get("model_name", "o4-mini-2025-04-16")
    temperature = kwargs.get("temperature", 1.0)
    max_tokens = kwargs.get("max_tokens", 4096)
    tools = kwargs.get("tools", [])
    
    # Initialize client
    client = openai.OpenAI(api_key=api_key)
    
    # Prepare messages with special prompt for reasoning extraction
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    
    # Add special instruction for reasoning model
    reasoning_prompt = (
        "Please structure your response in the following format:\n"
        "<thinking>\n"
        "[Your step-by-step reasoning process here]\n"
        "</thinking>\n"
        "<answer>\n"
        "[Your final answer here]\n"
        "</answer>"
    )
    
    messages.append({"role": "system", "content": reasoning_prompt})
    messages.append({"role": "user", "content": user})
    
    logger.debug(f"Streaming OpenAI {model_name} model response")
    
    current_section = None
    thinking_content = ""
    answer_content = ""
    buffer = ""
    
    try:
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice="auto",
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                buffer += content
                
                # Check for section markers
                if "<thinking>" in buffer and current_section != "thinking":
                    current_section = "thinking"
                    print("<thinking>\n", end="", flush=True)
                    buffer = buffer.split("<thinking>")[1]
                elif "<answer>" in buffer and current_section != "answer":
                    if current_section == "thinking":
                        print("</thinking>\n", end="", flush=True)
                    current_section = "answer"
                    print("<answer>\n", end="", flush=True)
                    buffer = buffer.split("<answer>")[1]
                
                # Process content based on current section
                if "</thinking>" in buffer and current_section == "thinking":
                    thinking_part = buffer.split("</thinking>")[0]
                    thinking_content += thinking_part
                    print(thinking_part, end="", flush=True)
                    buffer = "".join(buffer.split("</thinking>")[1:])
                    current_section = None
                elif "</answer>" in buffer and current_section == "answer":
                    answer_part = buffer.split("</answer>")[0]
                    answer_content += answer_part
                    print(answer_part, end="", flush=True)
                    buffer = "".join(buffer.split("</answer>")[1:])
                    current_section = None
                elif current_section:
                    print(content, end="", flush=True)
                    if current_section == "thinking":
                        thinking_content += content
                    else:
                        answer_content += content
        
        # Handle any remaining content
        if buffer:
            if current_section == "thinking":
                thinking_content += buffer
            elif current_section == "answer":
                answer_content += buffer
            else:
                answer_content += buffer
            print(buffer, end="", flush=True)
        
        if current_section == "thinking":
            print("\n</thinking>", flush=True)
        elif current_section == "answer":
            print("\n</answer>", flush=True)
        
        # If no structured format was found, treat all content as answer
        if not thinking_content and not answer_content:
            answer_content = buffer
        
        return answer_content
                
    except Exception as e:
        logger.error(f"OpenAI streaming API call failed: {e}")
        raise RuntimeError(f"OpenAI streaming API call failed: {e}")


if __name__ == "__main__":
    # Example 1: Regular generation without tools
    print("\n=== Example 1: Regular Generation ===")
    system = "You are a helpful assistant."
    user = "Explain what is quantum computing in simple terms."
    
    thinking, answer, function_calls = generate(system, user)
    print("Thinking:", thinking)
    print("\nAnswer:", answer)
    print("\nFunction Calls:", json.dumps(function_calls, indent=2))

    # Example 2: Function calling
    print("\n=== Example 2: Function Calling ===")
    # Define available tools/functions
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    system = """You are a helpful weather assistant. When users ask about weather, 
    use the get_weather function to fetch weather information."""
    
    user = "What's the weather like in Beijing? Please use Celsius."
    
    thinking, answer, function_calls = generate(
        system=system,
        user=user,
        tools=tools
    )
    
    print("Thinking:", thinking)
    print("\nAnswer:", answer)
    print("\nFunction Calls:", json.dumps(function_calls, indent=2))
