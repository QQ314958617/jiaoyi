"""
OpenClaw Random Word Slug Generator
================================
Inspired by Claude Code's src/utils/words.ts.

随机单词 slug 生成器，支持：
1. 生成 adjective-verb-noun 格式
2. 生成 adjective-noun 格式
3. 密码学安全的随机性
"""

from __future__ import annotations

import secrets, random

# ============================================================================
# 形容词列表（来自 Claude Code）
# ============================================================================

ADJECTIVES = [
    "abundant", "ancient", "bright", "calm", "cheerful", "clever", "cozy", "curious",
    "dapper", "dazzling", "deep", "delightful", "eager", "elegant", "enchanted",
    "fancy", "fluffy", "gentle", "gleaming", "golden", "graceful", "happy", "hidden",
    "humble", "jolly", "joyful", "keen", "kind", "lively", "lovely", "lucky",
    "luminous", "magical", "majestic", "mellow", "merry", "mighty", "misty",
    "noble", "peaceful", "playful", "polished", "precious", "proud", "quiet",
    "quirky", "radiant", "rosy", "serene", "shiny", "silly", "sleepy", "smooth",
    "snazzy", "snug", "soft", "sparkling", "spicy", "splendid", "sprightly",
    "starry", "steady", "sunny", "swift", "tender", "tidy", "toasty", "tranquil",
    "twinkly", "valiant", "vast", "velvet", "vivid", "warm", "whimsical", "wild",
    "wise", "witty", "wondrous", "zany", "zesty", "zippy",
    # 更多
    "breezy", "bubbly", "buzzing", "cheeky", "cosmic", "crispy", "crystalline",
    "cuddly", "dreamy", "effervescent", "ethereal", "fizzy", "flickering", "floating",
    "frolicking", "fuzzy", "giggly", "glimmering", "glistening", "glittery", "glowing",
    "goofy", "groovy", "harmonic", "hazy", "humming", "iridescent", "jaunty", "jazzy",
    "jiggly", "melodic", "moonlit", "mossy", "nifty", "peppy", "prancy",
    "rippling", "rustling", "shimmering", "shimmying", "snappy", "squishy", "swirling",
    "ticklish", "tingly", "twinkling", "velvety", "wiggly", "wobbly", "zazzy",
    # 编程概念
    "abstract", "adaptive", "agile", "async", "atomic", "binary", "cached",
    "compiled", "concurrent", "cryptic", "curried", "declarative", "delegated",
    "distributed", "dynamic", "elegant", "encapsulated", "enumerated", "eventual",
    "expressive", "federated", "functional", "generic", "greedy", "hashed",
    "idempotent", "immutable", "imperative", "indexed", "inherited", "iterative",
    "lazy", "lexical", "linear", "linked", "logical", "memoized", "modular",
    "mutable", "nested", "optimized", "parallel", "parsed", "partitioned",
    "polymorphic", "pure", "reactive", "recursive", "refactored", "reflective",
    "replicated", "resilient", "robust", "scalable", "sequential", "serialized",
    "sharded", "sorted", "stateful", "stateless", "streamed", "structured",
    "synchronous", "temporal", "transient", "typed", "unified", "validated",
]

# ============================================================================
# 动词列表
# ============================================================================

VERBS = [
    "baking", "beaming", "booping", "bouncing", "brewing", "bubbling", "chasing",
    "churning", "coalescing", "conjuring", "cooking", "crafting", "crunching",
    "cuddling", "dancing", "dazzling", "discovering", "doodling", "dreaming",
    "drifting", "enchanting", "exploring", "finding", "floating", "fluttering",
    "foraging", "forging", "frolicking", "gathering", "giggling", "gliding",
    "greeting", "growing", "hatching", "herding", "honking", "hopping", "hugging",
    "humming", "imagining", "inventing", "jingling", "juggling", "jumping",
    "kindling", "knitting", "launching", "leaping", "mapping", "marinating",
    "meandering", "mixing", "moseying", "munching", "napping", "nibbling",
    "noodling", "orbiting", "painting", "percolating", "petting", "plotting",
    "pondering", "popping", "prancing", "purring", "puzzling", "questing",
    "riding", "roaming", "rolling", "scribbling", "seeking", "shimmying",
    "singing", "skipping", "sleeping", "snacking", "sniffing", "snuggling",
    "soaring", "sparking", "spinning", "splashing", "sprouting", "squishing",
    "stargazing", "stirring", "strolling", "swimming", "swinging", "tickling",
    "tinkering", "toasting", "tumbling", "twirling", "waddling", "wandering",
    "watching", "weaving", "whistling", "wiggling", "wishing", "wobbling",
    "wondering", "yawning", "zooming",
]

# ============================================================================
# 名词列表
# ============================================================================

NOUNS = [
    # 自然和宇宙
    "aurora", "blossom", "breeze", "brook", "bubble", "canyon", "cascade",
    "cloud", "clover", "comet", "coral", "cosmos", "crescent", "crystal",
    "dawn", "dewdrop", "dusk", "eclipse", "ember", "feather", "fern",
    "firefly", "flame", "flurry", "fog", "forest", "frost", "galaxy",
    "garden", "glacier", "glade", "grove", "harbor", "horizon", "island",
    "lagoon", "lake", "leaf", "lightning", "meadow", "meteor", "mist",
    "moon", "moonbeam", "mountain", "nebula", "nova", "ocean", "orbit",
    "pebble", "petal", "pine", "planet", "pond", "puddle", "quasar",
    "rain", "rainbow", "reef", "ripple", "river", "shore", "sky",
    "snowflake", "spark", "spring", "star", "stardust", "starlight",
    "storm", "stream", "summit", "sun", "sunbeam", "sunrise", "sunset",
    "thunder", "tide", "twilight", "valley", "volcano", "waterfall",
    "wave", "willow", "wind",
    # 可爱动物
    "alpaca", "axolotl", "badger", "bear", "beaver", "bee", "bird",
    "bunny", "cat", "chipmunk", "crab", "crane", "deer", "dolphin",
    "dove", "dragon", "dragonfly", "duckling", "eagle", "elephant",
    "falcon", "finch", "flamingo", "fox", "frog", "giraffe", "goose",
    "hamster", "hare", "hedgehog", "hippo", "hummingbird", "jellyfish",
    "kitten", "koala", "ladybug", "lark", "lemur", "llama", "lobster",
    "lynx", "manatee", "meerkat", "moth", "narwhal", "newt", "octopus",
    "otter", "owl", "panda", "parrot", "peacock", "pelican", "penguin",
    "phoenix", "piglet", "platypus", "pony", "porcupine", "puffin",
    "puppy", "quail", "quokka", "rabbit", "raccoon", "raven", "robin",
    "salamander", "seahorse", "seal", "sloth", "snail", "sparrow",
    "sphinx", "squid", "squirrel", "starfish", "swan", "tiger", "toucan",
    "turtle", "unicorn", "walrus", "whale", "wolf", "wombat", "wren",
    # 物品
    "acorn", "anchor", "balloon", "beacon", "biscuit", "blanket",
    "book", "boot", "cake", "candle", "candy", "castle", "charm",
    "clock", "cocoa", "cookie", "crayon", "crown", "cupcake", "donut",
    "dream", "fairy", "fiddle", "flask", "flute", "fountain", "gadget",
    "gem", "gizmo", "globe", "goblet", "hammock", "harp", "haven",
    "hearth", "honey", "journal", "kazoo", "kettle", "key", "kite",
    "lantern", "lemon", "lighthouse", "locket", "lollipop", "map",
    "marble", "marshmallow", "melody", "mitten", "muffin", "music",
    "nest", "noodle", "oasis", "origami", "pancake", "parasol", "peach",
    "pearl", "pie", "pillow", "pinwheel", "pixel", "pizza", "plum",
    "popcorn", "pretzel", "prism", "pudding", "pumpkin", "puzzle",
    "rocket", "rose", "scone", "scroll", "shell", "sketch", "snowglobe",
    "sparkle", "spindle", "sprout", "sundae", "swing", "taco", "teacup",
    "teapot", "thimble", "toast", "token", "tome", "tower", "treasure",
    "treehouse", "trinket", "truffle", "tulip", "umbrella", "waffle",
    "wand", "whisper", "whistle", "widget", "wreath",
]

# 计算机科学家
SCIENTISTS = [
    "turing", "hopper", "knuth", "bachman", "babbage", "boole", "codd",
    "chandrasekhar", "church", "conway", "cook", "cray", "curry", "dahl",
    "dijkstra", "dongarra", "eich", "engelbart", "floyd", "gosling",
    "graham", "gray", "hamming", "hennessy", "hinton", "hoare", "hopper",
    "kay", "kernighan", "lamport", "lecun", "lovelace", "mccarthy",
    "metcalfe", "milner", "minsky", "moore", "naur", "neumann", "newell",
    "nygaard", "perl", "pike", "rabin", "ritchie", "rivest", "rossum",
    "scott", "sedgwick", "shamir", "shannon", "simon", "stallman",
    "stroustrup", "sutherland", "tarjan", "thompson", "torvalds",
    "ullman", "valiant", "wall", "wirth",
]

# ============================================================================
# 生成器
# ============================================================================

def _random_int(max_value: int) -> int:
    """生成密码学安全的随机整数"""
    return secrets.randbelow(max_value)

def _pick_random(array: list) -> str:
    """从数组中随机选择一个元素"""
    return array[_random_int(len(array))]

def generate_word_slug() -> str:
    """
    生成随机单词 slug（格式: adjective-verb-noun）
    
    Example:
        "gleaming-brewing-phoenix"
        "cosmic-pondering-lighthouse"
    """
    adjective = _pick_random(ADJECTIVES)
    verb = _pick_random(VERBS)
    noun = _pick_random(NOUNS)
    return f"{adjective}-{verb}-{noun}"

def generate_short_word_slug() -> str:
    """
    生成短随机单词 slug（格式: adjective-noun）
    
    Example:
        "graceful-unicorn"
        "cosmic-lighthouse"
    """
    adjective = _pick_random(ADJECTIVES)
    noun = _pick_random(NOUNS)
    return f"{adjective}-{noun}"

def generate_scientist_slug() -> str:
    """
    生成科学家主题 slug（格式: adjective-scientist）
    
    Example:
        "quantum-turing"
        "elegant-knuth"
    """
    adjective = _pick_random(ADJECTIVES)
    scientist = _pick_random(SCIENTISTS)
    return f"{adjective}-{scientist}"

def generate_id(prefix: str = "") -> str:
    """
    生成随机 ID
    
    Args:
        prefix: 前缀
    
    Returns:
        格式: {prefix}-{adjective}-{noun}-{random}
    """
    adjective = _pick_random(ADJECTIVES)
    noun = _pick_random(NOUNS)
    random_part = secrets.token_hex(2)
    if prefix:
        return f"{prefix}-{adjective}-{noun}-{random_part}"
    return f"{adjective}-{noun}-{random_part}"

def generate_words(count: int = 3) -> list[str]:
    """
    生成多个随机单词
    
    Args:
        count: 生成数量（最多 3 个）
    
    Returns:
        单词列表
    """
    count = min(count, 3)
    if count == 1:
        return [_pick_random(ADJECTIVES)]
    elif count == 2:
        return [_pick_random(ADJECTIVES), _pick_random(NOUNS)]
    else:
        return [
            _pick_random(ADJECTIVES),
            _pick_random(VERBS),
            _pick_random(NOUNS),
        ]
