import os

from pico2d import *

import config
import game_world
from systems import camera

star_font = None  # 처음 그릴 때 불러온다 (없으면 별 대신 사각형)


def _get_star_font():
    global star_font
    if star_font is None and os.path.exists(config.FONT_PATH):
        star_font = load_font(config.FONT_PATH, config.FONT_SIZE_STAR)
    return star_font


class Door:
    # x, y는 문 아래쪽 중심 좌표. 방에 들어오면 잠겨 있다가 적이 전멸하면 열린다
    # route가 있으면 안전지대의 루트 문: 문 위에 루트 색 표지판과 난이도 별을 그린다
    # cleared면 보스를 처치한 루트: 잠긴 채로 별 대신 'CLEAR'를 그린다
    # chest면 연결된 방에 보물상자가 있음: 문 위에 상자 아이콘을 그린다
    def __init__(self, x, y, route=None):
        self.x, self.y = x, y
        self.route = route
        self.opened = False
        self.cleared = False
        self.chest = False

    def open(self):
        self.opened = True

    def update(self):
        pass

    def draw(self):
        l, b, r, t = self.get_bb()
        camera.draw_rect(l - config.DOOR_FRAME, b, r + config.DOOR_FRAME, t + config.DOOR_FRAME,
                       *config.COLOR_DOOR_FRAME, filled=True)
        if self.cleared:
            color = config.COLOR_DOOR_CLEARED
        else:
            color = config.COLOR_DOOR_OPEN if self.opened else config.COLOR_DOOR_LOCKED
        camera.draw_rect(l, b, r, t, *color, filled=True)
        if self.route:
            self.draw_sign(t + config.DOOR_FRAME + config.DOOR_SIGN_GAP)
        if self.chest:
            self.draw_chest_icon(t + config.DOOR_FRAME + config.CHEST_ICON_GAP)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def draw_sign(self, bottom):
        half_w = config.DOOR_SIGN_W / 2
        top = bottom + config.DOOR_SIGN_H
        border = config.DOOR_SIGN_BORDER
        camera.draw_rect(self.x - half_w, bottom, self.x + half_w, top, *config.COLOR_DOOR_FRAME, filled=True)
        camera.draw_rect(self.x - half_w + border, bottom + border, self.x + half_w - border, top - border,
                       *config.ROUTE_COLOR[self.route], filled=True)
        stars = config.ROUTE_STARS[self.route]
        cy = (bottom + top) / 2
        font = _get_star_font()
        if self.cleared:
            self.draw_clear_mark(cy, font)
            return
        if font:
            text = '★' * stars
            # 글자 폭을 대략 글자 크기로 보고 가운데 정렬
            font.draw(*camera.to_screen(self.x - len(text) * config.FONT_SIZE_STAR / 2, cy), text, config.COLOR_DOOR_STAR)
            return
        size, gap = config.DOOR_STAR_SIZE, config.DOOR_STAR_GAP
        left = self.x - (stars * size + (stars - 1) * gap) / 2
        for i in range(stars):
            x = left + i * (size + gap)
            camera.draw_rect(x, cy - size / 2, x + size, cy + size / 2, *config.COLOR_DOOR_STAR, filled=True)

    def draw_clear_mark(self, cy, font):
        if font:
            text = 'CLEAR'
            # 영문 대문자 폭을 대략 글자 크기의 0.6배로 보고 가운데 정렬
            font.draw(*camera.to_screen(self.x - len(text) * config.FONT_SIZE_STAR * 0.3, cy), text, config.COLOR_DOOR_STAR)
            return
        half_w = config.DOOR_SIGN_W / 2 - config.DOOR_SIGN_BORDER * 2
        half_h = config.DOOR_STAR_SIZE / 2
        camera.draw_rect(self.x - half_w, cy - half_h, self.x + half_w, cy + half_h, *config.COLOR_DOOR_STAR, filled=True)

    def draw_chest_icon(self, bottom):
        half_w, edge = config.CHEST_ICON_W / 2, config.DOOR_SIGN_BORDER
        top = bottom + config.CHEST_ICON_H
        band = config.CHEST_BAND / 4
        camera.draw_rect(self.x - half_w - edge, bottom - edge, self.x + half_w + edge, top + edge,
                       *config.COLOR_DOOR_FRAME, filled=True)
        camera.draw_rect(self.x - half_w, bottom, self.x + half_w, top, *config.COLOR_CHEST, filled=True)
        camera.draw_rect(self.x - band, bottom, self.x + band, top, *config.COLOR_CHEST_BAND, filled=True)

    def get_bb(self):
        half_w = config.DOOR_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.DOOR_H

    def handle_collision(self, group, other):
        pass
