import os

from pico2d import *

import config
import game_framework
from modes import play_mode
from systems import sound

title_font = None
text_font = None


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
            game_framework.change_mode(play_mode)


def update():
    pass


def draw():
    clear_canvas()
    cx, cy = config.SCREEN_W // 2, config.SCREEN_H // 2
    if title_font:
        title_font.draw(cx - 180, cy + 80, 'AVENGER', config.COLOR_TEXT)
    if text_font:
        text_font.draw(cx - 110, cy - 60, 'Space : 시작', config.COLOR_TEXT_DIM)
        text_font.draw(cx - 110, cy - 100, 'Esc : 종료', config.COLOR_TEXT_DIM)
    update_canvas()


def pause():
    pass


def resume():
    pass
