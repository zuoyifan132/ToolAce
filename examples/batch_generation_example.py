#!/usr/bin/env python3
"""
批量多子任务对话生成示例

展示如何使用SDG模块的异步批量生成功能来提高数据生成效率
"""

import asyncio
import time
import json
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from toolace.sdg import SDG
from toolace.tss.api_pool import APIPool


def progress_callback(completed: int, failed: int, total: int):
    """进度回调函数"""
    percentage = (completed + failed) / total * 100
    print(f"📈 进度: {completed + failed}/{total} ({percentage:.1f}%) - 成功: {completed}, 失败: {failed}")


async def async_batch_example():
    """异步批量生成示例"""
    print("🚀 异步批量生成示例")
    print("=" * 50)
    
    # 初始化SDG
    config = {
        "batch_concurrency": 4,
        "batch_timeout": 300,
        "min_subtasks": 1,
        "max_subtasks": 3,
        "max_react_steps": 3
    }
    sdg = SDG(config=config)
    
    # 模拟API池
    api_pool = APIPool()
    # 这里应该从实际API池加载数据
    # api_pool.load_from_file("path/to/api_pool.json")
    
    # 生成少量API用于测试
    test_apis = [
        {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "days": {"type": "integer", "description": "预报天数"}
                },
                "required": ["city"]
            }
        },
        {
            "name": "search_music",
            "description": "搜索音乐信息",
            "parameters": {
                "type": "object", 
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回数量限制"}
                },
                "required": ["query"]
            }
        }
    ]
    
    # 模拟API池的sample_apis方法
    class MockAPIPool:
        def sample_apis(self, count=5):
            import random
            return random.sample(test_apis, min(count, len(test_apis)))
    
    api_pool = MockAPIPool()
    
    # 异步批量生成
    start_time = time.time()
    
    dialogs = await sdg.batch_generate_multi_subtask_dialogs(
        api_pool=api_pool,
        count=10,
        progress_callback=progress_callback
    )
    
    end_time = time.time()
    
    # 统计结果
    successful_dialogs = [d for d in dialogs if d.get("batch_metadata", {}).get("status") == "success"]
    failed_dialogs = [d for d in dialogs if d.get("batch_metadata", {}).get("status") == "failed"]
    
    print(f"\n📊 生成结果:")
    print(f"   总耗时: {end_time - start_time:.2f} 秒")
    print(f"   成功: {len(successful_dialogs)}")
    print(f"   失败: {len(failed_dialogs)}")
    print(f"   平均每个对话: {(end_time - start_time) / len(dialogs):.2f} 秒")
    
    # 保存结果
    output_file = Path("data/generated/batch_dialogs_async.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dialogs, f, ensure_ascii=False, indent=2)
    
    print(f"💾 结果已保存到: {output_file}")
    
    return dialogs


def threaded_batch_example():
    """多线程批量生成示例"""
    print("\n🧵 多线程批量生成示例")
    print("=" * 50)
    
    # 初始化SDG
    config = {
        "batch_concurrency": 4,
        "min_subtasks": 1,
        "max_subtasks": 3,
        "max_react_steps": 3
    }
    sdg = SDG(config=config)
    
    # 模拟API池
    class MockAPIPool:
        def sample_apis(self, count=5):
            test_apis = [
                {
                    "name": "get_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "城市名称"}
                        },
                        "required": ["city"]
                    }
                },
                {
                    "name": "search_music", 
                    "description": "搜索音乐信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索关键词"}
                        },
                        "required": ["query"]
                    }
                }
            ]
            import random
            return random.sample(test_apis, min(count, len(test_apis)))
    
    api_pool = MockAPIPool()
    
    # 多线程批量生成
    start_time = time.time()
    
    dialogs = sdg.batch_generate_dialogs_threaded(
        api_pool=api_pool,
        count=10,
        progress_callback=progress_callback
    )
    
    end_time = time.time()
    
    # 统计结果
    successful_dialogs = [d for d in dialogs if d.get("batch_metadata", {}).get("status") == "success"]
    failed_dialogs = [d for d in dialogs if d.get("batch_metadata", {}).get("status") == "failed"]
    
    print(f"\n📊 生成结果:")
    print(f"   总耗时: {end_time - start_time:.2f} 秒")
    print(f"   成功: {len(successful_dialogs)}")
    print(f"   失败: {len(failed_dialogs)}")
    print(f"   平均每个对话: {(end_time - start_time) / len(dialogs):.2f} 秒")
    
    return dialogs


def sync_batch_example():
    """同步批量生成示例（对比基准）"""
    print("\n🐌 同步批量生成示例（基准对比）")
    print("=" * 50)
    
    # 初始化SDG
    config = {
        "min_subtasks": 1,
        "max_subtasks": 3,
        "max_react_steps": 3
    }
    sdg = SDG(config=config)
    
    # 模拟API池
    class MockAPIPool:
        def sample_apis(self, count=5):
            test_apis = [
                {
                    "name": "get_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "城市名称"}
                        },
                        "required": ["city"]
                    }
                },
                {
                    "name": "search_music",
                    "description": "搜索音乐信息", 
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索关键词"}
                        },
                        "required": ["query"]
                    }
                }
            ]
            import random
            return random.sample(test_apis, min(count, len(test_apis)))
    
    api_pool = MockAPIPool()
    
    # 同步批量生成
    start_time = time.time()
    
    dialogs = sdg.batch_generate_dialogs(
        api_pool=api_pool,
        count=10
    )
    
    end_time = time.time()
    
    print(f"\n📊 生成结果:")
    print(f"   总耗时: {end_time - start_time:.2f} 秒")
    print(f"   成功: {len(dialogs)}")
    print(f"   平均每个对话: {(end_time - start_time) / len(dialogs):.2f} 秒")
    
    return dialogs


async def main():
    """主函数"""
    print("🎯 ToolACE 批量多子任务对话生成示例")
    print("=" * 60)
    
    # 运行异步示例
    await async_batch_example()
    
    # 运行多线程示例
    threaded_batch_example()
    
    # 运行同步示例（基准）
    sync_batch_example()
    
    print("\n✅ 所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())
