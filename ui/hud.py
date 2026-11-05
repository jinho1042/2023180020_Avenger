import math
import os

from pico2d import *

import config

from objects import effect
from systems import breath, upgrades

font = None
icon_font = None
message = ''          # 하단 중앙 알림 문구 ('저장했습니다' 등). message_timer > 0인 동안 보인다
message_timer = 0.0


def init():
    global font, icon_font, message, message_timer
    message, message_timer = '', 0.0
    if os.path.exists(config.FONT_PATH):
        font = load_font(config.FONT_PATH, config.FONT_SIZE_TEXT)
        icon_font = load_font(config.FONT_PATH, config.FONT_SIZE_ICON)


def finish():
    global font, icon_font
    font = None
    icon_font = None


def hp_cells_right(player):
    # 체력 칸 줄의 오른쪽 끝 x (그 오른쪽부터 강화 아이콘)
    return config.HUD_MARGIN + player.max_hp * (config.HP_CELL + config.HP_CELL_GAP) - config.HP_CELL_GAP


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
    if not breath.has_gauge:
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


def draw_breath_debug():
    # DEBUG: 숨 게이지 아래 구간 타이머 (13.5) - 마지막 숨 회복 지점을 떠난 뒤 시간·쓴 숨·현재 배율
    if not (config.DEBUG and font and breath.has_gauge):
        return
    y = (config.SCREEN_H - config.HUD_MARGIN - config.HP_CELL - config.BREATH_BAR_GAP * 2
         - config.BREATH_BAR_H - config.FONT_SIZE_TEXT / 2)
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


def draw_upgrade_icons(player):
    # 체력 칸 오른쪽에 획득한 강화를 카테고리 색 사각형 + 두 글자로 나열
    size = config.UPGRADE_ICON
    l = hp_cells_right(player) + config.HUD_MARGIN
    t = config.SCREEN_H - config.HUD_MARGIN + (size - config.HP_CELL) / 2
    for key in player.upgrades:
        u = upgrades.BY_KEY[key]
        draw_rectangle(l, t - size, l + size, t, *config.COLOR_HUD_FRAME, filled=True)
        edge = config.HP_BAR_BORDER
        draw_rectangle(l + edge, t - size + edge, l + size - edge, t - edge,
                       *config.COLOR_UPGRADE[u.category], filled=True)
        if icon_font:
            icon_font.draw(l + config.UPGRADE_ICON_PAD, t - size / 2, u.icon, config.COLOR_HUD_FRAME)
        l += size + config.UPGRADE_ICON_GAP


def draw_boss_bar(boss):
    # 하단 중앙: 이름 · 체력 바 · 그 아래 자세 게이지 (패링 성공마다 한 칸)
    edge = config.HP_BAR_BORDER
    l = (config.SCREEN_W - config.BOSS_BAR_W) / 2
    r = l + config.BOSS_BAR_W
    pb = config.HUD_MARGIN
    pt = pb + config.BOSS_POSTURE_H
    b = pt + config.BOSS_POSTURE_GAP + edge * 2
    t = b + config.BOSS_BAR_H
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *config.COLOR_HUD_FRAME, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_HP_BACK, filled=True)
    ratio = max(0, boss.hp) / boss.max_hp
    if ratio > 0:
        draw_rectangle(l, b, l + config.BOSS_BAR_W * ratio, t, *config.COLOR_BOSS_HP, filled=True)

    gap = config.BOSS_POSTURE_GAP
    cell = (config.BOSS_BAR_W - gap * (config.POSTURE_MAX - 1)) / config.POSTURE_MAX
    for i in range(config.POSTURE_MAX):
        cl = l + i * (cell + gap)
        draw_rectangle(cl - edge, pb - edge, cl + cell + edge, pt + edge, *config.COLOR_HUD_FRAME, filled=True)
        color = config.COLOR_POSTURE_FILL if i < boss.posture else config.COLOR_POSTURE_BACK
        draw_rectangle(cl, pb, cl + cell, pt, *color, filled=True)
    if font:
        font.draw(l, t + config.BOSS_NAME_GAP, config.BOSS_NAME[boss.boss_key], config.COLOR_TEXT)


def show_message(text):
    global message, message_timer
    message, message_timer = text, config.HUD_MESSAGE_TIME


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
    draw_breath_debug()
    draw_dash_icon(player)
    draw_upgrade_icons(player)
    if boss:
        draw_boss_bar(boss)
    draw_message()
