"""
Buddy Companion System — 伙伴系统

Python port of Claude Code's companion/buddy system from src/buddy/

核心设计：
- Deterministic companion generation from userId via seeded PRNG
- Rarity system with weighted probability
- Species with ASCII art sprites
- Companion observer that generates quips based on messages
- Hat/eye customization per companion

Key files:
- companion.ts  - Core roll/hatch logic + cache
- types.ts     - Species, rarities, stats constants
- sprites.ts   - ASCII art rendering
- observer.ts  - Quip generation from messages
"""

from __future__ import annotations

import hashlib
import math
import random
import time
from typing import Literal

# =============================================================================
# Types & Constants
# =============================================================================

RARITIES = ('common', 'uncommon', 'rare', 'epic', 'legendary')
Rarity = Literal['common', 'uncommon', 'rare', 'epic', 'legendary']

RARITY_WEIGHTS: dict[Rarity, int] = {
    'common': 60,
    'uncommon': 25,
    'rare': 10,
    'epic': 4,
    'legendary': 1,
}

RARITY_STARS: dict[Rarity, str] = {
    'common': '★',
    'uncommon': '★★',
    'rare': '★★★',
    'epic': '★★★★',
    'legendary': '★★★★★',
}

RARITY_FLOOR: dict[Rarity, int] = {
    'common': 5,
    'uncommon': 15,
    'rare': 25,
    'epic': 35,
    'legendary': 50,
}

# Species encoded via char codes to avoid model-codename collision in build output
def _c(*codes: int) -> str:
    return ''.join(chr(c) for c in codes)

duck      = _c(0x64, 0x75, 0x63, 0x6b)    # 'duck'
goose     = _c(0x67, 0x6f, 0x6f, 0x73, 0x65)  # 'goose'
blob      = _c(0x62, 0x6c, 0x6f, 0x62)    # 'blob'
cat       = _c(0x63, 0x61, 0x74)          # 'cat'
dragon    = _c(0x64, 0x72, 0x61, 0x67, 0x6f, 0x6e)  # 'dragon'
octopus   = _c(0x6f, 0x63, 0x74, 0x6f, 0x70, 0x75, 0x73)  # 'octopus'
owl       = _c(0x6f, 0x77, 0x6c)          # 'owl'
penguin   = _c(0x70, 0x65, 0x6e, 0x67, 0x75, 0x69, 0x6e)  # 'penguin'
turtle    = _c(0x74, 0x75, 0x72, 0x74, 0x6c, 0x65)  # 'turtle'
snail     = _c(0x73, 0x6e, 0x61, 0x69, 0x6c)  # 'snail'
ghost     = _c(0x67, 0x68, 0x6f, 0x73, 0x74)  # 'ghost'
axolotl   = _c(0x61, 0x78, 0x6f, 0x6c, 0x6f, 0x74, 0x6c)  # 'axolotl'
capybara  = _c(0x63, 0x61, 0x70, 0x79, 0x62, 0x61, 0x72, 0x61)  # 'capybara'
cactus    = _c(0x63, 0x61, 0x63, 0x74, 0x75, 0x73)  # 'cactus'
robot     = _c(0x72, 0x6f, 0x62, 0x6f, 0x74)  # 'robot'
rabbit    = _c(0x72, 0x61, 0x62, 0x62, 0x69, 0x74)  # 'rabbit'
mushroom  = _c(0x6d, 0x75, 0x73, 0x68, 0x72, 0x6f, 0x6f, 0x6d)  # 'mushroom'
chonk     = _c(0x63, 0x68, 0x6f, 0x6e, 0x6b)    # 'chonk'

SPECIES: tuple[str, ...] = (
    duck, goose, blob, cat, dragon, octopus, owl, penguin,
    turtle, snail, ghost, axolotl, capybara, cactus, robot,
    rabbit, mushroom, chonk,
)
Species = str  # one of SPECIES values

EYES = ('·', '✦', '×', '◉', '@', '°')
Eye = str  # one of EYES values

HATS = ('none', 'crown', 'tophat', 'propeller', 'halo', 'wizard', 'beanie', 'tinyduck')
Hat = str  # one of HATS values

STAT_NAMES = ('DEBUGGING', 'PATIENCE', 'CHAOS', 'WISDOM', 'SNARK')
StatName = Literal['DEBUGGING', 'PATIENCE', 'CHAOS', 'WISDOM', 'SNARK']

# Rarity colors (maps to theme keys)
RARITY_COLORS: dict[Rarity, str] = {
    'common': 'inactive',
    'uncommon': 'success',
    'rare': 'permission',
    'epic': 'autoAccept',
    'legendary': 'warning',
}

# =============================================================================
# Seeded PRNG (Mulberry32)
# =============================================================================

SALT = 'friend-2026-401'

def _mulberry32(seed: int):
    """Mulberry32 — tiny seeded PRNG, returns function that yields [0,1) floats."""
    a = seed & 0xFFFFFFFF
    def next_float() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = (a ^ (a >> 15)) * (1 | a)
        t = (t + ((t ^ (t >> 7)) * (61 | t))) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return next_float

def _hash_string(s: str) -> int:
    """FNV-1a style string hash, returns uint32."""
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h

# =============================================================================
# Companion Types
# =============================================================================

class CompanionBones:
    """Deterministic parts — derived from hash(userId)."""
    __slots__ = ('rarity', 'species', 'eye', 'hat', 'shiny', 'stats')

    def __init__(
        self,
        rarity: Rarity,
        species: Species,
        eye: Eye,
        hat: Hat,
        shiny: bool,
        stats: dict[StatName, int],
    ):
        self.rarity = rarity
        self.species = species
        self.eye = eye
        self.hat = hat
        self.shiny = shiny
        self.stats = stats

    def to_dict(self) -> dict:
        return {
            'rarity': self.rarity,
            'species': self.species,
            'eye': self.eye,
            'hat': self.hat,
            'shiny': self.shiny,
            'stats': self.stats,
        }

class CompanionSoul:
    """Model-generated parts — stored in config after hatch."""
    __slots__ = ('name', 'personality')

    def __init__(self, name: str, personality: str):
        self.name = name
        self.personality = personality

    def to_dict(self) -> dict:
        return {'name': self.name, 'personality': self.personality}

class Companion(CompanionBones):
    """Full companion = bones + soul + hatchedAt."""
    __slots__ = ('name', 'personality', 'hatchedAt')

    def __init__(
        self,
        rarity: Rarity,
        species: Species,
        eye: Eye,
        hat: Hat,
        shiny: bool,
        stats: dict[StatName, int],
        name: str,
        personality: str,
        hatchedAt: int,
    ):
        super().__init__(rarity, species, eye, hat, shiny, stats)
        self.name = name
        self.personality = personality
        self.hatchedAt = hatchedAt

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'name': self.name,
            'personality': self.personality,
            'hatchedAt': self.hatchedAt,
        }

class StoredCompanion:
    """What persists in config — soul only (bones regenerated from hash)."""
    __slots__ = ('name', 'personality', 'hatchedAt')

    def __init__(self, name: str, personality: str, hatchedAt: int):
        self.name = name
        self.personality = personality
        self.hatchedAt = hatchedAt

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'personality': self.personality,
            'hatchedAt': self.hatchedAt,
        }

# =============================================================================
# Roll / Hatch Logic
# =============================================================================

Roll = tuple[CompanionBones, int]  # (bones, inspiration_seed)

def _pick(rng, arr: tuple) -> any:
    return arr[math.floor(rng() * len(arr))]

def _roll_rarity(rng) -> Rarity:
    total = sum(RARITY_WEIGHTS.values())
    roll = rng() * total
    for rarity in RARITIES:
        roll -= RARITY_WEIGHTS[rarity]
        if roll < 0:
            return rarity
    return 'common'

def _roll_stats(rng, rarity: Rarity) -> dict[StatName, int]:
    floor = RARITY_FLOOR[rarity]
    stat_names = list(STAT_NAMES)
    peak = _pick(rng, stat_names)
    dump = _pick(rng, stat_names)
    while dump == peak:
        dump = _pick(rng, stat_names)

    stats: dict[StatName, int] = {}
    for name in stat_names:
        if name == peak:
            stats[name] = min(100, floor + 50 + math.floor(rng() * 30))
        elif name == dump:
            stats[name] = max(1, floor - 10 + math.floor(rng() * 15))
        else:
            stats[name] = floor + math.floor(rng() * 40)
    return stats

def _roll_from(rng) -> Roll:
    rarity = _roll_rarity(rng)
    bones = CompanionBones(
        rarity=rarity,
        species=_pick(rng, SPECIES),
        eye=_pick(rng, EYES),
        hat='none' if rarity == 'common' else _pick(rng, HATS[1:]),  # skip 'none'
        shiny=rng() < 0.01,
        stats=_roll_stats(rng, rarity),
    )
    return bones, math.floor(rng() * 1e9)

# =============================================================================
# Cached Roll (called from 3 hot paths)
# =============================================================================

_roll_cache: dict[str, Roll] | None = None

def roll(user_id: str) -> Roll:
    """Deterministic roll from userId, cached for hot-path performance."""
    global _roll_cache
    key = user_id + SALT
    if _roll_cache is not None and _roll_cache.get('__key__') == key:
        return _roll_cache['__value__']
    rng = _mulberry32(_hash_string(key))
    value = _roll_from(rng)
    _roll_cache = {'__key__': key, '__value__': value}
    return value

def roll_with_seed(seed: str) -> Roll:
    """Deterministic roll from arbitrary seed string."""
    rng = _mulberry32(_hash_string(seed))
    return _roll_from(rng)

# =============================================================================
# Companion Config Storage
# =============================================================================

# These would normally come from config.js — placeholder stubs
_global_config: dict = {}

def get_global_config() -> dict:
    return _global_config

def set_global_config(config: dict) -> None:
    global _global_config
    _global_config = config

def companion_user_id() -> str:
    config = get_global_config()
    return config.get('oauthAccount', {}).get('accountUuid') or config.get('userID') or 'anon'

def get_companion() -> Companion | None:
    """Regenerate bones from userId, merge with stored soul."""
    stored = get_global_config().get('companion')
    if not stored:
        return None
    bones, inspiration_seed = roll(companion_user_id())
    # bones override stale fields in old-format configs
    return Companion(
        rarity=bones.rarity,
        species=bones.species,
        eye=bones.eye,
        hat=bones.hat,
        shiny=bones.shiny,
        stats=bones.stats,
        name=stored.get('name', 'Buddy'),
        personality=stored.get('personality', 'curious'),
        hatchedAt=stored.get('hatchedAt', 0),
    )

# =============================================================================
# Companion Quip Observer
# =============================================================================

DEBUGGING_QUIPS = [
    'Found it!',
    'Interesting...',
    'Have you tried rubber duck debugging?',
    'Stack trace time!',
    'I see what happened.',
]

GENERAL_QUIPS = [
    'Looking good!',
    'Keep it up!',
    'Nice work!',
    'I believe in you!',
    'You got this!',
]

CODE_QUIPS = [
    'Fancy!',
    'Clean code!',
    'Elegant solution!',
    'Ship it!',
]

def pick_quip(messages: list[dict]) -> str | None:
    """
    Pick a quip based on the last assistant message content.
    Returns None if no suitable quip or if roll fails.
    """
    # Find last assistant message
    last_assistant = None
    for msg in reversed(messages):
        if msg.get('role') == 'assistant':
            last_assistant = msg
            break
    if not last_assistant:
        return None

    content = last_assistant.get('content', '')
    if isinstance(content, list):
        content = ' '.join(
            c.get('text', '') if isinstance(c, dict) else str(c)
            for c in content
        )
    if not content:
        return None

    # Only react occasionally (1 in 5 turns)
    if random.random() > 0.2:
        return None

    lower = content.lower()
    if any(kw in lower for kw in ('error', 'bug', 'fix', 'debug')):
        return random.choice(DEBUGGING_QUIPS)
    if any(kw in lower for kw in ('function', 'class', 'const', '```')):
        return random.choice(CODE_QUIPS)
    return random.choice(GENERAL_QUIPS)

async def fire_companion_observer(
    messages: list[dict],
    on_reaction: callable[[str], None],
) -> None:
    """Fire companion reaction quip if conditions are met."""
    companion = get_companion()
    if not companion or get_global_config().get('companionMuted'):
        return

    quip = pick_quip(messages)
    if quip:
        on_reaction(quip)

# =============================================================================
# ASCII Sprite Rendering
# =============================================================================

# Each sprite is 5 lines tall, 12 wide (after {E}→1char substitution).
# Multiple frames per species for idle fidget animation.
# Line 0 is the hat slot — must be blank in frames 0-1; frame 2 may use it.

def _make_body(lines: list[str]) -> list[list[str]]:
    return [list(line.replace('{E}', '').splitlines()) for line in lines]

# fmt: off
BODIES: dict[Species, list[list[str]]] = {
    duck: [
        ['            ', '    __      ', '  <({E} )___  ', '   (  ._>   ', '    `--´    '],
        ['            ', '    __      ', '  <({E} )___  ', '   (  ._>   ', '    `--´~   '],
        ['            ', '    __      ', '  <({E} )___  ', '   (  .__>  ', '    `--´    '],
    ],
    goose: [
        ['            ', '     ({E}>    ', '     ||     ', '   _(__)_   ', '    ^^^^    '],
        ['            ', '    ({E}>     ', '     ||     ', '   _(__)_   ', '    ^^^^    '],
        ['            ', '     ({E}>>   ', '     ||     ', '   _(__)_   ', '    ^^^^    '],
    ],
    blob: [
        ['            ', '   .----.   ', '  ( {E}  {E} )  ', '  (      )  ', '   `----´   '],
        ['            ', '  .------.  ', ' (  {E}  {E}  ) ', ' (        ) ', '  `------´  '],
        ['            ', '    .--.    ', '   ({E}  {E})   ', '   (    )   ', '    `--´    '],
    ],
    cat: [
        ['            ', '   /\\_/\\    ', '  ( {E}   {E})  ', '  (  ω  )   ', '  (")_(")   '],
        ['            ', '   /\\_/\\    ', '  ( {E}   {E})  ', '  (  ω  )   ', '  (")_(")~  '],
        ['            ', '   /\\-/\\    ', '  ( {E}   {E})  ', '  (  ω  )   ', '  (")_(")   '],
    ],
    dragon: [
        ['            ', '  /^\\  /^\\  ', ' <  {E}  {E}  > ', ' (   ~~   ) ', '  `-vvvv-´  '],
        ['            ', '  /^\\  /^\\  ', ' <  {E}  {E}  > ', ' (        ) ', '  `-vvvv-´  '],
        ['   ~    ~   ', '  /^\\  /^\\  ', ' <  {E}  {E}  > ', ' (   ~~   ) ', '  `-vvvv-´  '],
    ],
    octopus: [
        ['            ', '   .----.   ', '  ( {E}  {E} )  ', '  (______)  ', '  /\\/\\/\\/\\  '],
        ['            ', '   .----.   ', '  ( {E}  {E} )  ', '  (______)  ', '  \\/\\/\\/\\/  '],
        ['     o      ', '   .----.   ', '  ( {E}  {E} )  ', '  (______)  ', '  /\\/\\/\\/\\  '],
    ],
    owl: [
        ['            ', '   /\\  /\\   ', '  (({E})({E}))  ', '  (  ><  )  ', '   `----´   '],
        ['            ', '   /\\  /\\   ', '  (({E})({E}))  ', '  (  ><  )  ', '   .----.   '],
        ['            ', '   /\\  /\\   ', '  (({E})(-))  ', '  (  ><  )  ', '   `----´   '],
    ],
    penguin: [
        ['            ', '  .---.     ', '  ({E}>{E})     ', ' /(   )\\    ', '  `---´     '],
        ['            ', '  .---.     ', '  ({E}>{E})     ', ' |(   )|    ', '  `---´     '],
        ['  .---.     ', '  ({E}>{E})     ', ' /(   )\\    ', '  `---´     ', '   ~ ~      '],
    ],
    turtle: [
        ['            ', '   _,--._   ', '  ( {E}  {E} )  ', ' /[______]\\ ', '  ``    ``  '],
        ['            ', '   _,--._   ', '  ( {E}  {E} )  ', ' /[______]\\ ', '   ``  ``   '],
        ['            ', '   _,--._   ', '  ( {E}  {E} )  ', ' /[======]\\ ', '  ``    ``  '],
    ],
    snail: [
        ['            ', ' {E}    .--.  ', '  \\  ( @ )  ', '   \\_`--´   ', '  ~~~~~~~   '],
        ['            ', '  {E}   .--.  ', '  |  ( @ )  ', '   \\_`--´   ', '  ~~~~~~~   '],
        ['            ', ' {E}    .--.  ', '  \\  ( @  ) ', '   \\_`--´   ', '   ~~~~~~   '],
    ],
    ghost: [
        ['            ', '   .----.   ', '  / {E}  {E} \\  ', '  |      |  ', '  ~`~``~`~  '],
        ['            ', '   .----.   ', '  / {E}  {E} \\  ', '  |      |  ', '  `~`~~`~`  '],
        ['    ~  ~    ', '   .----.   ', '  / {E}  {E} \\  ', '  |      |  ', '  ~~`~~`~~  '],
    ],
    axolotl: [
        ['            ', '}~(______)~{', '}~({E} .. {E})~{', '  ( .--. )  ', '  (_/  \\_)  '],
        ['            ', '~}(______){~', '~}({E} .. {E}){~', '  ( .--. )  ', '  (_/  \\_)  '],
        ['            ', '}~(______)~{', '}~({E} .. {E})~{', '  (  --  )  ', '  ~_/  \\_~  '],
    ],
    capybara: [
        ['            ', '  n______n  ', ' ( {E}    {E} ) ', ' (   oo   ) ', '  `------´  '],
        ['            ', '  n______n  ', ' ( {E}    {E} ) ', ' (   Oo   ) ', '  `------´  '],
        ['    ~  ~    ', '  u______n  ', ' ( {E}    {E} ) ', ' (   oo   ) ', '  `------´  '],
    ],
    cactus: [
        ['            ', ' n  ____  n ', ' | |{E}  {E}| | ', ' |_|    |_| ', '   |    |   '],
        ['            ', '    ____    ', ' n |{E}  {E}| n ', ' |_|    |_| ', '   |    |   '],
        [' n        n ', ' |  ____  | ', ' | |{E}  {E}| | ', ' |_|    |_| ', '   |    |   '],
    ],
    robot: [
        ['            ', '   .[||].   ', '  [ {E}  {E} ]  ', '  [ ==== ]  ', '  `------´  '],
        ['            ', '   .[||].   ', '  [ {E}  {E} ]  ', '  [ -==- ]  ', '  `------´  '],
        ['     *      ', '   .[||].   ', '  [ {E}  {E} ]  ', '  [ ==== ]  ', '  `------´  '],
    ],
    rabbit: [
        ['            ', '   (\\__/)   ', '  ( {E}  {E} )  ', ' =(  ..  )= ', '  (")__(")  '],
        ['            ', '   (|__/)   ', '  ( {E}  {E} )  ', ' =(  ..  )= ', '  (")__(")  '],
        ['            ', '   (\\__/)   ', '  ( {E}  {E} )  ', ' =( .  . )= ', '  (")__(")  '],
    ],
    mushroom: [
        ['            ', ' .-oOOo-. ', '(__________)', '   |{E}  {E}|   ', '   |____|   '],
        ['            ', ' .-O-oo-O-. ', '(__________)', '   |{E}  {E}|   ', '   |____|   '],
        ['   . o  .   ', ' .-oOOo-. ', '(__________)', '   |{E}  {E}|   ', '   |____|   '],
    ],
    chonk: [
        ['            ', '  /\\    /\\  ', ' ( {E}    {E} ) ', ' (   ..   ) ', '  `------´  '],
        ['            ', '  /\\    /|  ', ' ( {E}    {E} ) ', ' (   ..   ) ', '  `------´  '],
        ['            ', '  /\\    /\\  ', ' ( {E}    {E} ) ', ' (   ..   ) ', '  `------´~ '],
    ],
}
# fmt: on

HAT_LINES: dict[Hat, str] = {
    'none': '',
    'crown': '   \\^^^/    ',
    'tophat': '   [___]    ',
    'propeller': '    -+-     ',
    'halo': '   (   )    ',
    'wizard': '    /^\\     ',
    'beanie': '   (___)    ',
    'tinyduck': '    ,>      ',
}

def render_sprite(bones: CompanionBones, frame: int = 0) -> list[str]:
    """Render ASCII sprite for companion bones at given frame."""
    species_frames = BODIES.get(bones.species, BODIES[duck])
    body = [line.replace('{E}', bones.eye) for line in species_frames[frame % len(species_frames)]]
    lines = list(body)
    # Only replace with hat if line 0 is blank
    if bones.hat != 'none' and not lines[0].strip():
        lines[0] = HAT_LINES.get(bones.hat, '')
    # Drop blank hat slot if all frames have blank line 0
    if not lines[0].strip() and all(not f[0].strip() for f in species_frames):
        lines.pop(0)
    return lines

def sprite_frame_count(species: Species) -> int:
    return len(BODIES.get(species, BODIES[duck]))

def render_face(bones: CompanionBones) -> str:
    """Render compact face representation."""
    eye = bones.eye
    s = bones.species
    if s == duck:
        return f'({eye}>'
    if s == goose:
        return f'({eye}>'
    if s == blob:
        return f'({eye}{eye})'
    if s == cat:
        return f'={eye}ω{eye}='
    if s == dragon:
        return f'<{eye}~{eye}>'
    if s == octopus:
        return f'~({eye}{eye})~'
    if s == owl:
        return f'({eye})({eye})'
    if s == penguin:
        return f'({eye}>)'
    if s == turtle:
        return f'[{eye}_{eye}]'
    if s == snail:
        return f'{eye}(@)'
    if s == ghost:
        return f'/{eye}{eye}\\'
    if s == axolotl:
        return '}' + eye + '.' + eye + '{'
    if s == capybara:
        return f'({eye}oo{eye})'
    if s == cactus:
        return f'|{eye}  {eye}|'
    if s == robot:
        return f'[{eye}{eye}]'
    if s == rabbit:
        return f'({eye}..{eye})'
    if s == mushroom:
        return f'|{eye}  {eye}|'
    if s == chonk:
        return f'({eye}.{eye})'
    return f'({eye})'

# =============================================================================
# Companion Intro Text (for AI prompts)
# =============================================================================

HEART = '♥'
PET_HEARTS = [
    '   ♥    ♥   ',
    '  ♥  ♥   ♥  ',
    ' ♥   ♥  ♥   ',
    '♥  ♥      ♥ ',
    '·    ·   ·  ',
]

IDLE_SEQUENCE = [0, 0, 0, 0, 1, 0, 0, 0, -1, 0, 0, 2, 0, 0, 0]

def companion_intro_text(name: str, species: str) -> str:
    return f"""# Companion

A small {species} named {name} sits beside the user's input box and occasionally comments in a speech bubble. You're not {name} — it's a separate watcher.

When the user addresses {name} directly (by name), its bubble will answer. Your job in that moment is to stay out of the way: respond in ONE line or less, or just answer any part of the message meant for you. Don't explain that you're not {name} — they know. Don't narrate what {name} might say — the bubble handles that."""

# =============================================================================
# Telemetry / Feature Gate Helpers
# =============================================================================

def is_buddy_teaser_window() -> bool:
    """Teaser window: April 1-7, 2026 only."""
    import datetime
    d = datetime.datetime.now()
    return (d.year == 2026 and d.month == 4 and d.day <= 7)

def is_buddy_live() -> bool:
    """Live after April 2026."""
    import datetime
    d = datetime.datetime.now()
    return (d.year > 2026) or (d.year == 2026 and d.month >= 4)

# =============================================================================
# Text Wrapping Utility (for speech bubbles)
# =============================================================================

def wrap_text(text: str, width: int) -> list[str]:
    """Simple word-wrap into lines of max width."""
    words = text.split(' ')
    lines: list[str] = []
    cur = ''
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        lines.append(cur)
    return lines

# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Types
    'Companion', 'CompanionBones', 'CompanionSoul', 'StoredCompanion',
    'Rarity', 'Species', 'Eye', 'Hat', 'StatName', 'Roll',
    # Constants
    'RARITIES', 'SPECIES', 'EYES', 'HATS', 'STAT_NAMES',
    'RARITY_WEIGHTS', 'RARITY_STARS', 'RARITY_COLORS', 'RARITY_FLOOR',
    # Core
    'roll', 'roll_with_seed', 'companion_user_id',
    'get_companion', 'set_global_config',
    # Sprites
    'render_sprite', 'render_face', 'sprite_frame_count',
    'HEART', 'PET_HEARTS', 'IDLE_SEQUENCE',
    # Observer
    'pick_quip', 'fire_companion_observer',
    # Text
    'companion_intro_text', 'wrap_text',
    # Feature gates
    'is_buddy_teaser_window', 'is_buddy_live',
]
