#!/usr/bin/env python3
"""
delete.py

删除 Wallpaper Engine 本地 workshop 数据中未订阅的壁纸目录。
脚本将输出要删除的目录列表
"""

import argparse
import os
import re
import sys
from datetime import datetime
from shutil import rmtree
from winreg import OpenKey,HKEY_CURRENT_USER,QueryValueEx


# ------------------------------------
#PATH = r"D:\Programs\Steam\steamapps\workshop\content\431960"
#USERDATA_PATH = r"D:\Programs\Steam\userdata\1745541154\ugc\431960_subscriptions.vdf"
#CHECK = True
CHECK = True
ALLUSER = False
# ----------------------------------------------------


def find_folders_with_ugc(root_path:str|os.PathLike)->list[str|os.PathLike]:
    if not os.path.isdir(root_path):
        raise ValueError(f"路径 '{root_path}' 不存在或不是一个目录。")
    result = list()
    try:
        with os.scandir(root_path) as entries:
            for entry in entries:
                if entry.is_dir():
                    ugc_path = os.path.join(entry.path, 'ugc/431960_subscriptions.vdf')
                    if os.path.exists(ugc_path):
                        result.append(entry.name)
    except PermissionError as e:
        print(f"权限不足，无法访问 {root_path}: {e}")
    except OSError as e:
        print(f"操作系统错误: {e}")
    return result

def find_steam_path_via_registry()->str|os.PathLike:
    try:
        with OpenKey(HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam_path, _ = QueryValueEx(key, "SteamPath")
            return steam_path
    except FileNotFoundError:
        return None

def parse_subscribed_ids(vdf_path:str|os.PathLike)->list[str]:
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


def mul_parse_subscribed_ids(users:list[str|os.PathLike])->list[str]:
    """
    对于每个账户，从 subscriptions vdf 文件中提取订阅的 workshop ID 集合相加。
    """
    ids = set()
    for user in users:
        ids |= parse_subscribed_ids(user)
    return ids

def find_local_workshop_ids(path:str|os.PathLike)->list[str]:
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

def without_path_input()->str|os.PathLike:
    loc = find_steam_path_via_registry()
    print('选中steam路径',loc)
    return loc

def without_userdata_input(originpath)->str|os.PathLike:
    loc = originpath
    path = os.path.join(loc,"steamapps/workshop/content/431960")
    users = find_folders_with_ugc(os.path.join(loc,"userdata"))
    for i in range(len(users)):
        print(f"{i} : {users[i]}")
    try:
        n = input("输入编号")
        user = users[int(n)]
        userdata = "{}/userdata/{}/ugc/431960_subscriptions.vdf".format(loc,user)
    except:
        print("非法输入")
        exit()
    return userdata

def rm(orphan,path):
    deleted_count = 0
    for oid in orphan:
        target = os.path.join(path, oid)
        try:
            rmtree(target)
            deleted_count += 1
            print(f"已删除: {target}")
        except Exception as e:
            print(f"删除失败: {target} -> {e}")

    print(f"完成: 已删除 {deleted_count} 个目录。")

def main():
    p = argparse.ArgumentParser(description="删除 Wallpaper Engine 本地未订阅的 workshop 数据目录")
    p.add_argument("--path", help="本地steam路径,例如 D:/steam/userdata")
    p.add_argument("--userdata", help="subscriptions vdf 文件路径，例如 ...//431960_subscriptions.vdf")
    p.add_argument("--check", action="store_true", default=CHECK, help="仅查找并列出将被删除的目录，不执行删除")
    p.add_argument("--alluser",action="store_true",default=ALLUSER,help="仅选中不被当前steam保存的所有账户订阅的文件")
    args = p.parse_args()
    #python .\delete.py --path "D:\steam\steamapps\workshop\content\431960" --userdata "D:\steam\userdata\1525254305\ugc\431960_subscriptions.vdf"
    
    originpath : str|os.PathLike  = args.path
    userdata : str|os.PathLike = args.userdata
    check_only : bool = args.check
    all_user: bool = args.alluser

    if(not originpath):originpath = without_path_input()
    path = os.path.join(originpath,"steamapps/workshop/content/431960")
    if(not all_user and not userdata):userdata = without_userdata_input(originpath)
    
    
    try:
        if(all_user):
            userdata = ["{}/userdata/{}/ugc/431960_subscriptions.vdf".format(originpath,user) for user in find_folders_with_ugc(os.path.join(originpath,"userdata"))]
            subscribed = mul_parse_subscribed_ids(userdata)
        else:
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
        print(f" - {oid} -> {os.path.join(path, oid)}")

    if check_only:
        print("--check 模式，未执行删除。")
        return

    #执行删除
    rm(orphan=orphan,path=path)

if __name__ == "__main__":
    main()