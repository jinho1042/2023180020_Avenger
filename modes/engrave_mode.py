from pico2d import *

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import engravings, sound
from ui import font

# 각인 새기기 (8.4). 안전지대에 앉아 X로 push (13.1). 월드·숨 정지
# 왼쪽: 곡괭이·가진 룬과 그 홈. ↑↓ 대상, ←→ 홈, X 고르기, Z·Esc 닫기 (바꾼 것이 있으면 저장)
# 오른쪽: X를 누르면 그 홈에 새길 수 있는 보유 각인 목록 (맨 위 '비우기'). ↑↓ 선택, X 새기기, Z·Esc 돌아가기
# 장착 상태는 world.state.player.engravings_set에만 쓰고, 효과는 engravings.py가 매번 계산한다

SELECT_KEYS = (SDLK_x, SDLK_RETURN, SDLK_SPACE)
BACK_KEYS = (SDLK_ESCAPE, SDLK_z)
EMPTY = None       # 목록의 '비우기' 항목

focus = 'slots'    # 'slots' | 'list'
row = 0            # 왼쪽 대상 줄
col = 0            # 그 대상의 홈 번호 (0 = 1번 홈)
options = []       # 오른쪽 목록 (EMPTY + 각인 id)
pick = 0           # 오른쪽 목록에서 고른 줄
list_top = 0       # 오른쪽 목록 첫 줄 (스크롤)
notice = ''
changed = False


def targets():
    return engravings.slot_targets()


def target():
    return targets()[row]


def slot_eid(t, index):
    ids = engravings.slots(t)
    return ids[index] if index < len(ids) else None


def init():
    global focus, row, col, pick, list_top, notice, changed, options
    before = {k: list(v) for k, v in world_engravings().items()}
    engravings.trim()
    changed = before != {k: list(v) for k, v in world_engravings().items()}
    focus, row, col, pick, list_top, notice, options = 'slots', 0, 0, 0, 0, '', []
    sound.play('select')


def world_engravings():
    return engravings.player_state().engravings_set


def finish():
    # 바꾼 것이 있으면 저장 (안전지대에 앉아 있으므로 rest_seat 그대로)
    if changed:
        play_mode.save_game()


# ---------- 조작 ----------

def move_row(step):
    global row, col, notice
    row = (row + step) % len(targets())
    col = min(col, engravings.slot_count(target()) - 1)
    notice = ''
    sound.play('cursor')


def move_col(step):
    global col, notice
    col = (col + step) % engravings.slot_count(target())
    notice = ''
    sound.play('cursor')


def open_list():
    # 이 홈에 새길 수 있는 보유 각인 (8.4 표 순서). 지금 끼워진 각인이 있으면 그 줄에서 시작
    global focus, options, pick, list_top, notice
    t = target()
    if engravings.is_locked(t, col):
        notice = font.text('「받아친 숨」은 이 홈에서 뺄 수 없다', 'Parry Breath cannot be removed from this slot')
        sound.play('cursor')
        return
    owned = engravings.player_state().engravings_owned
    options = [EMPTY] + [eid for eid in engravings.IDS if eid in owned and engravings.fits(eid, t)]
    current = slot_eid(t, col)
    pick = options.index(current) if current in options else 0
    list_top = 0
    scroll_to_pick()
    focus, notice = 'list', ''
    sound.play('cursor')


def scroll_to_pick():
    global list_top
    rows = config.ENGRAVE_UI['list_rows']
    list_top = min(max(list_top, pick - rows + 1), pick)


def apply_pick():
    # 고른 각인을 지금 홈에 새긴다 (다른 홈에 있던 같은 각인은 옮겨 온다). '비우기'면 홈을 비운다
    global focus, changed, notice
    t, eid = target(), options[pick]
    if eid is EMPTY:
        done = engravings.unequip(t, col)
    else:
        if engravings.where(eid) == 'breath' and engravings.is_locked('breath', engravings.slots('breath').index(eid)):
            notice = font.text('「받아친 숨」은 옮길 수 없다', 'Parry Breath cannot be moved')
            sound.play('cursor')
            return
        done = engravings.equip(eid, t, col)
    if done:
        changed = True
        sound.play('select')
    focus = 'slots'
    # 빈칸 없이 앞으로 당겨지므로 지금 홈이 비었으면 마지막으로 찬 홈 바로 뒤로
    clamp_col()


def clamp_col():
    global col
    col = min(col, len(engravings.slots(target())), engravings.slot_count(target()) - 1)


def handle_events():
    global focus, pick, notice
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif focus == 'slots':
            if e.key in BACK_KEYS:
                game_framework.pop_mode()
                return
            if e.key in (SDLK_UP, SDLK_DOWN):
                move_row(-1 if e.key == SDLK_UP else 1)
            elif e.key in (SDLK_LEFT, SDLK_RIGHT):
                move_col(-1 if e.key == SDLK_LEFT else 1)
            elif e.key in SELECT_KEYS:
                open_list()
        else:
            if e.key in BACK_KEYS:
                focus, notice = 'slots', ''
                sound.play('cursor')
            elif e.key in (SDLK_UP, SDLK_DOWN):
                pick = (pick + (-1 if e.key == SDLK_UP else 1)) % len(options)
                scroll_to_pick()
                sound.play('cursor')
            elif e.key in SELECT_KEYS:
                apply_pick()


def update():
    pass


# ---------- 그리기 ----------

def frame(l, b, r, t, color, fill):
    edge = config.ENGRAVE_UI['border']
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *color, filled=True)
    draw_rectangle(l, b, r, t, *fill, filled=True)


def target_label(t):
    p = engravings.player_state()
    lv = p.pickaxe_level if t == 'pickaxe' else p.runes.get(t, 0)
    return f'{engravings.target_name(t)} Lv{lv}'


def draw_targets(text_font, small_font):
    ui = config.ENGRAVE_UI
    for i, t in enumerate(targets()):
        y = ui['top'] - i * ui['row_h']
        color = config.COLOR_CARD_SELECTED if i == row else config.COLOR_TEXT
        text_font.draw(ui['left_x'], y - ui['slot_h'] / 2, target_label(t), color)
        for j in range(engravings.slot_count(t)):
            l = ui['left_x'] + ui['name_w'] + j * (ui['slot_w'] + ui['slot_gap'])
            b = y - ui['slot_h']
            selected = i == row and j == col
            if selected:
                border = config.COLOR_CARD_SELECTED
            elif engravings.is_locked(t, j):
                border = config.COLOR_ENGRAVE_LOCKED
            else:
                border = config.COLOR_CARD_BORDER
            frame(l, b, l + ui['slot_w'], y, border, config.COLOR_ENGRAVE_SLOT)
            eid = slot_eid(t, j)
            label = engravings.item_name(eid) if eid else font.text('빈 홈', 'Empty')
            small_font.draw(l + ui['slot_pad'], b + ui['slot_h'] / 2, label,
                            config.COLOR_TEXT if eid else config.COLOR_TEXT_DIM)


def list_ids():
    # 오른쪽에 보여 줄 줄: 고르는 중이면 그 홈 후보, 아니면 보유 각인 전부
    if focus == 'list':
        return options
    owned = engravings.player_state().engravings_owned
    return [eid for eid in engravings.IDS if eid in owned]


def draw_list(text_font, small_font):
    ui = config.ENGRAVE_UI
    ids = list_ids()
    top = ui['top'] + ui['list_row_h'] / 2
    bottom = top - ui['list_rows'] * ui['list_row_h']
    frame(ui['right_x'], bottom, ui['right_x'] + ui['right_w'], top + ui['list_row_h'],
          config.COLOR_CARD_BORDER, config.COLOR_ENGRAVE_PANEL)
    title = font.text('새길 각인', 'Choose') if focus == 'list' else font.text('보유 각인', 'Owned')
    text_font.draw(ui['right_x'] + ui['slot_pad'], top + ui['list_row_h'] / 2, title, config.COLOR_DIALOG_NAME)
    if not ids:
        small_font.draw(ui['right_x'] + ui['slot_pad'], top - ui['list_row_h'] / 2,
                        font.text('가진 각인이 없다', 'No engravings'), config.COLOR_TEXT_DIM)
        return
    first = list_top if focus == 'list' else 0
    for k, eid in enumerate(ids[first:first + ui['list_rows']]):
        y = top - (k + 0.5) * ui['list_row_h']
        selected = focus == 'list' and first + k == pick
        x = ui['right_x'] + ui['slot_pad']
        if selected:
            draw_rectangle(ui['right_x'], y - ui['list_row_h'] / 2, ui['right_x'] + ui['right_w'],
                           y + ui['list_row_h'] / 2, *config.COLOR_ENGRAVE_SLOT, filled=True)
        if eid is EMPTY:
            small_font.draw(x, y, font.text('— 비우기', '— Clear'),
                            config.COLOR_CARD_SELECTED if selected else config.COLOR_TEXT_DIM)
            continue
        small_font.draw(x, y, engravings.item_name(eid), config.COLOR_CARD_SELECTED if selected else config.COLOR_TEXT)
        where = engravings.where(eid)
        if where:
            small_font.draw(ui['right_x'] + ui['right_w'] / 2, y, engravings.target_name(where),
                            config.COLOR_ENGRAVE_SET)
        else:
            small_font.draw(ui['right_x'] + ui['right_w'] / 2, y, engravings.target_name(engravings.target_of(eid)),
                            config.COLOR_TEXT_DIM)


def focused_eid():
    if focus == 'list':
        return options[pick] if options else None
    return slot_eid(target(), col)


def draw_desc(text_font, small_font):
    ui = config.ENGRAVE_UI
    eid = focused_eid()
    y = ui['desc_y']
    if notice:
        small_font.draw(ui['left_x'], y + ui['list_row_h'], notice, config.COLOR_CARD_SELECTED)
    if eid:
        text_font.draw(ui['left_x'], y, engravings.item_name(eid), config.COLOR_DIALOG_NAME)
        for k, line in enumerate(engravings.item_desc(eid)):
            small_font.draw(ui['left_x'] + ui['name_w'], y - k * ui['list_row_h'], line, config.COLOR_TEXT)
    if focus == 'slots':
        help_text = font.text('↑↓ 대상   ←→ 홈   X 고르기   Z 닫기', '↑↓ Target   ←→ Slot   X Choose   Z Close')
    else:
        help_text = font.text('↑↓ 선택   X 새기기   Z 돌아가기', '↑↓ Select   X Engrave   Z Back')
    small_font.draw(ui['left_x'], ui['help_y'], help_text, config.COLOR_TEXT_DIM)


def draw():
    play_mode.draw_scene()
    effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, config.ENGRAVE_DIM_ALPHA)
    text_font, small_font = font.get(config.FONT_SIZE_TEXT), font.get(config.FONT_SIZE_SMALL)
    if text_font:
        text_font.draw(config.ENGRAVE_UI['left_x'], config.ENGRAVE_UI['title_y'],
                       font.text('각인 새기기', 'Engravings'), config.COLOR_DIALOG_NAME)
        draw_targets(text_font, small_font)
        draw_list(text_font, small_font)
        draw_desc(text_font, small_font)
    update_canvas()


def pause():
    pass


def resume():
    pass
