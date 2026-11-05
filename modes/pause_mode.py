import os

from pico2d import *

import config
import game_framework
from modes import play_mode, title_mode
from objects import effect
from systems import sound

# 일시정지 (13.7). play_mode 위에 push된다 (월드·숨 정지)
# 계속 / 조작법 / 저장하고 타이틀로 (확인 창: 소지 광석은 저장되지 않음). Esc = 계속
# 메뉴·확인 창·조작법 그리기는 title_mode 것을 쓴다

ITEMS = [('계속', 'resume'), ('조작법', 'controls'), ('저장하고 타이틀로', 'title')]
CONFIRM_LINES = ['소지한 광석은 저장되지 않습니다.', '다음에는 마지막으로 앉은 안전지대에서 시작합니다.',
                 '저장하고 타이틀로 갈까요?']

text_font = None
selected = 0
view = 'menu'      # 'menu' | 'confirm' | 'controls'
confirm_yes = False


def init():
    global text_font, selected, view
    if os.path.exists(config.FONT_PATH):
        text_font = load_font(config.FONT_PATH, config.FONT_SIZE_TEXT)
    selected = 0
    view = 'menu'


def finish():
    global text_font
    text_font = None


def to_title():
    # 저장한 뒤 play_mode를 끝내고 타이틀로. rest_seat는 그대로라 이어하기는 마지막으로 앉은 자리에서
    play_mode.save_game()
    sound.play('select')
    game_framework.pop_mode()
    game_framework.change_mode(title_mode)


def choose(action):
    global view, confirm_yes
    if action == 'resume':
        game_framework.pop_mode()
    elif action == 'controls':
        view = 'controls'
        sound.play('select')
    else:
        view, confirm_yes = 'confirm', False
        sound.play('cursor')


def handle_events():
    global selected, view, confirm_yes
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif view == 'controls':
            if e.key in title_mode.BACK_KEYS + title_mode.CONFIRM_KEYS:
                view = 'menu'
        elif view == 'confirm':
            if e.key in (SDLK_LEFT, SDLK_RIGHT):
                confirm_yes = not confirm_yes
                sound.play('cursor')
            elif e.key in title_mode.BACK_KEYS:
                view = 'menu'
            elif e.key in title_mode.CONFIRM_KEYS:
                if confirm_yes:
                    to_title()
                    return
                view = 'menu'
        elif e.key == SDLK_ESCAPE:
            game_framework.pop_mode()
            return
        elif e.key in (SDLK_UP, SDLK_DOWN):
            selected = (selected + (1 if e.key == SDLK_DOWN else -1)) % len(ITEMS)
            sound.play('cursor')
        elif e.key in title_mode.CONFIRM_KEYS:
            choose(ITEMS[selected][1])
            return


def update():
    pass


def draw():
    play_mode.draw_scene()
    effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, config.DIM_ALPHA)
    if view == 'controls':
        title_mode.draw_controls(text_font)
    elif view == 'confirm':
        title_mode.draw_confirm(text_font, CONFIRM_LINES, confirm_yes)
    else:
        title_mode.draw_menu(text_font, [label for label, _ in ITEMS], selected)
    update_canvas()


def pause():
    pass


def resume():
    pass
