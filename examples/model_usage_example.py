#!/usr/bin/env python3
"""
简化模型调用示例

演示如何使用新的简化模型调用接口
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from toolace.utils.model_manager import get_model_generator, generate


def main():
    """主示例函数"""
    print("🚀 ToolACE 简化模型调用示例")
    
    # 示例1: 使用工厂函数获取模型生成器
    print("\n📊 示例1: 使用工厂函数动态获取模型")
    
    system_prompt = "你是一个API设计专家，请帮助设计API接口。"
    user_prompt = "请设计一个天气查询的API接口"
    
    # 获取Mock模型生成器
    try:
        print("\n🎭 使用Mock模型:")
        mock_generator = get_model_generator("mock_llm")
        response = mock_generator(system_prompt, user_prompt, temperature=0.7)
        print(f"响应: {response[:200]}...")
    except Exception as e:
        print(f"Mock模型调用失败: {e}")
    
    # 获取Qwen模型生成器  
    try:
        print("\n🤖 使用Qwen3 32B模型:")
        qwen_generator = get_model_generator("qwen3_32b")
        response = qwen_generator(
            system_prompt, 
            user_prompt, 
            temperature=0.3,
            max_tokens=512
        )
        print(f"响应: {response[:200]}...")
    except Exception as e:
        print(f"Qwen模型调用失败: {e}")
    
    # 示例2: 直接使用统一生成函数
    print("\n📊 示例2: 使用统一生成函数")
    
    try:
        print("\n🔧 直接调用生成函数:")
        response = generate(
            model_key="mock_llm",
            system_prompt="你是一个对话生成专家。",
            user_prompt="请生成一个关于工具调用的简单示例",
            temperature=0.8,
            max_tokens=300
        )
        print(f"响应: {response}")
        
    except Exception as e:
        print(f"统一生成函数调用失败: {e}")
    
    # 示例3: 直接导入模型模块使用
    print("\n📊 示例3: 直接导入模型模块")
    
    try:
        from toolace.utils.model_generator import mock_llm
        print("\n🎯 直接导入mock_llm模块:")
        response = mock_llm.generate(
            system="你是一个故事讲述者。",
            user="请讲一个关于AI的简短故事",
            temperature=0.9
        )
        print(f"生成的故事: {response}")
        
    except Exception as e:
        print(f"直接导入调用失败: {e}")
    
    # 示例4: 流式生成
    print("\n📊 示例4: 流式生成")
    
    try:
        from toolace.utils.model_manager import stream_generate
        print("\n🌊 流式生成示例:")
        
        stream = stream_generate(
            model_key="mock_llm",
            system_prompt="你是一个编程助手。",
            user_prompt="请解释什么是函数调用",
            temperature=0.7
        )
        
        print("流式输出: ", end="")
        for chunk in stream:
            print(chunk, end="", flush=True)
        print()
        
    except Exception as e:
        print(f"流式生成失败: {e}")
    
    print("\n🎉 所有示例运行完成！")
    print("\n💡 使用说明:")
    print("1. 使用 get_model_generator(model_name) 获取模型生成函数")
    print("2. 使用 generate(model_name, system, user, **kwargs) 统一调用")
    print("3. 直接导入具体模型模块使用")
    print("4. 所有模型都支持 generate(system, user, **kwargs) 接口")


if __name__ == "__main__":
    main()
