import random

import config
from objects import projectile

# 강화 정의와 적용. 스탯형은 apply(player)로 플레이어 수치를 바꾸고,
# 조건부 효과는 플레이어가 부르는 훅(on_parry_success, on_attack, on_dash_end)에서 보유 여부를 보고 처리한다


class Upgrade:
    def __init__(self, key, category, name, icon, desc, apply=None):
        self.key = key
        self.category = category
        self.name = name
        self.icon = icon   # HUD 아이콘에 들어가는 두 글자
        self.desc = desc   # 줄바꿈(\n)으로 카드에 여러 줄 표시
        self.apply = apply


def percent(mult):
    return round(abs(mult - 1) * 100)


def apply_parry_window(p):
    p.parry_window += config.UPGRADE_PARRY_WINDOW_BONUS


def apply_reflect(p):
    p.reflect_damage_mult = config.UPGRADE_REFLECT_MULT


def apply_max_hp(p):
    bonus = min(config.UPGRADE_MAX_HP_BONUS, config.HP_MAX - p.max_hp)
    p.max_hp += bonus
    p.hp += bonus


def apply_attack(p):
    p.attack_mult *= config.UPGRADE_ATTACK_MULT


def apply_invincible(p):
    p.invincible_on_hit += config.UPGRADE_INVINCIBLE_BONUS


def apply_double_jump(p):
    p.max_jumps = config.UPGRADE_MAX_JUMPS


def apply_dash_dist(p):
    p.dash_dist *= config.UPGRADE_DASH_DIST_MULT


def apply_dash_cooldown(p):
    p.dash_cooldown_time *= config.UPGRADE_DASH_COOLDOWN_MULT


ALL = [
    Upgrade('parry_window', 'parry', '예리한 감각', '판정',
            f'패링 판정 시간\n+{config.UPGRADE_PARRY_WINDOW_BONUS}초', apply_parry_window),
    Upgrade('parry_wave', 'parry', '반격의 검기', '검기', '패링 성공 시\n전방으로 검기 발사'),
    Upgrade('reflect', 'parry', '되받아치기', '반사',
            f'반사 투사체 피해\n{config.UPGRADE_REFLECT_MULT:g}배', apply_reflect),
    Upgrade('parry_heal', 'parry', '흡수', '회복', f'패링 성공 시\n체력 {config.UPGRADE_PARRY_HEAL} 회복'),
    Upgrade('max_hp', 'stat', '강인한 몸', '체력', f'최대 체력\n+{config.UPGRADE_MAX_HP_BONUS}', apply_max_hp),
    Upgrade('attack', 'stat', '날 선 검', '공격',
            f'공격력\n+{percent(config.UPGRADE_ATTACK_MULT)}%', apply_attack),
    Upgrade('finisher', 'stat', '마무리 일격', '3타',
            f'3타째 피해\n+{percent(config.UPGRADE_ATTACK3_MULT)}%'),
    Upgrade('invincible', 'stat', '불굴', '무적',
            f'피격 후 무적 시간\n+{config.UPGRADE_INVINCIBLE_BONUS}초', apply_invincible),
    Upgrade('double_jump', 'util', '2단 점프', '점프', '공중에서\n한 번 더 점프', apply_double_jump),
    Upgrade('dash_dist', 'util', '질풍', '거리',
            f'대시 거리\n+{percent(config.UPGRADE_DASH_DIST_MULT)}%', apply_dash_dist),
    Upgrade('dash_cooldown', 'util', '순보', '쿨감',
            f'대시 쿨타임\n-{percent(config.UPGRADE_DASH_COOLDOWN_MULT)}%', apply_dash_cooldown),
    Upgrade('dash_strike', 'util', '기습', '기습',
            f'대시 후 첫 공격\n피해 {config.UPGRADE_DASH_ATTACK_MULT:g}배'),
]
BY_KEY = {u.key: u for u in ALL}


def has(player, key):
    return key in player.upgrades


def roll_choices(player):
    # 이미 가진 것을 빼고 카테고리별로 하나씩 먼저 뽑은 뒤 남은 자리를 무작위로 채운다
    pool = [u for u in ALL if not has(player, u.key)]
    choices = []
    for category in config.UPGRADE_CATEGORIES:
        candidates = [u for u in pool if u.category == category]
        if candidates and len(choices) < config.UPGRADE_CHOICES:
            choices.append(random.choice(candidates))
    rest = [u for u in pool if u not in choices]
    choices += random.sample(rest, min(len(rest), config.UPGRADE_CHOICES - len(choices)))
    random.shuffle(choices)
    return choices


def apply(player, upgrade):
    player.upgrades.append(upgrade.key)
    if upgrade.apply:
        upgrade.apply(player)


def on_parry_success(player, target):
    if has(player, 'parry_heal'):
        player.hp = min(player.max_hp, player.hp + config.UPGRADE_PARRY_HEAL)
    if has(player, 'parry_wave'):
        wave = config.SWORD_WAVE
        p = projectile.fire(player.x, player.y + config.PLAYER_H / 2, player.face_dir, 0,
                            wave['speed'], wave['damage'], False, player.platforms, wave, owner=player)
        p.reflected = True   # 처음부터 플레이어 소유


def on_attack(player):
    # 한 번 휘두를 때의 추가 배율 (공격 시작 시 정한다)
    mult = 1.0
    if has(player, 'finisher') and player.swing_count % 3 == 0:   # T29: 3연타 → 단타 3번째마다
        mult *= config.UPGRADE_ATTACK3_MULT
    if has(player, 'dash_strike') and player.dash_strike_ready:
        player.dash_strike_ready = False
        mult *= config.UPGRADE_DASH_ATTACK_MULT
    player.swing_mult = mult


def on_dash_end(player):
    if has(player, 'dash_strike'):
        player.dash_strike_ready = True
