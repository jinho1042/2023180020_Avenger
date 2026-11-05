# 세이브/로드 (13.6, 1슬롯). world.state를 13.6 JSON 모양으로 쓰고 읽는다
# 저장 경로는 매번 state.debug_unlocked로 정한다: True면 SAVE_DEBUG_PATH (F3·F7을 쓴 뒤의 저장)
# 소지 광석·현재 숨·기절 복귀 지점(breath.last_safe_zone)은 저장하지 않는다. 게임 데이터(적 체력 등)도 넣지 않는다

import json
import os

import config
from systems import world

# 13.6 player / world 필드 중 집합(set)으로 들고 있는 것. JSON에는 정렬한 목록으로 쓴다
PLAYER_SETS = ('engravings_owned',)
WORLD_SETS = ('visited', 'map_stones', 'broken', 'opened', 'switches', 'collected', 'miners_rescued',
              'miner_rewards_taken', 'safe_zones_found', 'bosses_met', 'bosses_defeated', 'elites_defeated',
              'cores', 'flags')
WORLD_VALUES = ('mined', 'hint_fail_count', 'debug_unlocked')   # mined는 13.6에 없지만 저장한다 (18장 25번)


def path_for(state):
    return config.SAVE_DEBUG_PATH if state.debug_unlocked else config.SAVE_PATH


def exists(path=config.SAVE_PATH):
    return os.path.exists(path)


def to_dict(state, play_time):
    p = state.player
    player = {k: v for k, v in vars(p).items() if k not in PLAYER_SETS}
    player.update({k: sorted(getattr(p, k)) for k in PLAYER_SETS})
    world_data = {k: sorted(getattr(state, k)) for k in WORLD_SETS}
    world_data.update({k: getattr(state, k) for k in WORLD_VALUES})
    return dict(version=config.SAVE_VERSION, play_time=play_time, rest_seat=state.rest_seat,
                player=player, world=world_data, stats=dict(state.stats))


def write(state, play_time):
    # 임시 파일에 쓴 뒤 교체한다 (쓰는 도중 꺼져도 이전 세이브가 남게). 반환: 쓴 경로
    path = path_for(state)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(to_dict(state, play_time), f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


def load(path):
    # 반환: (상태, play_time). 없는 필드는 새 게임 기본값으로 채운다 (버전 마이그레이션: 숫자 0, debug_unlocked False)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    state = world.new_state()
    p = state.player
    for k, v in data.get('player', {}).items():
        if hasattr(p, k):
            setattr(p, k, set(v) if k in PLAYER_SETS else v)
    for k, v in data.get('world', {}).items():
        if k in WORLD_SETS:
            setattr(state, k, set(v))
        elif k in WORLD_VALUES:
            setattr(state, k, v)
    state.stats.update(data.get('stats', {}))
    state.rest_seat = data.get('rest_seat')
    if path == config.SAVE_DEBUG_PATH:
        state.debug_unlocked = True   # 디버그 세이브는 파일 안 값과 상관없이 계속 디버그 저장
    return state, data.get('play_time', 0.0)
