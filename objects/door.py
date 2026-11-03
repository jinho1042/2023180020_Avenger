from pico2d import *

import config
import game_world


class Door:
    # x, y는 문 아래쪽 중심 좌표. 방에 들어오면 잠겨 있다가 적이 전멸하면 열린다
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.opened = False

    def open(self):
        self.opened = True

    def update(self):
        pass

    def draw(self):
        l, b, r, t = self.get_bb()
        draw_rectangle(l - config.DOOR_FRAME, b, r + config.DOOR_FRAME, t + config.DOOR_FRAME,
                       *config.COLOR_DOOR_FRAME, filled=True)
        color = config.COLOR_DOOR_OPEN if self.opened else config.COLOR_DOOR_LOCKED
        draw_rectangle(l, b, r, t, *color, filled=True)
        if game_world.show_hitbox:
            draw_rectangle(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def get_bb(self):
        half_w = config.DOOR_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.DOOR_H

    def handle_collision(self, group, other):
        pass
