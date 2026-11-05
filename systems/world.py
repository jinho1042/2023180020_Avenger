import os
from types import SimpleNamespace

import config
from systems.room import Room

ROOM_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'rooms')

# 영구 월드 상태 (5.6, 13.6 world). 저장은 T36. runes·engravings_*는 13.6에서 player 쪽이지만 지금은 여기에 둔다 (18장 8번)
state = None
room_paths = {}    # 방 id(파일 이름) → JSON 경로. data/rooms 아래 모든 폴더
enter = None       # 방을 실제로 채우는 함수 (play_mode.enter_room). Room과 도착 정보를 받는다
# 방 전환: None → 'out'(어두워짐, 월드 정지) → 방 교체 → 'in'(밝아짐, 월드 진행) → None
phase = None
timer = 0.0
lock = 0.0         # 도착 후 TRANSITION_LOCK 동안 출구를 무시한다 (출구 왕복 방지)
pending = None     # 'out'이 끝나면 들어갈 (방 id, 도착 정보)


def new_state():
    return SimpleNamespace(
        runes={}, engravings_owned=set(), engravings_set={}, flags=set(), debug_unlocked=False,
        visited=set(), map_stones=set(), broken=set(), opened=set(), switches=set(), collected=set(),
        miners_rescued=set(), miner_rewards_taken=set(), safe_zones_found=set(),
        bosses_met=set(), bosses_defeated=set(), elites_defeated=set(), cores=set(), hint_fail_count=0)


def init(enter_fn):
    global state, room_paths, enter, phase, timer, lock, pending
    state = new_state()
    enter = enter_fn
    phase, timer, lock, pending = None, 0.0, 0.0, None
    room_paths = {}
    for folder, _, files in os.walk(ROOM_DIR):
        for name in files:
            if name.endswith('.json'):
                room_paths[name[:-len('.json')]] = os.path.join(folder, name)


def finish():
    global state, enter, pending
    state = None
    enter = None
    pending = None


def room_ids():
    return sorted(room_paths)


def load(room_id, arrival=None):
    # 페이드 없이 바로 방을 바꾼다 (새 게임 첫 방). 평소에는 go_through·warp
    room = Room(room_paths[room_id])
    state.visited.add(room.id)
    enter(room, arrival or {})


def go_through(exit_zone, player):
    # 출구에 닿음 → 도착 방의 to_exit 출구 안쪽으로. 출구를 따라 어디쯤이었는지와 속도를 이어받는다
    if exit_zone.to not in room_paths:
        return  # 아직 만들지 않은 방 (12.5 미작성 출구)
    l, b, r, t = exit_zone.get_bb()
    along = player.y - b if exit_zone.side in ('left', 'right') else player.x - l
    begin(exit_zone.to, dict(exit_id=exit_zone.to_exit, along=along,
                             vx=player.vx, vy=player.vy, fall_time=player.fall_time))


def warp(room_id, spot=None):
    # 페이드를 거쳐 방을 옮긴다. spot이 없으면 방의 기본 자리 (기절 복귀·F4)
    begin(room_id, dict(spot=spot))


def begin(room_id, arrival):
    global phase, timer, pending
    if phase == 'out':
        return
    # 밝아지는 도중에 다시 나가면 지금 어두운 정도에서 이어서 어두워진다
    timer = config.TRANSITION_FADE - timer if phase == 'in' else config.TRANSITION_FADE
    phase, pending = 'out', (room_id, arrival)


def update(dt):
    global phase, timer, lock, pending
    lock = max(0, lock - dt)
    if phase is None:
        return
    timer -= dt
    if timer > 0:
        return
    if phase == 'out':
        room_id, arrival = pending
        pending = None
        load(room_id, arrival)
        phase, timer, lock = 'in', config.TRANSITION_FADE, config.TRANSITION_LOCK
    else:
        phase = None


def frozen():
    # 어두워지는 동안은 월드를 멈춘다
    return phase == 'out'


def can_exit():
    return phase != 'out' and lock <= 0


def fade_alpha():
    if phase == 'out':
        return 255 * (1 - timer / config.TRANSITION_FADE)
    if phase == 'in':
        return 255 * timer / config.TRANSITION_FADE
    return 0


def exit_spot(exit_zone, along):
    # 출구 안쪽 EXIT_SPAWN_INSET 자리. 옆 출구는 높이, 위·아래 출구는 가로 위치를 출구 범위 안에서 이어받는다
    l, b, r, t = exit_zone.get_bb()
    inset = config.EXIT_SPAWN_INSET
    if exit_zone.side in ('left', 'right'):
        x = r + inset if exit_zone.side == 'left' else l - inset
        return x, min(max(b + along, b), max(b, t - config.PLAYER_H))
    half_w = config.PLAYER_W / 2
    x = min(max(l + along, l + half_w), r - half_w)
    return x, (t + inset if exit_zone.side == 'down' else b - inset - config.PLAYER_H)


def place_player(player, room, arrival):
    # 도착 자리에 플레이어를 놓는다. play_mode.enter_room이 부른다
    if 'exit_id' not in arrival:
        spot = arrival.get('spot') or room.player_start or (room.safe_points[0] if room.safe_points else None)
        if spot is None and room.exits:
            spot = exit_spot(room.exits[0], 0)
        player.enter_room(room.platforms, spot or (room.width / 2, 0), room.safe_points)
        return
    exit_zone = room.exit(arrival['exit_id'])
    player.enter_room(room.platforms, exit_spot(exit_zone, arrival['along']), room.safe_points)
    if exit_zone.side in ('left', 'right'):
        player.vx, player.vy = arrival['vx'], arrival['vy']
    elif exit_zone.side == 'up':
        # 아래 출구로 떨어져 들어옴: 낙하 속도·낙하 시간 유지 (강착지 판정이 이어진다)
        player.vy, player.fall_time = arrival['vy'], arrival['fall_time']
    else:
        # 위 출구로 올라옴: 착지 발판까지 밀어올린다
        player.vy = max(arrival['vy'], config.EXIT_UP_BOOST)
