import random

import pico2d.pico2d as canvas  # open_canvas 이후 renderer가 여기 생긴다
from sdl2 import SDL_Rect, SDL_RenderSetViewport

import config

# 화면 흔들림. 월드를 그리는 동안 SDL viewport를 옮겨서 모든 그리기에 오프셋을 준다
# (SDL viewport는 음수 위치를 잘라내므로 오프셋은 0 ~ 2 * 세기 범위로 잡는다)

amplitude = 0.0
duration = 0.0
timer = 0.0


def shake(amp, time):
    # 지금 흔들림보다 센 것만 덮어쓴다
    global amplitude, duration, timer
    if amp >= current_amplitude():
        amplitude, duration, timer = amp, time, time


def current_amplitude():
    if timer <= 0:
        return 0.0
    return amplitude * timer / duration


def update(dt):
    global timer
    timer = max(0, timer - dt)


def begin():
    amp = current_amplitude()
    if amp <= 0:
        return
    ox = int(random.uniform(0, amp * 2))
    oy = int(random.uniform(0, amp * 2))
    SDL_RenderSetViewport(canvas.renderer, SDL_Rect(ox, oy, config.SCREEN_W, config.SCREEN_H))


def end():
    SDL_RenderSetViewport(canvas.renderer, None)


def reset():
    global amplitude, duration, timer
    amplitude, duration, timer = 0.0, 0.0, 0.0
