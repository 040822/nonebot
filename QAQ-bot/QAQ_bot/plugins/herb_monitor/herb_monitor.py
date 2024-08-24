from nonebot import on_command
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
import re
import json

# 加载或初始化用户数据
try:
    with open("user_data.json", "r", encoding="utf-8") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

# 保存用户数据到文件
def save_user_data():
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

# 完整药材价格字典
herb_prices = {
    # ... 请在这里添加完整的药材价格字典 ...
}

# 获取药材价格
def get_herb_price(name):
    return herb_prices.get(name, None)

# 监听器
matcher = on_message(rule=to_me(), priority=5)

@matcher.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    # 解析药材信息
    message_text = str(event.message).strip()
    group_id = str(event.group_id)
    user_id = str(event.user_id)

    # 检查用户是否在数据中，如果不在则初始化
    if group_id not in user_data:
        user_data[group_id] = {"ignored_user": None}
    if user_id not in user_data[group_id]:
        user_data[group_id][user_id] = {"monitoring": True, "warn_count": 0, "last_quantity": {}}

    # 检查是否@了特殊用户
    at_pattern = re.compile(r'@(\d+)')
    at_users = at_pattern.findall(message_text)
    for at_user in at_users:
        if at_user != user_data[group_id]["ignored_user"]:
            await matcher.send(f"是否记忆忽略用户 {at_user} 的药材监测？")
            state["at_user"] = at_user  # 保存状态以便后续处理
            break  # 只处理第一个@的用户

    # 监测药材数量变化
    if "坊市上架" in message_text:
        # 提取药材名称和数量
        name_pattern = re.compile(r'名字：([^\n]+)(?=\s+品级：|$)')
        quantity_pattern = re.compile(r'拥有数量：(\d+)')

        names = name_pattern.findall(message_text)
        quantities = quantity_pattern.findall(message_text)

        for name, quantity in zip(names, quantities):
            current_quantity = int(quantity)
            if user_id == user_data[group_id]["ignored_user"]:
                continue  # 忽略特殊用户
            last_quantity = user_data[group_id][user_id]["last_quantity"].get(name, 0)

            if current_quantity > last_quantity:
                user_data[group_id][user_id]["warn_count"] += 1
                if user_data[group_id][user_id]["warn_count"] == 1:
                    await matcher.send(f"{name} 数量上升，请注意！")
                elif user_data[group_id][user_id]["warn_count"] == 2:
                    await matcher.send(f"{name} 数量再次上升，将对您进行禁言处理。")
                    # 实现禁言功能
                    # await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=600)
            elif current_quantity < last_quantity:
                diff = last_quantity - current_quantity
                price = get_herb_price(name)
                if price is not None:
                    await matcher.send(f"{name} 数量下降，请补充 {diff * price} 金币。")

            user_data[group_id][user_id]["last_quantity"][name] = current_quantity

        save_user_data()

# 处理记忆用户
memory_matcher = on_message(rule=to_me(), priority=5)

@memory_matcher.handle()
async def handle_memory(bot: Bot, event: GroupMessageEvent, state: T_State):
    message_text = str(event.message).strip()
    at_user = state.get("at_user")
    if at_user and message_text.lower() == "记忆":
        user_data[group_id]["ignored_user"] = at_user
        await memory_matcher.send(f"已记忆忽略用户 {at_user} 的药材监测。")
        save_user_data()

# 开启/关闭监测功能
monitoring_matcher = on_message(rule=to_me(), priority=5)

@monitoring_matcher.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    message_text = str(event.message).strip().lower()
    group_id = str(event.group_id)
    user_id = str(event.user_id)

    if "开启监测" in message_text:
        user_data[group_id][user_id]["monitoring"] = True
        await monitoring_matcher.send("已开启监测功能。")
    elif "关闭监测" in message_text:
        user_data[group_id][user_id]["monitoring"] = False
        await monitoring_matcher.send("已关闭监测功能。")
    else:
        await monitoring_matcher.send("未知命令，请使用'开启监测'或'关闭监测'。")

    save_user_data()