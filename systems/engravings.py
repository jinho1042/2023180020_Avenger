# 각인 정의·효과 (8.4, v2 upgrades.py 대체)
# 장착 상태는 world.state.player.engravings_set (홈 대상 → 각인 id 목록, 인덱스 0 = 1번 홈, 13.6)만 읽는다
# 홈 대상 = 'pickaxe' 또는 룬 id. 각인의 대상(items.json target) = 'pickaxe' / 룬 id / 'any'(공용)
# 스탯 각인은 누적 대입하지 않는다: 아래 함수가 매번 '기본값 × 장착 각인 배율'로 계산한다 (8.4)
# 숨 각인(깊은 폐·고른 숨·아끼는 숨·먼저 간 이의 숨)은 systems/breath.py가 is_set으로 계산한다 (18장 39번)

import json
import math
import os

import config
import game_world
from objects import effect
from objects.projectile import Projectile
from systems import world
from ui import font

ITEMS_PATH = os.path.join(os.path.dirname(__file__), '..', config.ITEMS_PATH)
with open(ITEMS_PATH, encoding='utf-8') as _f:
    ITEMS = json.load(_f)
IDS = [k for k, v in ITEMS.items() if v['kind'] == 'engraving']   # 8.4 표 순서
RUNES_PATH = os.path.join(os.path.dirname(__file__), '..', config.DIALOG_DIR, 'runes.json')
with open(RUNES_PATH, encoding='utf-8') as _f:
    RUNE_TEXTS = json.load(_f)


def player_state():
    return world.state.player


# ---------- 이름 · 설명 (items.json, 한글 폰트가 없으면 영어) ----------

def item_name(item_id):
    item = ITEMS.get(item_id, {})
    return font.text(item.get('name', item_id), item.get('name_en', item_id))


def item_desc(item_id):
    # 각인이면 첫 줄에 '각인 · 대상'을 붙인다 (상점·각인 화면·인벤토리 공통)
    item = ITEMS.get(item_id, {})
    lines = font.text(item.get('desc', []), item.get('desc_en', []))
    if item.get('kind') == 'engraving':
        lines = [font.text('각인 · ', 'Engraving · ') + target_name(item['target'])] + lines
    return lines


def target_name(target):
    if target == 'pickaxe':
        return font.text('곡괭이', 'Pickaxe')
    if target == 'any':
        return font.text('공용', 'Any')
    info = RUNE_TEXTS.get(target, {})
    return font.text(info.get('name', target), info.get('name_en', target))


# ---------- 장착 조회 ----------

def is_set(eid):
    # 어느 홈에든 장착되어 있는가 (보유만 한 것은 아님)
    return any(eid in slots for slots in player_state().engravings_set.values())


def target_of(eid):
    return ITEMS[eid]['target']


def slot_targets():
    # 홈이 있는 대상: 곡괭이 + 가진 룬 (RUNE_ORDER 순서). 룬이 없으면 그 룬 홈도 없다
    p = player_state()
    return ['pickaxe'] + [r for r in config.RUNE_ORDER if p.runes.get(r, 0) >= 1]


def slot_count(target):
    p = player_state()
    if target == 'pickaxe':
        return config.PICKAXE_ENGRAVE_SLOTS[p.pickaxe_level - 1]
    return config.ENGRAVE_SLOTS[target][p.runes.get(target, 0)]


def slots(target):
    return player_state().engravings_set.setdefault(target, [])


def where(eid):
    # 장착된 대상 (없으면 None)
    for target, ids in player_state().engravings_set.items():
        if eid in ids:
            return target
    return None


def fits(eid, target):
    # 대상 제한 (8.4): 곡괭이 전용 / 특정 룬 전용 / 공용
    return target_of(eid) in (target, 'any')


def is_locked(target, index):
    # PARRY_BREATH_ENGRAVING_LOCKED면 숨의 룬 1번 홈의 「받아친 숨」은 빼거나 바꿀 수 없다 (8.4)
    ids = slots(target)
    return (config.PARRY_BREATH_ENGRAVING_LOCKED and target == 'breath' and index == 0
            and index < len(ids) and ids[index] == 'parry_breath')


def equip(eid, target, index):
    # index번 홈에 새긴다. 다른 홈에 있던 같은 각인은 옮긴다. 빈 홈이면 뒤에 붙인다 (목록은 빈칸 없이 홈 순서)
    # 반환: 바뀌었으면 True
    if eid not in player_state().engravings_owned or not fits(eid, target):
        return False
    if index >= slot_count(target) or is_locked(target, index):
        return False
    ids = slots(target)
    if index < len(ids) and ids[index] == eid:
        return False
    old = where(eid)
    if old is not None:
        old_index = slots(old).index(eid)
        if is_locked(old, old_index):
            return False
        slots(old).remove(eid)
        if old == target and old_index < index:
            index -= 1
    if index < len(ids):
        ids[index] = eid
    else:
        ids.append(eid)
    return True


def unequip(target, index):
    ids = slots(target)
    if index >= len(ids) or is_locked(target, index):
        return False
    ids.pop(index)
    return True


def trim():
    # 홈 수보다 많이 끼워진 각인은 뺀다 (F7로 룬 레벨을 낮춘 경우). 대상이 없어진 홈도 비운다
    p = player_state()
    targets = slot_targets()
    for target, ids in p.engravings_set.items():
        if target not in targets:
            ids.clear()
        else:
            del ids[slot_count(target):]


def give_all():
    # F3 디버그: 각인 전부 보유 (장착은 각인 화면에서). 「받아친 숨」 장착은 runes.unlock_all이 한다
    player_state().engravings_owned.update(IDS)


# ---------- 스탯 (기본값 × 장착 각인) ----------

def attack_cooldown():
    return config.ATTACK_COOLDOWN_QUICK if is_set('quick_hands') else config.ATTACK_COOLDOWN


def attack_reach_mult():
    # 「긴 자루」: 곡괭이가 닿는 길이 (옆 공격은 가로, 위·아래 공격은 세로)
    return config.ATTACK_RANGE_LONG if is_set('long_handle') else 1


def damage_mult(player):
    mult = 1
    if is_set('miners_grit'):
        mult *= config.ENGRAVING['miners_grit']
    if is_set('last_stand') and player.hp == 1:
        mult *= config.ENGRAVING['last_stand']
    return mult


def third_strike_on():
    return is_set('third_strike')


def dash_dist():
    dist = config.DASH_DIST
    if is_set('long_dash'):
        dist *= config.ENGRAVING['long_dash']
    return dist


def dash_cooldown():
    cooldown = config.DASH_COOLDOWN
    if is_set('wind_step'):
        cooldown *= config.ENGRAVING['wind_step']
    return cooldown


def parry_window():
    window = config.PARRY_WINDOW
    if is_set('sharp_counter'):
        window += config.ENGRAVING['sharp_counter']
    return window


def invincible_on_hit():
    time = config.INVINCIBLE_ON_HIT
    if is_set('stone_skin'):
        time += config.ENGRAVING['stone_skin']
    return time


def reflect_mult():
    return config.ENGRAVING['mirror_crystal'] if is_set('mirror_crystal') else 1


# ---------- 패링 숨 (8.4, 이 함수 한 곳에서만) ----------

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


# ---------- 훅 (플레이어가 부른다) ----------

def on_parry_success(player, source):
    # 「반격 파동」: 바라보는 방향으로 플레이어 소유 파동 (v2 검기). 숨 각인은 여기를 쓰지 않는다 (8.4)
    if not is_set('counter_wave'):
        return
    from objects import projectile
    wave = config.ENGRAVING['counter_wave']
    w, h = wave['size']
    spec = dict(size=h, length=w, color=config.COLOR_COUNTER_WAVE)
    p = projectile.fire(player.x, player.y + config.PLAYER_H / 2, player.face_dir, 0,
                        wave['speed'], wave['damage'], False, player.platforms, spec, owner=player)
    p.reflected = True   # 처음부터 플레이어 소유 (적에게만 맞는다)


def on_attack_start(player):
    # 이번 한 번 휘두름의 추가 배율. 「질풍 일격」: 대시가 끝나고 window초 안의 첫 공격
    mult = 1
    if is_set('dash_strike') and player.dash_strike_timer > 0:
        mult *= config.ENGRAVING['dash_strike']['mult']
    player.dash_strike_timer = 0.0
    return mult


def on_attack_hit(player, target):
    # 적중마다 부르는 자리 (지금 이 훅을 쓰는 각인은 없다. 세 번째 일격은 player.count_strike)
    pass


def on_dash_end(player):
    if is_set('dash_strike'):
        player.dash_strike_timer = config.ENGRAVING['dash_strike']['window']


def on_hurt(player):
    # 「가시 갑각」: 적에게 맞으면 radius 안의 적에게 피해 (연습 석상 제외)
    if not is_set('thorn_shell'):
        return
    spec = config.ENGRAVING['thorn_shell']
    cx, cy = player.x, player.y + config.PLAYER_H / 2
    effect.thorn_burst(cx, cy)
    for e in list(game_world.world[config.DEPTH_ENEMY]):
        if getattr(e, 'kind', None) not in ('enemy', 'boss', 'elite') or not e.is_alive():
            continue
        ex, ey = (e.get_bb()[0] + e.get_bb()[2]) / 2, (e.get_bb()[1] + e.get_bb()[3]) / 2
        if math.hypot(ex - cx, ey - cy) <= spec['radius']:
            e.take_damage(spec['damage'])
            if e.is_alive():
                effect.enemy_hurt(ex, ey, 1 if ex >= cx else -1)


def on_mend(player):
    # 숨 고르기 완료 자리 (고른 숨·아끼는 숨은 breath.heal_time·heal_cost가 계산한다)
    pass


def on_breath_tick(dt):
    # 숨 갱신 자리 (깊은 폐·먼저 간 이의 숨은 breath.capacity·suffocate_interval이 계산한다)
    pass
