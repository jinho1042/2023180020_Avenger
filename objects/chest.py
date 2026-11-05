from pico2d import *

import config
import game_framework
import game_world
from objects import effect
from systems import camera, sound


class Chest:
    # x, y는 상자 아래쪽 중심 좌표. 방의 적이 전멸하면 잠금이 풀리고, 플레이어가 닿으면 열린다
    # 열리면 빛 기둥을 CHEST_PILLAR_TIME 동안 보여준 뒤 reward_ready가 켜진다 (play_mode가 강화 화면을 띄움)
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.unlocked = False
        self.opened = False
        self.pillar_timer = 0.0
        self.reward_ready = False

    def unlock(self):
        self.unlocked = True

    def can_open(self):
        return self.unlocked and not self.opened

    def open(self):
        self.opened = True
        self.pillar_timer = config.CHEST_PILLAR_TIME
        sound.play('chest')

    def take_reward(self):
        self.reward_ready = False

    def update(self):
        if self.pillar_timer > 0:
            self.pillar_timer -= game_framework.frame_time
            if self.pillar_timer <= 0:
                self.reward_ready = True

    def draw(self):
        l, b, r, t = self.get_bb()
        if self.opened:
            color = config.COLOR_CHEST_OPENED
        else:
            color = config.COLOR_CHEST if self.unlocked else config.COLOR_CHEST_LOCKED
        lid_b = t - config.CHEST_LID_H
        lift = config.CHEST_LID_LIFT if self.opened else 0
        camera.draw_rect(l, b, r, lid_b, *color, filled=True)
        camera.draw_rect(l, lid_b + lift, r, t + lift, *color, filled=True)
        if not self.opened:
            # 잠금쇠: 적이 남아 있으면 어두운 색으로 잠금 표시
            band = config.CHEST_BAND / 2
            band_color = config.COLOR_CHEST_BAND if self.unlocked else config.COLOR_DOOR_LOCKED
            camera.draw_rect(self.x - band, b, self.x + band, t, *band_color, filled=True)
        if self.pillar_timer > 0:
            half_w = config.CHEST_PILLAR_W / 2
            alpha = config.CHEST_PILLAR_ALPHA * self.pillar_timer / config.CHEST_PILLAR_TIME
            effect.draw_alpha_rect(self.x - half_w, t, self.x + half_w, game_world.room_h,
                                   config.COLOR_CHEST_PILLAR, alpha)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def get_bb(self):
        half_w = config.CHEST_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.CHEST_H

    def handle_collision(self, group, other):
        pass
