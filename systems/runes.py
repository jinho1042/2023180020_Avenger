# 룬 보유·레벨 조회와 능력 잠금 (6.2, 8.2)
# 능력 확인은 player.can('dash'), player.rune_lv('burrow')로만 한다. 둘 다 이 모듈을 거쳐 world_state를 본다
# world_state.player.runes: 룬 id → 레벨 (없으면 0), world_state.flags: 플래그 집합 (반사 해금 = REFLECT_UNLOCK_FLAG)

import config


def rune_lv(world_state, rune):
    return world_state.player.runes.get(rune, 0)


def can(world_state, ability):
    # 반사는 룬이 아니라 플래그로 해금된다 (9.3)
    if ability == 'reflect':
        return config.REFLECT_UNLOCK_FLAG in world_state.flags
    rune, need = config.ABILITY_RUNE[ability]
    return rune_lv(world_state, rune) >= need


def give_parry_breath(world_state):
    # 「받아친 숨」을 보유 목록에 넣고 숨의 룬 1번 홈에 장착한다 (8.4). 이미 장착이면 그대로
    p = world_state.player
    p.engravings_owned.add('parry_breath')
    breath_slots = p.engravings_set.setdefault('breath', [])
    if 'parry_breath' not in breath_slots:
        breath_slots.insert(0, 'parry_breath')


def grant(world_state, rune):
    # 룬 획득 (8.5): Lv1. 숨의 룬은 첫 각인 「받아친 숨」이 1번 홈에 새겨진 채로 (7.4). 저장은 부른 쪽
    world_state.player.runes[rune] = max(1, rune_lv(world_state, rune))
    if rune == 'breath':
        give_parry_breath(world_state)


def upgrade_cost(world_state, rune):
    # 다음 레벨 비용 (광석, 희귀 광석). 룬이 없거나 최대 레벨이면 None (8.3)
    lv = rune_lv(world_state, rune)
    if lv < 1 or lv >= config.RUNE_MAX_LEVEL[rune]:
        return None
    return config.RUNE_UPGRADE_COST[rune][lv - 1]


def upgradable(world_state):
    # 룬지기 강화 목록에 나오는 룬 (보유한 것, RUNE_ORDER 순서). 최대 레벨도 목록에는 남긴다
    return [r for r in config.RUNE_ORDER if rune_lv(world_state, r) >= 1]


def unlock_all(world_state):
    # F3 디버그: 모든 룬 최대 레벨 + 반사 플래그 + 「받아친 숨」 장착(숨의 룬 1번 홈, T37). 이후 저장은 save_debug.json으로 (13.6)
    p = world_state.player
    p.runes = dict(config.RUNE_MAX_LEVEL)
    world_state.flags.add(config.REFLECT_UNLOCK_FLAG)
    give_parry_breath(world_state)
    world_state.debug_unlocked = True
