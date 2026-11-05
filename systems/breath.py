# 숨 게이지 (7.2, 7.3, 13.5): 소모·회복·질식·게이트 기절(레벨 확인)·디버그 구간 측정
# 숨의 단위는 '초' (배율 1.0에서 1초에 1씩 준다)
# play_mode가 월드가 움직이는 프레임에만 update()를 부른다. 메뉴·일시정지·히트스톱·방 전환 페이드 중에는
# 부르지 않으므로 그동안 숨이 멈춘다 (7.2 소모가 멈추는 경우)

import json
import os

import config
from objects import effect
from systems import engravings, runes, world

value = 0.0
infinite = False          # F5 숨 무한
has_gauge = True          # 지금 방에 숨 게이지가 있는가 (공기 배율 None = 광산, 14.1 HUD 숨김)
mult = 0.0                # 지금 소모 배율 (HUD·디버그). 안전지대 안이면 0
air = None                # 지금 배율을 정한 공기 이름 (HUD 표시용)
in_safe = False           # 몸이 안전지대 영역 안인가
grace = 0.0               # 안전지대를 나선 뒤 남은 소모 유예
gate = None               # 몸 중심이 들어 있는 숨 게이트 (objects.breath_zone.BreathGate)
locked_rate = None        # 요구 레벨 미달 게이트에서 초당 줄어드는 양 (들어온 순간의 숨 ÷ LOCKED_TIME)
suffocating = False
suffocate_timer = 0.0
last_safe_zone = None     # 마지막으로 들어간 안전지대 전역 id (7.3 기절 복귀 지점). 저장 안 함, 로드 시 rest_seat
blackout = None           # None | 'fade'(어두워지는 중) | 'warp'(복귀 방 전환 중)
blackout_timer = 0.0
flash_timer = 0.0         # 패링 숨을 얻었을 때 게이지 반짝
# 디버그 구간 측정 (13.5): 마지막 숨 회복 지점(안전지대·숨구멍)을 떠난 뒤 경과 시간·쓴 숨
segment = None            # 진행 중인 구간 dict(start, time, used, gate). 안전지대 안이면 None
finished = None           # 마지막으로 끝난 구간 (F6가 기록하면 None)


def init(state):
    # 새 게임·이어하기: 숨 가득, 기절 복귀 지점은 rest_seat의 안전지대 (13.6)
    global value, infinite, in_safe, grace, gate, locked_rate, suffocating, suffocate_timer
    global last_safe_zone, blackout, blackout_timer, flash_timer, segment, finished
    value = capacity()
    infinite = False
    in_safe, grace, gate, locked_rate = False, 0.0, None, None
    suffocating, suffocate_timer = False, 0.0
    last_safe_zone = state.rest_seat
    blackout, blackout_timer, flash_timer = None, 0.0, 0.0
    segment, finished = None, None


def base_capacity():
    # 숨의 룬 레벨의 기본 용량 (7.6 비율 계산은 각인 보정 없이 이것으로)
    return config.BREATH_CAPACITY[runes.rune_lv(world.state, 'breath')]


def capacity():
    # 매번 기본값 × 장착 각인 배율로 계산한다 (8.4 누적 대입 금지)
    cap = base_capacity()
    if engravings.is_set('deep_lung'):
        cap *= config.ENGRAVING['deep_lung']
    return cap


def ratio():
    cap = capacity()
    return value / cap if cap > 0 else 0


def is_low():
    return has_gauge and ratio() < config.BREATH_LOW_RATIO


def heal_cost():
    cost = config.HEAL_BREATH_COST
    if engravings.is_set('thrifty_breath'):
        cost *= config.ENGRAVING['thrifty_breath']
    return cost


def heal_time():
    t = config.HEAL_TIME
    if engravings.is_set('steady_breath'):
        t *= config.ENGRAVING['steady_breath']
    return t


def suffocate_interval():
    interval = config.SUFFOCATE_INTERVAL
    if engravings.is_set('first_breath'):
        interval *= config.ENGRAVING['first_breath']
    return interval


def add(amount):
    # 숨구멍·패링 등으로 얻는 숨. 0 이하면 아무것도 안 한다
    global value, flash_timer, suffocating
    if amount <= 0:
        return
    value = min(capacity(), value + amount)
    flash_timer = config.BREATH_FLASH_TIME
    suffocating = False


def spend(amount):
    # 숨 고르기·룬 기술. 모자라면 쓰지 않고 False (7.2)
    global value
    if infinite:
        return True
    if value < amount:
        return False
    use(amount)
    return True


def use(amount):
    # 숨을 줄이고 구간 측정에 더한다
    global value
    value = max(0.0, value - amount)
    if segment is not None:
        segment['used'] += amount


# ---------- 배율 · 영역 ----------

def body_center(player):
    return player.x, player.y + config.PLAYER_H / 2


def contains(obj, x, y):
    l, b, r, t = obj.get_bb()
    return l <= x <= r and b <= y <= t


def base_air(room):
    # 7.2 순서 1: 방 air가 있으면 그것, 없으면 구역 기본. None이면 숨 게이지 없음
    if room.air:
        return room.air
    region = config.REGIONS.get(room.region)
    return region['air'] if region else None


def drain_multiplier(room, player):
    # 7.2 순서 2: 몸 중심이 들어 있는 영역 배율과 기본 배율 중 가장 큰 값 하나 (곱하지 않는다). 반환: (배율, 공기 이름)
    # 순서 3(안전지대)은 update가, 순서 4(버팀 Lv3 매달림)는 T65에서
    name = base_air(room)
    if name is None:
        return None, None
    m = config.BREATH_DRAIN_MULT[name]
    x, y = body_center(player)
    for zone in room.breath_zone_objects:
        zone_m = config.BREATH_DRAIN_MULT[zone.air]
        if zone_m > m and contains(zone, x, y):
            m, name = zone_m, zone.air
    return m, name


def gate_at(room, player):
    x, y = body_center(player)
    return next((g for g in room.breath_gate_objects if contains(g, x, y)), None)


# ---------- 갱신 ----------

def update(dt, player, room, safe_zone):
    # safe_zone = 몸이 들어 있는 안전지대 (없으면 None, play_mode.check_safe_zones가 찾는다)
    global value, has_gauge, mult, air, gate, locked_rate, flash_timer
    flash_timer = max(0, flash_timer - dt)
    if blackout:
        update_blackout(dt, player)
        return
    if player.dead:
        return
    cap = capacity()
    value = min(value, cap)
    m, air = drain_multiplier(room, player)
    has_gauge = m is not None
    if not has_gauge:
        # 광산(R0): 숨 게이지 없음. 숨은 가득인 채로 둔다
        value, mult, gate = cap, 0.0, None
        return
    if safe_zone:
        update_safe(dt, safe_zone, cap)
        return
    leave_safe()
    gate = gate_at(room, player)
    if segment is not None:
        segment['time'] += dt
        if gate and segment['gate'] is None:
            segment['gate'] = gate.gate_id
    mult = m
    if infinite:
        value = cap
        return
    drain(dt, m)
    if value > 0:
        stop_suffocating()
    elif gate:
        start_blackout(player)   # 게이트 방 안에서 숨 0 = 기절 (질식하지 않는다)
    else:
        suffocate(dt, player)


def drain(dt, m):
    global grace, locked_rate
    if gate and runes.rune_lv(world.state, 'breath') < gate.need_lv:
        # 요구 레벨 미달: 들어온 순간의 숨이 BREATH_GATE_LOCKED_TIME에 걸쳐 0이 된다 (7.3)
        if locked_rate is None:
            locked_rate = value / config.BREATH_GATE_LOCKED_TIME
        use(locked_rate * dt)
        return
    locked_rate = None
    if grace > 0:
        grace = max(0, grace - dt)
        return
    use(config.BREATH_DRAIN * m * dt)


def update_safe(dt, zone, cap):
    # 안전지대 안 (7.2 순서 3, 13.1): 소모 0, BREATH_REFILL_RATE로 회복, 기절 복귀 지점 갱신
    global value, in_safe, grace, mult, gate, locked_rate, last_safe_zone, segment, finished
    if not in_safe:
        in_safe = True
        effect.safe_zone_entered()
        if segment is not None:
            finished = dict(segment, to=zone.gid)
            segment = None
    last_safe_zone = zone.gid
    grace = config.BREATH_EXIT_GRACE
    mult, gate, locked_rate = 0.0, None, None
    stop_suffocating()
    value = min(cap, value + config.BREATH_REFILL_RATE * dt)


def leave_safe():
    global in_safe, segment
    if in_safe:
        in_safe = False
        segment = new_segment(last_safe_zone)
    elif segment is None:
        segment = new_segment(world.state.rest_seat)   # 안전지대 밖에서 시작함 (워프 등)


def new_segment(start):
    return dict(start=start, time=0.0, used=0.0, gate=None)


def touch_air_vent(vent):
    # 숨구멍에 닿음 (play_mode가 쿨다운이 끝난 숨구멍만 넘긴다). 회복 지점이므로 구간을 끊고 새로 잰다
    global segment, finished
    add(config.AIR_VENT_REFILL)
    stop_suffocating()
    if segment is not None:
        finished = dict(segment, to=vent.gid)
    segment = new_segment(vent.gid)


# ---------- 질식 · 기절 ----------

def stop_suffocating():
    global suffocating
    suffocating = False


def suffocate(dt, player):
    # 숨 0 (게이트 방 밖): suffocate_interval()마다 체력 1칸. 히트스톱·무적 없이 (7.3)
    global suffocating, suffocate_timer
    if not suffocating:
        suffocating = True
        suffocate_timer = 0.0
        world.state.stats['suffocations'] += 1
    suffocate_timer += dt
    interval = suffocate_interval()
    if suffocate_timer >= interval:
        suffocate_timer -= interval
        player.suffocate_hit()
        effect.suffocated()


def start_blackout(player):
    # 게이트 기절 (7.3): 입력 잠금 → 어두워짐 → 마지막 안전지대. 체력·광석 손실 없음
    global blackout, blackout_timer, segment
    blackout = 'fade'
    blackout_timer = config.BREATH_GATE_BLACKOUT_FADE
    segment = None
    player.start_blackout()
    world.state.stats['blackouts'] += 1
    if gate.gate_id == 'choke':
        world.state.hint_fail_count += 1   # 숨막이 갱 (7.5 보름 힌트)
    print(f'[숨] 게이트 {gate.gate_id} 기절 → {last_safe_zone}')


def update_blackout(dt, player):
    global blackout, blackout_timer
    if blackout == 'fade':
        blackout_timer -= dt
        if blackout_timer <= 0:
            blackout = 'warp'
            warp_to_safe_zone()
    elif world.phase is None:
        # 복귀 방에 도착해 밝아지기까지 끝남 (update는 방 전환 페이드 중에는 불리지 않는다)
        blackout = None
        player.end_blackout()


def warp_to_safe_zone():
    # 마지막으로 들어간 안전지대 → rest_seat → 새 게임 첫 방 순으로. 앉지 않은 상태로 영역 바닥에 선다
    for gid in (last_safe_zone, world.state.rest_seat):
        if gid and gid.split(':')[0] in world.room_paths:
            room_id, zone_id = gid.split(':')
            world.warp(room_id, zone=zone_id)
            return
    world.warp(config.START_ROOM)


def blackout_alpha():
    # 화면을 덮는 어둠 (0~255). 복귀 방으로 바뀌는 동안은 world.fade_alpha와 이어지도록 끝까지 검게
    if blackout == 'fade':
        return 255 * (1 - blackout_timer / config.BREATH_GATE_BLACKOUT_FADE)
    if blackout == 'warp' and world.phase == 'out':
        return 255
    return 0


# ---------- 디버그 (F5, F6) ----------

def toggle_infinite():
    global infinite
    infinite = not infinite
    return infinite


def current_segment():
    # HUD 구간 타이머에 보일 구간 (진행 중이면 그것, 안전지대 안이면 마지막으로 끝난 구간)
    return segment or finished


def record(room_id):
    # F6: 측정값을 BREATH_BUDGET_PATH에 한 줄 추가 (13.5, 7.6 기록 형식). 반환: 기록한 dict, 없으면 None
    # 끝난 구간이 있으면 그것을, 없으면 진행 중인 구간을 지금 방까지로 기록한다
    global finished
    seg = finished or (dict(segment, to=room_id) if segment else None)
    if seg is None or seg['time'] <= 0:
        return None
    lv = runes.rune_lv(world.state, 'breath')
    line = {'from': seg['start'], 'to': seg['to'], 'gate': seg['gate'], 'breath_lv': lv,
            'time': round(seg['time'], 1), 'used': round(seg['used'], 1),
            'ratio': round(seg['used'] / config.BREATH_CAPACITY[lv], 2)}
    path = os.path.join(os.path.dirname(__file__), '..', config.BREATH_BUDGET_PATH)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(line, ensure_ascii=False) + '\n')
    finished = None
    return line
