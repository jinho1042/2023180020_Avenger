import os

import pico2d
from pico2d import *

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import engravings, sound, world

# play_mode 위에 push되는 디버그 메뉴 (0장 15번). config.DEBUG일 때만 열린다
# F4 방 이동: ↑↓로 방을 고르고 Z·Enter로 워프
# F7 개별 지급: 룬은 ←→(Z = +1)로 레벨, 플래그·봉인 핵(T57)·각인은 Z·Enter로 켜고 끈다. 하나라도 바꾸면 debug_unlocked (13.6)
# Esc·F4·F7로 닫는다

DEBUG_KEY = {getattr(pico2d, name): action for action, name in config.DEBUG_KEYS.items()}
CONFIRM_KEYS = (SDLK_z, SDLK_RETURN)

title_font = None
text_font = None
kind = 'warp'      # 'warp' | 'give'. play_mode가 push_mode 직전에 open_menu로 정한다
entries = []       # warp: 방 id 목록 / give: (종류, id) 목록
selected = 0
top = 0            # 스크롤: 화면 첫 줄의 인덱스


def open_menu(menu_kind):
    global kind
    kind = menu_kind


def give_entries():
    return ([('rune', r) for r in config.RUNE_MAX_LEVEL] + [('flag', f) for f in config.DEBUG_GIVE_FLAGS]
            + [('core', c) for c in config.BOSS_CORE.values()] + [('engraving', e) for e in engravings.IDS])


def owned_set(entry_kind):
    # 켜고 끄는 항목이 들어 있는 집합 (플래그·봉인 핵·각인)
    state = world.state
    return dict(flag=state.flags, core=state.cores).get(entry_kind, state.player.engravings_owned)


def init():
    global title_font, text_font, entries, selected, top
    if os.path.exists(config.FONT_PATH):
        title_font = load_font(config.FONT_PATH, config.FONT_SIZE_TEXT)
        text_font = load_font(config.FONT_PATH, config.FONT_SIZE_SMALL)
    entries = world.room_ids() if kind == 'warp' else give_entries()
    selected = entries.index(play_mode.room.id) if kind == 'warp' and play_mode.room.id in entries else 0
    top = 0
    scroll_to_selected()


def finish():
    global title_font, text_font, entries
    title_font = None
    text_font = None
    entries = []


def scroll_to_selected():
    global top
    top = min(max(top, selected - config.DEBUG_MENU_ROWS + 1), selected)


def change_rune(rune, step):
    runes = world.state.player.runes
    runes[rune] = (runes.get(rune, 0) + step) % (config.RUNE_MAX_LEVEL[rune] + 1)


def toggle_engraving(eid):
    # 지급 = 보유 목록에 추가. 「받아친 숨」은 실제 획득처럼 숨의 룬 1번 홈에 장착된 채로 준다 (8.4)
    state = world.state.player
    breath_slots = state.engravings_set.setdefault('breath', [])
    if eid in state.engravings_owned:
        state.engravings_owned.discard(eid)
        for slots in state.engravings_set.values():
            if eid in slots:
                slots.remove(eid)
    else:
        state.engravings_owned.add(eid)
        if eid == 'parry_breath':
            breath_slots.insert(0, eid)


def give(step):
    entry_kind, eid = entries[selected]
    if entry_kind == 'rune':
        change_rune(eid, step)
    elif entry_kind in ('flag', 'core'):
        owned_set(entry_kind).symmetric_difference_update({eid})
    else:
        toggle_engraving(eid)
    world.state.debug_unlocked = True   # 이후 저장은 save_debug.json으로 (13.6)
    print(f'[DEBUG] F7 지급: {label(entries[selected])}')
    sound.play('select')


def handle_events():
    global selected
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif e.key == SDLK_ESCAPE or DEBUG_KEY.get(e.key) in ('warp', 'give'):
            game_framework.pop_mode()
            return
        elif e.key in (SDLK_UP, SDLK_DOWN):
            selected = (selected + (1 if e.key == SDLK_DOWN else -1)) % len(entries)
            scroll_to_selected()
            sound.play('cursor')
        elif kind == 'give' and e.key in (SDLK_LEFT, SDLK_RIGHT) and entries[selected][0] == 'rune':
            give(1 if e.key == SDLK_RIGHT else -1)
        elif e.key in CONFIRM_KEYS:
            if kind == 'give':
                give(1)
                continue
            sound.play('select')
            world.warp(entries[selected])
            print(f'[DEBUG] F4 워프: {entries[selected]}')
            game_framework.pop_mode()
            return


def update():
    pass


def label(entry):
    if kind == 'warp':
        folder = os.path.basename(os.path.dirname(world.room_paths[entry]))
        return f'{entry}    ({folder})'
    entry_kind, eid = entry
    state = world.state
    if entry_kind == 'rune':
        return f'룬  {eid}  Lv{state.player.runes.get(eid, 0)} / {config.RUNE_MAX_LEVEL[eid]}'
    on = eid in owned_set(entry_kind)
    name = dict(flag='플래그', core='봉인 핵').get(entry_kind, '각인')
    return f"{name}  {eid}  {'O' if on else '-'}"


def is_on(entry):
    if kind == 'warp':
        return entry == play_mode.room.id
    entry_kind, eid = entry
    if entry_kind == 'rune':
        return world.state.player.runes.get(eid, 0) > 0
    return eid in owned_set(entry_kind)


def draw():
    play_mode.draw_scene()
    effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, config.DIM_ALPHA)
    pad, row_h = config.DEBUG_MENU_PAD, config.DEBUG_MENU_ROW_H
    w, h = config.DEBUG_MENU_W, (config.DEBUG_MENU_ROWS + 2) * row_h + pad * 2
    l, b = (config.SCREEN_W - w) / 2, (config.SCREEN_H - h) / 2
    draw_rectangle(l, b, l + w, b + h, *config.COLOR_DEBUG_MENU, filled=True)
    y = b + h - pad - row_h / 2
    if title_font:
        title = 'F4 방 이동  (Z: 워프)' if kind == 'warp' else 'F7 개별 지급  (Z: 지급/해제, ←→: 룬 레벨)'
        title_font.draw(l + pad, y, title, config.COLOR_TEXT)
    y -= row_h * 1.5
    for i in range(top, min(top + config.DEBUG_MENU_ROWS, len(entries))):
        if i == selected:
            draw_rectangle(l + pad / 2, y - row_h / 2, l + w - pad / 2, y + row_h / 2,
                           *config.COLOR_DEBUG_MENU_SELECTED)
        if text_font:
            color = config.COLOR_DEBUG_MENU_ON if is_on(entries[i]) else config.COLOR_TEXT
            text_font.draw(l + pad, y, label(entries[i]), color)
        y -= row_h
    if text_font and len(entries) > config.DEBUG_MENU_ROWS:
        text_font.draw(l + pad, b + pad / 2, f'{selected + 1} / {len(entries)}', config.COLOR_TEXT_DIM)
    update_canvas()


def pause():
    pass


def resume():
    pass
