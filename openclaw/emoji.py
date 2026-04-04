"""
Emoji - 表情
基于 Claude Code emoji.ts 设计

表情符号工具。
"""


def emoji(name: str) -> str:
    """
    获取emoji
    
    Args:
        name: emoji名称
        
    Returns:
        emoji字符
    """
    emojis = {
        # 状态
        "rocket": "🚀",
        "fire": "🔥",
        "sparkles": "✨",
        "star": "⭐",
        "warning": "⚠️",
        "error": "❌",
        "check": "✅",
        "x": "❌",
        
        # 动物
        "cat": "🐱",
        "dog": "🐕",
        "bird": "🐦",
        "fish": "🐟",
        "bug": "🐛",
        "snake": "🐍",
        
        # 食物
        "apple": "🍎",
        "banana": "🍌",
        "rice": "🍚",
        "coffee": "☕",
        "beer": "🍺",
        "wine": "🍷",
        "pizza": "🍕",
        "burger": "🍔",
        "fries": "🍟",
        "sushi": "🍣",
        
        # 天气
        "sun": "☀️",
        "cloud": "☁️",
        "rain": "🌧️",
        "snow": "❄️",
        "thunder": "⛈️",
        
        # 技术
        "computer": "💻",
        "phone": "📱",
        "tv": "📺",
        "camera": "📷",
        "floppy": "💾",
        "cd": "💿",
        "satellite": "🛰️",
        
        # 金融
        "money": "💰",
        "dollar": "💵",
        "chart": "📈",
        "chart_down": "📉",
        
        # 常用
        "clock": "🕐",
        "calendar": "📅",
        "mail": "📧",
        "inbox": "📥",
        "outbox": "📤",
        "book": "📖",
        "pen": "🖊️",
        "paper": "📄",
        "key": "🔑",
        "lock": "🔒",
        "unlock": "🔓",
        
        # 手势
        "thumbs_up": "👍",
        "thumbs_down": "👎",
        "clap": "👏",
        "wave": "👋",
        "point_right": "👉",
        "point_left": "👈",
        "pray": "🙏",
        
        # 情绪
        "smile": "😊",
        "laugh": "😄",
        "cry": "😢",
        "angry": "😠",
        "heart": "❤️",
        "broken_heart": "💔",
        "eyes": "👀",
        "brain": "🧠",
        
        # 蛋蛋专用
        "egg": "🥚",
        "hatched": "🐣",
    }
    
    return emojis.get(name, f":{name}:")


def random_emoji() -> str:
    """随机emoji"""
    import random
    emojis_list = [
        "🚀", "🔥", "✨", "⭐", "⚡", "🌈", "💫", "🎯",
        "💡", "🔮", "🏆", "🎪", "🎭", "🎨", "🎬",
        "🐱", "🐶", "🦊", "🦁", "🐼", "🐨", "🐯",
        "🍎", "🍕", "🍜", "☕", "🎂", "🍰",
        "📱", "💻", "⌚", "🎮", "📷", "🎧",
        "❤️", "💖", "💝", "💘", "💕",
        "👍", "👏", "🙌", "🙏", "💪",
    ]
    return random.choice(emojis_list)


# 导出
__all__ = [
    "emoji",
    "random_emoji",
]
