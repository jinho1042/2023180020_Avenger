import os

from pico2d import *

import config
import game_framework
from systems import sound

title_font = None
text_font = None

# play_mode가 change_mode 직전에 채운다
cleared = False
rooms_reached = 0
rooms_total = 0
parry_count = 0
play_time = 0.0


def set_result(is_cleared, reached, total, parries, time):
    global cleared, rooms_reached, rooms_total, parry_count, play_time
    cleared = is_cleared
    rooms_reached = reached
    rooms_total = total
    parry_count = parries
    play_time = time


def _load_font(size):
    if os.path.exists(config.FONT_PATH):
        return load_font(config.FONT_PATH, size)
    return None


def init():
    global title_font, text_font
    title_font = _load_font(config.FONT_SIZE_TITLE)
    text_font = _load_font(config.FONT_SIZE_TEXT)


def finish():
    global title_font, text_font
    title_font = None
    text_font = None


def handle_events():
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key == SDLK_SPACE:
            sound.play('select')
            from modes import title_mode
            game_framework.change_mode(title_mode)


def update():
    pass


def draw():
    clear_canvas()
    cx, cy = config.SCREEN_W // 2, config.SCREEN_H // 2
    if title_font:
        if cleared:
            title_font.draw(cx - 110, cy + 120, 'CLEAR', config.COLOR_RESULT_CLEAR)
        else:
            title_font.draw(cx - 200, cy + 120, 'GAME OVER', config.COLOR_RESULT_DEAD)
    if text_font:
        minutes, seconds = divmod(int(play_time), 60)
        text_font.draw(cx - 110, cy + 20, f'도달한 방 : {rooms_reached} / {rooms_total}', config.COLOR_TEXT)
        text_font.draw(cx - 110, cy - 20, f'패링 횟수 : {parry_count}', config.COLOR_TEXT)
        text_font.draw(cx - 110, cy - 60, f'플레이 시간 : {minutes:02d}:{seconds:02d}', config.COLOR_TEXT)
        text_font.draw(cx - 110, cy - 140, 'Space : 타이틀로', config.COLOR_TEXT_DIM)
    update_canvas()


def pause():
    pass


def resume():
    pass
