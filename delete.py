#!/usr/bin/env python3
"""
delete.py

删除 Wallpaper Engine 本地 workshop 数据中未订阅的壁纸目录。
脚本将输出要删除的目录列表
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime


# ------------------ 用户可编辑的配置 ------------------
# PATH: 本地wallpaper engine 壁纸保存文件夹路径
PATH = r"D:\Programs\Steam\steamapps\workshop\content\431960"
# USERDATA_PATH: wallpaper engine 订阅信息文件路径
USERDATA_PATH = r"D:\Programs\Steam\userdata\1745541154\ugc\431960_subscriptions.vdf"
# CHECK = True 表示默认仅检查不删除；设置为 False 则默认执行删除。
CHECK = False
# ----------------------------------------------------


def parse_subscribed_ids(vdf_path):
    """
    从 subscriptions vdf 文件中提取订阅的 workshop ID 集合。
    优先尝试匹配条目 key(如:"123456789" { ... }), 若未找到则退回匹配任意被引用的数字字符串。
    """
    if not os.path.isfile(vdf_path):
        raise FileNotFoundError(f"subscriptions file not found: {vdf_path}")

    text = open(vdf_path, "r", encoding="utf-8", errors="ignore").read()

    # 先尝试匹配像 "123456789" \n {  的条目形式 (key 前面跟着一个花括号)
    ids = set(re.findall(r'"\s*(\d{6,20})\s*"\s*\n\s*\{', text, flags=re.M))

    # 回退: 匹配任意被引号包围的数字（可能包含时间戳等）
    if not ids:
        ids = set(re.findall(r'"\s*(\d{6,20})\s*"', text))

    return ids


def find_local_workshop_ids(path):
    """
    返回路径下以数字命名的子目录集合(假设 workshop 每个 item 存为数字文件夹)。
    """
    if not os.path.isdir(path):
        raise NotADirectoryError(f"路径未找到或不是目录: {path}")

    ids = set()
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.isdir(full) and name.isdigit():
            ids.add(name)
    return ids


def main():
    p = argparse.ArgumentParser(description="删除 Wallpaper Engine 本地未订阅的 workshop 数据目录")
    p.add_argument("--path", default=PATH, help="本地 workshop content 路径, 例如 D:\\...\\workshop\\content\\431960")
    p.add_argument("--userdata", default=USERDATA_PATH, help="subscriptions vdf 文件路径, 例如 ...\\431960_subscriptions.vdf")
    p.add_argument("--check", action="store_true", default=CHECK, help="仅查找并列出将被删除的目录, 不执行删除")
    args = p.parse_args()

    # 支持从文件顶部配置常量或命令行覆盖
    path = args.path
    userdata = args.userdata
    check_only = args.check

    try:
        subscribed = parse_subscribed_ids(userdata)
    except Exception as e:
        print(f"解析订阅文件失败: {e}")
        sys.exit(2)

    try:
        local = find_local_workshop_ids(path)
    except Exception as e:
        print(f"扫描本地 workshop 目录失败: {e}")
        sys.exit(2)

    orphan = sorted(list(local - subscribed))

    if not orphan:
        print("未发现未订阅但存在于本地的 workshop 项目。")
        return

    print(f"发现 {len(orphan)} 个本地存在但未订阅的项目:")
    for oid in orphan:
        print(f" - {oid} -> {os.path.join(args.path, oid)}")

    if check_only:
        print("--check 模式，未执行删除。")
        return

    # 执行删除
    deleted_count = 0
    for oid in orphan:
        target = os.path.join(args.path, oid)
        try:
            shutil.rmtree(target)
            deleted_count += 1
            print(f"已删除: {target}")
        except Exception as e:
            print(f"删除失败: {target} -> {e}")

    print(f"完成: 已删除 {deleted_count} 个目录。")


if __name__ == "__main__":
    main()