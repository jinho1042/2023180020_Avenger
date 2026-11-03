# 전역 히트스톱 타이머. 남은 시간이 있는 동안 play_mode가 월드 update를 건너뛴다
# 슬로모션도 여기서 관리한다: 남은 시간이 있는 동안 월드에 frame_time × SLOWMO_SCALE을 전달

import config

timer = 0.0
slowmo_timer = 0.0


def start(duration):
    # 이미 더 긴 히트스톱이 걸려 있으면 유지한다
    global timer
    timer = max(timer, duration)


def start_slowmo(duration):
    global slowmo_timer
    slowmo_timer = max(slowmo_timer, duration)


def is_active():
    return timer > 0


def time_scale():
    return config.SLOWMO_SCALE if slowmo_timer > 0 else 1.0


def update(dt):
    # dt는 실제 시간. 히트스톱 중에는 슬로모션 시간이 흐르지 않는다
    global timer, slowmo_timer
    if timer > 0:
        timer = max(0, timer - dt)
    else:
        slowmo_timer = max(0, slowmo_timer - dt)


def reset():
    global timer, slowmo_timer
    timer = 0.0
    slowmo_timer = 0.0
