import os

from pico2d import *

import config
import game_framework
from modes import play_mode
from systems import save, sound

# 타이틀 (13.7): 이어하기 / 새 게임(덮어쓰기 확인) / 조작법 / 종료. DEBUG면 '디버그 이어하기' 추가
# ↑↓로 고르고 Z·Enter·Space로 선택. 확인 창은 ←→, 조작법·확인 창은 Esc·X로 닫는다
# 메뉴·확인 창·조작법 그리기는 pause_mode도 같이 쓴다

CONFIRM_KEYS = (SDLK_z, SDLK_RETURN, SDLK_SPACE)
BACK_KEYS = (SDLK_ESCAPE, SDLK_x)

title_font = None
text_font = None
items = []         # (항목 이름, 동작 키)
selected = 0
view = 'menu'      # 'menu' | 'confirm' | 'controls'
confirm_yes = False


def _load_font(size):
    if os.path.exists(config.FONT_PATH):
        return load_font(config.FONT_PATH, size)
    return None


def init():
    global title_font, text_font, items, selected, view
    title_font = _load_font(config.FONT_SIZE_TITLE)
    text_font = _load_font(config.FONT_SIZE_TEXT)
    items = [('이어하기', 'continue'), ('새 게임', 'new'), ('조작법', 'controls'), ('종료', 'quit')]
    if config.DEBUG:
        items.insert(1, ('디버그 이어하기', 'debug_continue'))
    selected = 0 if save.exists() else [a for _, a in items].index('new')
    view = 'menu'


def finish():
    global title_font, text_font
    title_font = None
    text_font = None


def enabled(action):
    # 이어하기는 save.json만 읽는다. 디버그 이어하기는 save_debug.json (13.6)
    if action == 'continue':
        return save.exists(config.SAVE_PATH)
    if action == 'debug_continue':
        return save.exists(config.SAVE_DEBUG_PATH)
    return True


def start_game(path):
    sound.play('select')
    play_mode.start(path)
    game_framework.change_mode(play_mode)


def choose(action):
    global view, confirm_yes
    if not enabled(action):
        sound.play('cursor')
    elif action == 'continue':
        start_game(config.SAVE_PATH)
    elif action == 'debug_continue':
        start_game(config.SAVE_DEBUG_PATH)
    elif action == 'new':
        if save.exists():
            view, confirm_yes = 'confirm', False
            sound.play('cursor')
        else:
            start_game(None)
    elif action == 'controls':
        view = 'controls'
        sound.play('select')
    else:
        game_framework.quit()


def handle_events():
    global selected, view, confirm_yes
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif view == 'controls':
            if e.key in BACK_KEYS + CONFIRM_KEYS:
                view = 'menu'
        elif view == 'confirm':
            if e.key in (SDLK_LEFT, SDLK_RIGHT):
                confirm_yes = not confirm_yes
                sound.play('cursor')
            elif e.key in BACK_KEYS:
                view = 'menu'
            elif e.key in CONFIRM_KEYS:
                if confirm_yes:
                    start_game(None)   # 새 게임. 이전 세이브는 다음 저장 때 덮어쓴다
                    return
                view = 'menu'
        elif e.key == SDLK_ESCAPE:
            game_framework.quit()
        elif e.key in (SDLK_UP, SDLK_DOWN):
            selected = (selected + (1 if e.key == SDLK_DOWN else -1)) % len(items)
            sound.play('cursor')
        elif e.key in CONFIRM_KEYS:
            choose(items[selected][1])
            return


def update():
    pass


def draw_menu(font, labels, index, is_enabled=None):
    # 화면 가운데 세로 메뉴. 고른 항목은 강조색, 고를 수 없는 항목은 흐리게
    if not font:
        return
    x = config.SCREEN_W / 2 - config.FONT_SIZE_TEXT * 3
    for i, label in enumerate(labels):
        y = config.MENU_TOP_Y - i * config.MENU_ROW_H
        if is_enabled and not is_enabled[i]:
            color = config.COLOR_TEXT_DIM
        else:
            color = config.COLOR_MENU_SELECTED if i == index else config.COLOR_TEXT
        font.draw(x - config.FONT_SIZE_TEXT if i == index else x, y, ('▶ ' if i == index else '') + label, color)


def draw_confirm(font, lines, yes):
    # 확인 창: 안내 문구 몇 줄 + 예 / 아니오
    if not font:
        return
    x = config.SCREEN_W / 2 - config.FONT_SIZE_TEXT * 8
    y = config.MENU_TOP_Y
    for line in lines:
        font.draw(x, y, line, config.COLOR_TEXT)
        y -= config.MENU_ROW_H
    y -= config.MENU_ROW_H / 2
    font.draw(x, y, '예', config.COLOR_MENU_SELECTED if yes else config.COLOR_TEXT_DIM)
    font.draw(x + config.FONT_SIZE_TEXT * 4, y, '아니오', config.COLOR_TEXT_DIM if yes else config.COLOR_MENU_SELECTED)


def draw_controls(font):
    if not font:
        return
    x = config.SCREEN_W / 2 - config.FONT_SIZE_TEXT * 8
    y = config.SCREEN_H - config.MENU_ROW_H * 2
    for line in config.CONTROLS_TEXT:
        font.draw(x, y, line, config.COLOR_TEXT)
        y -= config.MENU_ROW_H
    font.draw(x, y - config.MENU_ROW_H / 2, 'Esc : 돌아가기', config.COLOR_TEXT_DIM)


def draw():
    clear_canvas()
    if view == 'controls':
        draw_controls(text_font)
    elif view == 'confirm':
        draw_confirm(text_font, ['저장된 게임을 덮어씁니다.', '새 게임을 시작할까요?'], confirm_yes)
    else:
        if title_font:
            title_font.draw(config.SCREEN_W / 2 - 180, config.SCREEN_H - 160, 'AVENGER', config.COLOR_TEXT)
        draw_menu(text_font, [label for label, _ in items], selected, [enabled(a) for _, a in items])
    update_canvas()


def pause():
    pass


def resume():
    pass
