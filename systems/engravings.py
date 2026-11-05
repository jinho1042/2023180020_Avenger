# 각인 정의·효과 (8.4, upgrades.py 대체)
# T37 껍데기: 장착 여부 is_set(id)와 패링 숨 계산 parry_breath_gain(source)만 동작한다
# 나머지 훅은 빈 함수이고, T44에서 v2 upgrades.py의 훅·효과를 옮겨 채운다
# 장착 상태는 world.state.player.engravings_set (홈 대상 → 각인 id 목록, 13.6)만 읽는다

import config
from objects.projectile import Projectile
from systems import world


def is_set(eid):
    # 어느 홈에든 장착되어 있는가 (보유만 한 것은 아님)
    return any(eid in slots for slots in world.state.player.engravings_set.values())


def parry_breath_gain(source):
    # 패링 성공 시 얻는 숨 (8.4). 패링 숨은 여기서만 계산한다. source = 패링한 적·보스 또는 투사체
    # 1. 「받아친 숨」 미장착 → 0
    if not is_set('parry_breath'):
        return 0
    # 2. 투사체면 쏜 쪽으로 바꾼다. 함정·연습 석상 → 0
    owner = source.owner if isinstance(source, Projectile) else source
    kind = getattr(owner, 'kind', None)
    if kind is None or kind in ('hazard', 'statue'):
        return 0
    # 3. 일반 적은 한 마리당 PARRY_BREATH_PER_ENEMY_MAX회까지 (보스·정예는 세지 않는다)
    if kind == 'enemy':
        if owner.parry_breath_count >= config.PARRY_BREATH_PER_ENEMY_MAX:
            return 0
        owner.parry_breath_count += 1
    # 4. 「되받은 숨」도 장착이면 배율
    gain = config.BREATH_PER_PARRY
    if is_set('breath_echo'):
        gain *= config.ENGRAVING['breath_echo']
    return gain


# ---------- 훅 (T44에서 채운다) ----------

def on_parry_success(player, source):
    pass


def on_attack_hit(player, target):
    pass


def on_dash_end(player):
    pass


def on_hurt(player):
    pass


def on_mend(player):
    pass


def on_breath_tick(dt):
    pass
