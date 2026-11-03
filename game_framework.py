from pico2d import get_time

import config

running = False
stack = []
frame_time = 0.0


def change_mode(mode):
    if stack:
        stack[-1].finish()
        stack.pop()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack[-1].finish()
        stack.pop()
    if stack:
        stack[-1].resume()


def quit():
    global running
    running = False


def run(start_mode):
    global running, frame_time
    running = True
    stack.append(start_mode)
    start_mode.init()

    current_time = get_time()
    while running:
        stack[-1].handle_events()
        stack[-1].update()
        stack[-1].draw()
        now = get_time()
        frame_time = min(now - current_time, config.MAX_FRAME_TIME)
        current_time = now

    while stack:
        stack[-1].finish()
        stack.pop()
