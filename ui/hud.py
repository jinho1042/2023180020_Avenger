import math
import os

from pico2d import *

import config

from systems import upgrades

font = None
icon_font = None


def init():
    global font, icon_font
    if os.path.exists(config.FONT_PATH):
        font = load_font(config.FONT_PATH, config.FONT_SIZE_TEXT)
        icon_font = load_font(config.FONT_PATH, config.FONT_SIZE_ICON)


def finish():
    global font, icon_font
    font = None
    icon_font = None


def draw_hp_bar(player):
    # 좌상단 체력 바
    l = config.HUD_MARGIN
    t = config.SCREEN_H - config.HUD_MARGIN
    r, b = l + config.HP_BAR_W, t - config.HP_BAR_H
    edge = config.HP_BAR_BORDER
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *config.COLOR_HUD_FRAME, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_HP_BACK, filled=True)
    ratio = player.hp / player.max_hp
    if ratio > 0:
        color = config.COLOR_HP_LOW if ratio <= config.HP_LOW_RATIO else config.COLOR_HP_FILL
        draw_rectangle(l, b, l + config.HP_BAR_W * ratio, t, *color, filled=True)
    if font:
        font.draw(r + config.HUD_MARGIN, (b + t) / 2, f'{math.ceil(player.hp)}', config.COLOR_TEXT)


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
    # 체력 바 오른쪽에 획득한 강화를 카테고리 색 사각형 + 두 글자로 나열
    size = config.UPGRADE_ICON
    l = config.HUD_MARGIN + config.HP_BAR_W + config.HUD_MARGIN + config.HUD_HP_TEXT_W
    t = config.SCREEN_H - config.HUD_MARGIN + (size - config.HP_BAR_H) / 2
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


def draw(player, boss=None):
    draw_hp_bar(player)
    draw_dash_icon(player)
    draw_upgrade_icons(player)
    if boss:
        draw_boss_bar(boss)
