# 키 매핑 · 누름 상태 · 입력 버퍼 · 누름 시간 (6.1, 6.3)
# 코드에서는 키 대신 동작 이름으로 쓴다: input.pressed('jump'), input.consume('attack')
# 버퍼와 누름 시간은 update(dt)에서만 흐른다. 플레이어 update에서 월드 dt로 부르므로
# 히트스톱 중에는 버퍼가 줄지 않고 그대로 저장된다 (16장)

import pico2d

import config

# pico2d 키 코드 → 동작 이름
KEY_TO_ACTION = {getattr(pico2d, name): action for action, name in config.KEYS.items()}

# 동작별 입력 버퍼 시간. 여기 없는 동작은 버퍼를 쓰지 않는다
# up은 앉기·말 걸기 누름 (위 공격·위 보기는 누름 상태 pressed('up')를 쓴다)
BUFFER_TIME = dict(jump=config.JUMP_BUFFER, attack=config.INPUT_BUFFER,
                   parry=config.INPUT_BUFFER, dash=config.INPUT_BUFFER, up=config.INPUT_BUFFER)

held = set()       # 지금 누르고 있는 동작
hold_time = {}     # 동작 → 누른 뒤 지난 시간 (누르고 있는 동안만)
buffers = {}       # 동작 → 남은 버퍼 시간 (> 0이면 아직 처리 안 된 누름)


def handle_event(e):
    # 매핑된 키면 동작 이름을 돌려준다. 키 반복(누르고 있을 때 반복 KEYDOWN)은 무시
    if e.type not in (pico2d.SDL_KEYDOWN, pico2d.SDL_KEYUP):
        return None
    action = KEY_TO_ACTION.get(e.key)
    if action is None:
        return None
    if e.type == pico2d.SDL_KEYDOWN:
        if action not in held:
            held.add(action)
            hold_time[action] = 0.0
            if action in BUFFER_TIME:
                buffers[action] = BUFFER_TIME[action]
    else:
        held.discard(action)
        hold_time.pop(action, None)
    return action


def update(dt):
    for action in hold_time:
        hold_time[action] += dt
    for action in list(buffers):
        buffers[action] -= dt
        if buffers[action] < 0:   # 정확히 버퍼 시간 전에 누른 입력도 살린다
            del buffers[action]


def pressed(action):
    # 지금 누르고 있는가
    return action in held


def held_for(action):
    # 누른 뒤 지난 시간 (안 누르고 있으면 0)
    return hold_time.get(action, 0.0)


def buffered(action):
    # 버퍼 안에 처리 안 된 누름이 있는가
    return action in buffers


def consume(action):
    # 버퍼된 누름을 쓴다. 있었으면 True
    return buffers.pop(action, None) is not None


def axis_x():
    # 좌우 동시 입력이면 0
    return pressed('right') - pressed('left')


def clear_buffers():
    # 입력 잠금 중(환경 피해 복귀 등) 들어온 누름을 버린다. 누름 상태는 유지
    buffers.clear()


def clear():
    # 다른 모드가 위에 있는 동안 뗀 키를 놓치므로 누름 상태·버퍼를 초기화한다
    held.clear()
    hold_time.clear()
    buffers.clear()
