import os

from pico2d import *

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import sound, upgrades

# play_mode 위에 push되는 강화 선택 화면. ← →로 카드를 고르고 Enter로 결정하면 pop한다

title_font = None
text_font = None
small_font = None

# play_mode가 push_mode 직전에 채운다
player = None
choices = []
selected = 0


def set_choices(p, upgrade_list):
    global player, choices, selected
    player = p
    choices = upgrade_list
    selected = len(choices) // 2


def _load_font(size):
    if os.path.exists(config.FONT_PATH):
        return load_font(config.FONT_PATH, size)
    return None


def init():
    global title_font, text_font, small_font
    title_font = _load_font(config.FONT_SIZE_TEXT * 2)
    text_font = _load_font(config.FONT_SIZE_TEXT)
    small_font = _load_font(config.FONT_SIZE_SMALL)


def finish():
    global title_font, text_font, small_font, player, choices
    title_font = None
    text_font = None
    small_font = None
    player = None
    choices = []


def handle_events():
    global selected
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif e.key == SDLK_LEFT:
            selected = (selected - 1) % len(choices)
            sound.play('cursor')
        elif e.key == SDLK_RIGHT:
            selected = (selected + 1) % len(choices)
            sound.play('cursor')
        elif e.key == SDLK_RETURN:
            sound.play('select')
            upgrades.apply(player, choices[selected])
            game_framework.pop_mode()
            return


def update():
    pass


def draw_card(l, b, u, is_selected):
    r, t = l + config.CARD_W, b + config.CARD_H
    edge = config.CARD_BORDER
    border = config.COLOR_CARD_SELECTED if is_selected else config.COLOR_CARD_BORDER
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *border, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_CARD, filled=True)
    color = config.COLOR_UPGRADE[u.category]
    draw_rectangle(l, t - config.CARD_STRIPE_H, r, t, *color, filled=True)
    x = l + config.CARD_PAD
    y = t - config.CARD_STRIPE_H - config.CARD_PAD - config.CARD_LINE_H / 2
    if small_font:
        small_font.draw(x, y, config.UPGRADE_CATEGORY_NAME[u.category], color)
    y -= config.CARD_LINE_H * 1.5
    if text_font:
        text_font.draw(x, y, u.name, config.COLOR_TEXT)
    y -= config.CARD_LINE_H * 2
    if small_font:
        for line in u.desc.split('\n'):
            small_font.draw(x, y, line, config.COLOR_TEXT_DIM)
            y -= config.CARD_LINE_H


def draw():
    play_mode.draw_scene()
    effect.draw_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, config.DIM_ALPHA)
    total_w = len(choices) * config.CARD_W + (len(choices) - 1) * config.CARD_GAP
    l = (config.SCREEN_W - total_w) / 2
    b = (config.SCREEN_H - config.CARD_H) / 2
    for i, u in enumerate(choices):
        draw_card(l, b, u, i == selected)
        l += config.CARD_W + config.CARD_GAP
    cx = config.SCREEN_W // 2
    if title_font:
        title_font.draw(cx - config.FONT_SIZE_TEXT * 2.5, b + config.CARD_H + config.CARD_GAP * 1.5,
                        '강화 선택', config.COLOR_TEXT)
    if text_font:
        text_font.draw(cx - config.FONT_SIZE_TEXT * 4.5, b - config.CARD_GAP * 1.5,
                       '← → : 선택    Enter : 결정', config.COLOR_TEXT_DIM)
    update_canvas()


def pause():
    pass


def resume():
    pass
