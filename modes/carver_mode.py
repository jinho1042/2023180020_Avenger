import json
import os
import sys

from pico2d import *

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import economy, runes, sound, world
from ui import font

# 룬지기 오람 (8.3, 7.4). 새김터에서 ↑로 말을 걸면 talk()가 대화를 열고, 대화가 끝나면 강화 목록(이 모드)을 push한다
# 처음: 대화 oram_first → 숨의 룬 지급(「받아친 숨」 1번 홈 장착, met_oram, 저장) → rune_get_mode → 대화 oram_gift → 강화 목록
# 이후: 대화 oram → 강화 목록
# 강화 목록: ←→ 룬 선택, X 강화 (보관 광석·희귀 광석, RUNE_UPGRADE_COST), Z·Esc 닫기. 강화하면 저장 + 짧은 rune_get_mode

RUNES_PATH = os.path.join(os.path.dirname(__file__), '..', config.DIALOG_DIR, 'runes.json')
UPGRADE_KEYS = (SDLK_x, SDLK_RETURN, SDLK_SPACE)
CLOSE_KEYS = (SDLK_ESCAPE, SDLK_z)

listed = []        # 목록의 룬 id (runes.upgradable)
selected = 0
notice = ''
texts = {}


# ---------- 대화 흐름 ----------

def open_dialog(dialog_id, after):
    from modes import dialog_mode
    dialog_mode.start(dialog_id, after)
    game_framework.push_mode(dialog_mode)


def talk():
    # play_mode.check_npcs가 부른다. 숨의 룬이 없으면 첫 만남
    state = world.state
    state.flags.add('met_oram')   # 새김터 발견 → 지도 아이콘 영구 표시 (8.3, 13.6)
    if runes.rune_lv(state, 'breath') < 1:
        open_dialog('oram_first', give_breath_rune)
    else:
        open_dialog('oram', open_list)


def give_breath_rune():
    # 숨의 룬 Lv1 + 「받아친 숨」 (7.4). 받는 즉시 저장 (8.5)
    from modes import rune_get_mode
    runes.grant(world.state, 'breath')
    play_mode.save_game()
    rune_get_mode.start('breath', 1, carver=True, after=lambda: open_dialog('oram_gift', open_list))
    game_framework.push_mode(rune_get_mode)


def open_list():
    game_framework.push_mode(sys.modules[__name__])


# ---------- 강화 목록 ----------

def init():
    global listed, selected, notice, texts
    with open(RUNES_PATH, encoding='utf-8') as f:
        texts = json.load(f)
    listed = runes.upgradable(world.state)
    selected, notice = 0, ''
    sound.play('select')


def finish():
    global listed
    listed = []


def rune_name(rune):
    info = texts.get(rune, {})
    return font.text(info.get('name', rune), info.get('name_en', rune))


def next_lines(rune, lv):
    # 다음 레벨 설명 (runes.json levels[lv], 숨의 룬은 {cap})
    info = texts.get(rune, {})
    levels = font.text(info.get('levels', []), info.get('levels_en', info.get('levels', [])))
    if lv >= len(levels):
        return []
    cap = config.BREATH_CAPACITY[lv + 1] if rune == 'breath' else 0
    return [line.format(cap=cap) for line in levels[lv]]


def upgrade():
    global notice
    if not listed:
        return
    from modes import rune_get_mode
    state = world.state
    rune = listed[selected]
    cost = runes.upgrade_cost(state, rune)
    if cost is None:
        notice = font.text('더 깊이 새길 수 없다.', 'It cannot be carved any deeper.')
        sound.play('cursor')
        return
    if not economy.pay(*cost):
        notice = font.text('보관 광석이 모자랍니다', 'Not enough stored ore')
        sound.play('cursor')
        return
    state.player.runes[rune] += 1
    notice = ''
    play_mode.save_game()   # 강화하면 자동 저장 (8.3)
    rune_get_mode.start(rune, state.player.runes[rune], is_short=True)
    game_framework.push_mode(rune_get_mode)


def handle_events():
    global selected, notice
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif e.key in CLOSE_KEYS:
            game_framework.pop_mode()
            return
        elif e.key in (SDLK_LEFT, SDLK_RIGHT) and listed:
            selected = (selected + (1 if e.key == SDLK_RIGHT else -1)) % len(listed)
            notice = ''
            sound.play('cursor')
        elif e.key in UPGRADE_KEYS:
            upgrade()
            return


def update():
    pass


# ---------- 그리기 ----------

def draw_box():
    box = config.DIALOG_BOX
    l = (config.SCREEN_W - box['w']) / 2
    b, r, t = box['bottom'], l + box['w'], box['bottom'] + box['h']
    edge = box['border']
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *config.COLOR_DIALOG_BORDER, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_DIALOG_BOX, filled=True)
    return l, b, r, t


def draw_card(rune, l, t, text_font, small_font):
    c = config.CARVER_CARD
    state = world.state
    r, b = l + c['w'], t - c['h']
    pad, edge = config.CARD_PAD, config.CARD_BORDER
    border = config.COLOR_CARD_SELECTED if rune == listed[selected] else config.COLOR_CARD_BORDER
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *border, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_CARD, filled=True)
    lv = runes.rune_lv(state, rune)
    y = t - pad - config.FONT_SIZE_TEXT / 2
    text_font.draw(l + pad, y, rune_name(rune), config.COLOR_RUNE_GLYPH)
    y -= config.CARD_LINE_H
    small_font.draw(l + pad, y, f'Lv{lv} / {config.RUNE_MAX_LEVEL[rune]}', config.COLOR_TEXT)
    cost = runes.upgrade_cost(state, rune)
    if cost is None:
        small_font.draw(l + pad, b + pad, font.text('최대 레벨', 'Max level'), config.COLOR_TEXT_DIM)
        return
    y -= config.CARD_LINE_H
    small_font.draw(l + pad, y, f'→ Lv{lv + 1}', config.COLOR_TEXT_DIM)
    for line in next_lines(rune, lv):
        y -= config.CARD_LINE_H
        small_font.draw(l + pad, y, line, config.COLOR_TEXT_DIM)
    ore, rare = cost
    price = font.text(f'광석 {ore}', f'Ore {ore}') + (font.text(f' · 희귀 {rare}', f' · Rare {rare}') if rare else '')
    color = config.COLOR_ORE if economy.can_pay(ore, rare) else config.COLOR_TEXT_DIM
    text_font.draw(l + pad, b + pad, price, color)


def draw_cards(text_font, small_font):
    # visible장씩 가로로. 고른 카드가 보이도록 시작 위치를 옮긴다 (상점과 같은 방식)
    c = config.CARVER_CARD
    count = min(c['visible'], len(listed))
    if count == 0:
        return
    first = min(max(0, selected - count + 1), len(listed) - count)
    total_w = count * c['w'] + (count - 1) * c['gap']
    left = (config.SCREEN_W - total_w) / 2
    for i in range(count):
        draw_card(listed[first + i], left + i * (c['w'] + c['gap']), c['top'], text_font, small_font)
    mid = c['top'] - c['h'] / 2
    if first > 0:
        text_font.draw(left - c['gap'] * 1.5, mid, '◀', config.COLOR_TEXT_DIM)
    if first + count < len(listed):
        text_font.draw(left + total_w + c['gap'] / 2, mid, '▶', config.COLOR_TEXT_DIM)


def draw():
    play_mode.draw_scene()
    effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, config.DIM_ALPHA)
    l, b, r, t = draw_box()
    text_font, small_font = font.get(config.FONT_SIZE_TEXT), font.get(config.FONT_SIZE_SMALL)
    if text_font:
        pad, line_h = config.DIALOG_BOX['pad'], config.DIALOG_BOX['line_h']
        y = t - pad - config.FONT_SIZE_TEXT / 2
        text_font.draw(l + pad, y, font.text('오람 — 룬 새기기', 'Oram — Carve Runes'), config.COLOR_DIALOG_NAME)
        ore = font.text(f'보관 광석 {economy.banked()}   희귀 광석 {economy.rare()}',
                        f'Stored ore {economy.banked()}   Rare ore {economy.rare()}')
        text_font.draw(l + pad, y - line_h, ore, config.COLOR_ORE)
        if notice:
            small_font.draw(l + pad, y - line_h * 2, notice, config.COLOR_TEXT)
        help_text = font.text('←→ 선택   X 새기기   Z 닫기', '←→ Select   X Carve   Z Close')
        small_font.draw(l + pad, b + pad, help_text, config.COLOR_TEXT_DIM)
        draw_cards(text_font, small_font)
    update_canvas()


def pause():
    pass


def resume():
    global listed
    listed = runes.upgradable(world.state)
