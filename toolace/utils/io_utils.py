import os
import json
import pandas as pd
import numpy as np
from loguru import logger
from typing import List, Dict, Any, Union


def save_jsonl(data: Union[Dict[str, Any], List[Dict[str, Any]]], output_path: str, mode="w") -> bool:
    """
    将数据保存为 JSONL 文件。

    参数:
        data: 要保存的数据(单条字典或字典列表)。
        output_path: 输出文件路径。
        mode: 写入模式，'w'表示覆盖，'a'表示追加。

    返回:
        成功返回 True，失败抛出异常。
    """
    try:
        dir_path = os.path.dirname(output_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        with open(output_path, mode=mode, encoding="utf-8") as f:
            if isinstance(data, dict):
                # 单个字典，直接写入一行
                json.dump(data, f, ensure_ascii=False)
                f.write("\n")
            else:
                # 字典列表，逐行写入
                for row in data:
                    try:
                        json.dump(row, f, ensure_ascii=False)
                        f.write("\n")
                    except:
                        continue
                    
        logger.info(f"Data successfully saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {output_path}: {e}")
        raise


def save_to_json(data: Union[Dict[str, Any], List[Dict[str, Any]]], file_name: str, mode="w") -> bool:
    """
    将数据保存为 JSON 文件。

    参数:
        data: 要保存的数据(单条字典或字典列表)。
        file_name: 输出 JSON 文件路径。
        mode: 写入模式，'w'表示覆盖，'a'表示追加。

    返回:
        成功返回 True，失败抛出异常。
    """
    try:
        dir_path = os.path.dirname(file_name)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        if mode == "a" and os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            # 追加模式且文件存在
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                if isinstance(existing_data, list):
                    if isinstance(data, dict):
                        # 添加单个字典到现有列表
                        existing_data.append(data)
                    else:
                        # 添加字典列表到现有列表
                        existing_data.extend(data)
                    
                    # 写回完整数据
                    with open(file_name, 'w', encoding='utf-8') as f:
                        json.dump(existing_data, f, ensure_ascii=False, indent=4)
                else:
                    logger.warning(f"Existing JSON is not a list. Overwriting with new data.")
                    with open(file_name, 'w', encoding='utf-8') as f:
                        if isinstance(data, dict):
                            json.dump([data], f, ensure_ascii=False, indent=4)
                        else:
                            json.dump(data, f, ensure_ascii=False, indent=4)
            except json.JSONDecodeError:
                logger.warning(f"Existing JSON file is invalid. Overwriting with new data.")
                with open(file_name, 'w', encoding='utf-8') as f:
                    if isinstance(data, dict):
                        json.dump([data], f, ensure_ascii=False, indent=4)
                    else:
                        json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            # 新文件或覆盖模式
            with open(file_name, 'w', encoding='utf-8') as f:
                if isinstance(data, dict):
                    # 单条数据，但JSON文件应保持为列表格式
                    json.dump([data], f, ensure_ascii=False, indent=4)
                else:
                    # 列表数据，直接写入
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    
        logger.info(f"Data successfully saved to {file_name}")
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_name}: {e}")
        raise