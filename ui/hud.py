import math
import os

from pico2d import *

import config

from objects import effect
from systems import breath, economy
from ui import font as fonts

font = None
message = ''          # 하단 중앙 알림 문구 ('저장했습니다' 등). message_timer > 0인 동안 보인다
message_timer = 0.0
hide_breath = False   # 도입부 추락·깨어남 동안 숨 게이지를 숨긴다 (2.2 '숨 게이지가 처음 나타남', script.py)


def init():
    global font, message, message_timer, hide_breath
    message, message_timer = '', 0.0
    hide_breath = False
    if os.path.exists(config.FONT_PATH):
        font = load_font(config.FONT_PATH, config.FONT_SIZE_TEXT)


def finish():
    global font
    font = None


def draw_hp_cells(player):
    # 좌상단 체력 칸 (6.7): 최대 체력만큼 틀, 남은 체력만큼 채움. 1칸 남으면 경고색
    size, edge = config.HP_CELL, config.HP_BAR_BORDER
    t = config.SCREEN_H - config.HUD_MARGIN
    b = t - size
    fill = config.COLOR_HP_LOW if player.hp == 1 else config.COLOR_HP_FILL
    for i in range(player.max_hp):
        l = config.HUD_MARGIN + i * (size + config.HP_CELL_GAP)
        draw_rectangle(l - edge, b - edge, l + size + edge, t + edge, *config.COLOR_HUD_FRAME, filled=True)
        color = fill if i < player.hp else config.COLOR_HP_BACK
        draw_rectangle(l, b, l + size, t, *color, filled=True)


def draw_breath_bar():
    # 체력 칸 아래 숨 게이지 (14.1): 하늘색 가로 막대, 길이는 용량에 비례. 광산(숨 게이지 없음)에서는 숨김
    if not breath.has_gauge or hide_breath:
        return
    edge = config.HP_BAR_BORDER
    l = config.HUD_MARGIN
    t = config.SCREEN_H - config.HUD_MARGIN - config.HP_CELL - config.BREATH_BAR_GAP
    b = t - config.BREATH_BAR_H
    r = l + breath.capacity() * config.BREATH_BAR_PX
    frame = config.COLOR_HUD_FRAME
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *frame, filled=True)
    if breath.gate:
        # 숨 게이트 방 안: 테두리에 빗금
        hatch = config.BREATH_GATE_HATCH
        for x in range(int(l - edge), int(r + edge), hatch * 2):
            draw_rectangle(x, b - edge, min(x + hatch, r + edge), t + edge, *config.COLOR_BREATH_GATE, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_BREATH_BACK, filled=True)
    fill_r = l + breath.value * config.BREATH_BAR_PX
    if fill_r <= l:
        return
    if breath.flash_timer > 0:
        color = config.COLOR_BREATH_FLASH          # 패링 숨을 얻음
    elif breath.in_safe:
        color = config.COLOR_BREATH_REFILL         # 안전지대 안에서 차오름
    elif breath.is_low() and int(get_time() / config.BREATH_LOW_BLINK) % 2:
        color = config.COLOR_BREATH_LOW            # 숨 부족 깜빡임
    else:
        color = config.COLOR_BREATH
    draw_rectangle(l, b, fill_r, t, *color, filled=True)
    if breath.mult > 1:
        draw_breath_flow(l, b, fill_r, t)


def draw_breath_flow(l, b, r, t):
    # 배율이 1보다 크면 게이지 안에 줄어드는 쪽(왼쪽)으로 흐르는 무늬 + 막대 오른쪽에 공기 종류 표시 (14.1)
    gap = config.BREATH_FLOW_GAP
    shift = get_time() * config.BREATH_FLOW_SPEED * breath.mult % gap
    stripe = gap / 3
    x = r - shift
    while x - stripe > l:
        draw_rectangle(x - stripe, b, x, t, *config.COLOR_BREATH_FLOW, filled=True)
        x -= gap
    mark = config.COLOR_BREATH_ZONE.get(breath.air, config.COLOR_BREATH_FLOW)
    right = config.HUD_MARGIN + breath.capacity() * config.BREATH_BAR_PX + config.HP_CELL_GAP * 2
    draw_rectangle(right, b, right + config.BREATH_BAR_H, t, *mark, filled=True)


def text_width(text):
    # 글자 폭을 알 수 없어 한글은 글자 크기, 나머지는 HUD_FONT_NARROW배로 어림한다
    size = config.FONT_SIZE_TEXT
    return sum(size if ord(c) >= 0x1100 else size * config.HUD_FONT_NARROW for c in text)


def ore_line_y():
    # 숨 게이지 아래 광석 줄의 글자 가운데 y. 숨 게이지가 숨겨진 광산에서도 자리는 같다
    return (config.SCREEN_H - config.HUD_MARGIN - config.HP_CELL - config.BREATH_BAR_GAP - config.BREATH_BAR_H
            - config.HP_BAR_BORDER - config.ORE_HUD_GAP - config.FONT_SIZE_TEXT / 2)


def draw_ore():
    # 숨 게이지 아래 '보관 840 (+소지 120)' (14.1). 보관하는 순간 소지 숫자가 보관 숫자 쪽으로 미끄러지며
    # 보관 숫자가 올라간다 (13.2)
    if not font:
        return
    x, y = config.HUD_MARGIN, ore_line_y()
    progress = economy.bank_progress()
    banked = economy.banked()
    if progress is not None:
        banked -= round(economy.bank_amount * (1 - progress))
    text = f'보관 {banked}'
    font.draw(x, y, text, config.COLOR_ORE)
    x += text_width(text)
    if economy.carried > 0:
        font.draw(x, y, f' (+소지 {economy.carried})', config.COLOR_ORE_CARRIED)
    if progress is not None and progress < 1:
        slide = config.ORE_BANK_SLIDE * (1 - progress)
        font.draw(x + slide, y, f' +{economy.bank_amount}', config.COLOR_ORE_CARRIED)


def draw_breath_debug():
    # DEBUG: 광석 줄 아래 구간 타이머 (13.5) - 마지막 숨 회복 지점을 떠난 뒤 시간·쓴 숨·현재 배율
    if not (config.DEBUG and font and breath.has_gauge):
        return
    y = ore_line_y() - config.FONT_SIZE_TEXT - config.ORE_HUD_GAP
    seg = breath.current_segment()
    text = f'숨 {breath.value:.1f}/{breath.capacity():.0f}  배율 {breath.mult:g}'
    if seg:
        text += f"  구간 {seg['time']:.1f}s 쓴 숨 {seg['used']:.1f}"
    if breath.infinite:
        text += '  [F5 무한]'
    font.draw(config.HUD_MARGIN, y, text, config.COLOR_TEXT_DIM)


def draw_breath_vignette():
    # 숨 부족 (7.3, 14.3): BREATH_LOW_RATIO 아래면 화면 가장자리가 점점 어두워진다. 숨 0이면 가장 진하게
    if not breath.is_low() or breath.blackout:
        return
    strength = 1 - breath.ratio() / config.BREATH_LOW_RATIO
    w, h = config.SCREEN_W, config.SCREEN_H
    layers = config.BREATH_VIGNETTE_LAYERS
    d = config.BREATH_VIGNETTE_W / layers
    for i in range(layers):
        alpha = config.BREATH_VIGNETTE_ALPHA * strength * (layers - i) / layers
        o = d * i
        effect.draw_screen_alpha_rect(o, o, w - o, o + d, config.COLOR_FADE, alpha)
        effect.draw_screen_alpha_rect(o, h - o - d, w - o, h - o, config.COLOR_FADE, alpha)
        effect.draw_screen_alpha_rect(o, o + d, o + d, h - o - d, config.COLOR_FADE, alpha)
        effect.draw_screen_alpha_rect(w - o - d, o + d, w - o, h - o - d, config.COLOR_FADE, alpha)


def draw_dash_icon(player):
    # 우상단 대시 쿨타임 원형: 12시 방향부터 시계 방향으로 점이 차오른다
    radius = config.DASH_ICON_RADIUS
    cx = config.SCREEN_W - config.HUD_MARGIN - radius
    cy = config.SCREEN_H - config.HUD_MARGIN - radius
    ready = player.dash_cooldown <= 0
    ratio = 1 - player.dash_cooldown / player.dash_cooldown_time
    half = config.DASH_ICON_DOT / 2
    for i in range(config.DASH_ICON_DOTS):
        angle = math.pi / 2 - 2 * math.pi * i / config.DASH_ICON_DOTS
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        if ready:
            color = config.COLOR_DASH_READY
        elif i < ratio * config.DASH_ICON_DOTS:
            color = config.COLOR_DASH_FILL
        else:
            color = config.COLOR_DASH_COOL
        draw_rectangle(x - half, y - half, x + half, y + half, *color, filled=True)
    if ready:
        inner = radius / 2
        draw_rectangle(cx - inner, cy - inner, cx + inner, cy + inner, *config.COLOR_DASH_READY, filled=True)


def boss_name(key):
    # 정예(10.4)도 보스 HUD(이름 + 자세 게이지)를 같이 쓴다
    if key in config.ELITE_NAME:
        return fonts.text(config.ELITE_NAME[key], config.ELITE_NAME_EN[key])
    return fonts.text(config.BOSS_NAME[key], config.BOSS_NAME_EN[key])


def draw_boss_bar(boss):
    # 하단 중앙 (14.1): 이름(작게) + 자세 게이지. 체력 바는 BOSS_HP_BAR일 때만 (원칙 12: 몸으로 알린다)
    if not boss.show_hud():
        return
    edge = config.HP_BAR_BORDER
    l = (config.SCREEN_W - config.BOSS_BAR_W) / 2
    r = l + config.BOSS_BAR_W
    pb = config.HUD_MARGIN
    pt = pb + config.BOSS_POSTURE_H
    draw_rectangle(l - edge, pb - edge, r + edge, pt + edge, *config.COLOR_HUD_FRAME, filled=True)
    draw_rectangle(l, pb, r, pt, *config.COLOR_POSTURE_BACK, filled=True)
    ratio = boss.posture / config.POSTURE_MAX
    if ratio > 0:
        draw_rectangle(l, pb, l + config.BOSS_BAR_W * ratio, pt, *config.COLOR_POSTURE_FILL, filled=True)
    t = pt
    if config.BOSS_HP_BAR:
        b = pt + config.BOSS_POSTURE_GAP + edge * 2
        t = b + config.BOSS_BAR_H
        draw_rectangle(l - edge, b - edge, r + edge, t + edge, *config.COLOR_HUD_FRAME, filled=True)
        draw_rectangle(l, b, r, t, *config.COLOR_HP_BACK, filled=True)
        hp = max(0, boss.hp) / boss.max_hp
        if hp > 0:
            draw_rectangle(l, b, l + config.BOSS_BAR_W * hp, t, *config.COLOR_BOSS_HP, filled=True)
    f = fonts.get(config.FONT_SIZE_SMALL)
    if f:
        f.draw(l, t + config.BOSS_NAME_GAP, boss_name(boss.boss_key), config.COLOR_TEXT)


def draw_boss_card(boss):
    # 첫 만남 타이틀 카드 (11.2): 이름(큰 글자) + 가로줄 + 칭호. 글자는 알파가 없어 색을 어둡게 해 페이드한다
    alpha = boss.card_alpha()
    if alpha <= 0:
        return
    card = config.BOSS_CARD
    cx = config.SCREEN_W / 2
    half = card['line_w'] / 2
    effect.draw_screen_alpha_rect(cx - half, card['y'], cx + half, card['y'] + card['line_h'],
                                  card['color_line'], 255 * alpha)
    title = fonts.text(config.BOSS_TITLE[boss.boss_key], '')
    for text, size, color, y in ((boss_name(boss.boss_key), card['name_size'], card['color_name'],
                                  card['y'] + card['title_gap']),
                                 (title, card['title_size'], card['color_title'], card['y'] - card['title_gap'] / 2)):
        f = fonts.get(size)
        if not f or not text:
            continue
        width = sum(size if ord(c) >= 0x1100 else size * config.HUD_FONT_NARROW for c in text)
        f.draw(cx - width / 2, y, text, tuple(int(c * alpha) for c in color))


def show_message(text, time=config.HUD_MESSAGE_TIME):
    global message, message_timer
    message, message_timer = text, time


def update(dt):
    global message_timer
    message_timer = max(0, message_timer - dt)


def draw_message():
    # 글자 폭을 알 수 없어 글자 수로 대충 가운데를 맞춘다
    if font and message_timer > 0:
        x = config.SCREEN_W / 2 - len(message) * config.FONT_SIZE_TEXT / 2
        font.draw(x, config.HUD_MESSAGE_Y, message, config.COLOR_TEXT)


def draw(player, boss=None):
    draw_hp_cells(player)
    draw_breath_bar()
    draw_ore()
    draw_breath_debug()
    draw_dash_icon(player)
    if boss:
        draw_boss_bar(boss)
    draw_message()
