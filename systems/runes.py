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


def unlock_all(world_state):
    # F3 디버그: 모든 룬 최대 레벨 + 반사 플래그 + 「받아친 숨」 장착(숨의 룬 1번 홈, T37). 이후 저장은 save_debug.json으로 (13.6)
    p = world_state.player
    p.runes = dict(config.RUNE_MAX_LEVEL)
    world_state.flags.add(config.REFLECT_UNLOCK_FLAG)
    p.engravings_owned.add('parry_breath')
    breath_slots = p.engravings_set.setdefault('breath', [])
    if 'parry_breath' not in breath_slots:
        breath_slots.insert(0, 'parry_breath')
    world_state.debug_unlocked = True
