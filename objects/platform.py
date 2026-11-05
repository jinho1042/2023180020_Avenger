from pico2d import *

import config
from systems import camera


class Platform:
    # x, y는 좌하단 좌표. kind는 'solid'(사방 충돌) 또는 'oneway'(위에서만 착지)
    def __init__(self, x, y, w, h, kind):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.kind = kind

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y

    @property
    def top(self):
        return self.y + self.h

    def update(self):
        pass

    def draw(self):
        color = config.COLOR_SOLID if self.kind == 'solid' else config.COLOR_ONEWAY
        camera.draw_rect(self.left, self.bottom, self.right, self.top, *color, filled=True)

    def get_bb(self):
        return self.left, self.bottom, self.right, self.top

    def handle_collision(self, group, other):
        pass
