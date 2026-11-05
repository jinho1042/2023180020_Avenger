import random

from pico2d import draw_rectangle

import config
from systems import input

# 카메라 (5.3, 14.2): 추적·룩어헤드·위/아래 보기·경계 clamp + 흔들림
# 모든 위치는 월드 좌표(방 좌하단 = (0, 0)). 그릴 때만 to_screen()으로 화면 좌표로 바꾼다
# x, y = 화면 좌하단이 보고 있는 월드 좌표

x, y = 0.0, 0.0
bounds = (0, 0, config.SCREEN_W, config.SCREEN_H)  # (l, b, r, t) 카메라가 보여줄 수 있는 범위 (방 또는 보스 아레나)
look_timer = 0.0    # 멈춰서 ↑/↓를 누르고 있는 시간
look_dir = 0        # 1 = 위, -1 = 아래

# 흔들림. 세기는 시간에 따라 줄어들고, 오프셋은 그리기 시작할 때(begin) 한 번 정해 최종 오프셋으로 더한다
amplitude = 0.0
duration = 0.0
timer = 0.0
shake_x, shake_y = 0, 0
# 이번 그리기에서 쓰는 월드 → 화면 오프셋 (정수로 맞춰 객체끼리 1px 어긋나지 않게)
offset_x, offset_y = 0, 0


def shake(amp, time):
    # 지금 흔들림보다 센 것만 덮어쓴다
    global amplitude, duration, timer
    if amp >= current_amplitude():
        amplitude, duration, timer = amp, time, time


def current_amplitude():
    if timer <= 0:
        return 0.0
    return amplitude * timer / duration


def set_bounds(l, b, r, t):
    # 방 경계 (보스 아레나는 T45에서 아레나 경계로 부른다)
    global bounds
    bounds = (l, b, r, t)


def set_room(w, h):
    set_bounds(0, 0, w, h)


def clamp_axis(v, lo, hi, view):
    # 보여줄 범위가 화면보다 작거나 같으면 고정 (1×1 방)
    if hi - lo <= view:
        return lo
    return max(lo, min(v, hi - view))


def update_look(player, dt):
    # 멈춰 서서 ↑/↓를 CAMERA_LOOK_HOLD초 누르면 그쪽을 본다. 움직이거나 떼면 바로 풀린다
    global look_timer, look_dir
    d = input.pressed('up') - input.pressed('down')
    standing = player.on_ground and input.axis_x() == 0 and not player.dead
    if d == 0 or not standing or d != look_dir:
        look_timer = 0.0
        look_dir = d if standing else 0
        return
    look_timer += dt


def target(player):
    l, b, r, t = bounds
    tx = player.x + player.face_dir * config.CAMERA_LOOKAHEAD_X - config.SCREEN_W / 2
    # 세로 보기는 경계로 맞춘 위치에서 더한다 (바닥에 서서 위를 봐도 위가 보이게)
    ty = clamp_axis(player.y + config.PLAYER_H / 2 - config.SCREEN_H / 2, b, t, config.SCREEN_H)
    if look_dir and look_timer >= config.CAMERA_LOOK_HOLD:
        ty += look_dir * config.CAMERA_LOOK_VERTICAL
    elif not player.on_ground and player.vy < 0:
        ty -= config.CAMERA_FALL_LOOKAHEAD
    return clamp_axis(tx, l, r, config.SCREEN_W), clamp_axis(ty, b, t, config.SCREEN_H)


def update(dt, player=None):
    # 히트스톱 중에도 부른다 (흔들림과 추적은 실제 시간으로 흐른다)
    global timer, x, y
    timer = max(0, timer - dt)
    if player is None:
        return
    update_look(player, dt)
    tx, ty = target(player)
    k = min(1.0, config.CAMERA_LERP * dt)
    x += (tx - x) * k
    y += (ty - y) * k


def snap(player):
    # 방 전환 직후 즉시 목표 위치로
    global x, y, look_timer, look_dir
    look_timer, look_dir = 0.0, 0
    x, y = target(player)


def begin():
    # 월드를 그리기 직전: 이번 프레임의 흔들림을 정해 최종 오프셋을 만든다
    global shake_x, shake_y, offset_x, offset_y
    amp = current_amplitude()
    shake_x = random.uniform(-amp, amp) if amp > 0 else 0
    shake_y = random.uniform(-amp, amp) if amp > 0 else 0
    offset_x = round(x - shake_x)
    offset_y = round(y - shake_y)


def end():
    pass


def to_screen(wx, wy):
    return wx - offset_x, wy - offset_y


def rect(l, b, r, t):
    return l - offset_x, b - offset_y, r - offset_x, t - offset_y


def draw_rect(l, b, r, t, *color, filled=False):
    # 월드 좌표 사각형 그리기 (pico2d.draw_rectangle의 월드 버전)
    draw_rectangle(*rect(l, b, r, t), *color, filled=filled)


def visible(bb):
    # 화면 밖(여유 CAMERA_CULL_MARGIN) 객체는 그리지 않는다
    l, b, r, t = bb
    m = config.CAMERA_CULL_MARGIN
    return (r >= offset_x - m and l <= offset_x + config.SCREEN_W + m
            and t >= offset_y - m and b <= offset_y + config.SCREEN_H + m)


def reset():
    global amplitude, duration, timer, shake_x, shake_y
    amplitude, duration, timer = 0.0, 0.0, 0.0
    shake_x, shake_y = 0, 0
