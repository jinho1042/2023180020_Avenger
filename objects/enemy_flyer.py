import math

from pico2d import *

import config
import game_framework
from objects.enemy_base import ACTIVE, CHASE, RECOVER, Attack, EnemyBase
from systems import terrain

STATS = config.FLYER


class EnemyFlyer(EnemyBase):
    # 플라잉 몹: 중력 없이 플레이어 머리 위로 이동해 급강하 돌진 (흰색 예고). 패링당하면 즉시 격추
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.hover_height = STATS['hover_height']
        self.hover_tolerance = STATS['hover_tolerance']
        self.dive = Attack('dive', True, STATS['telegraph'], STATS['windup'], STATS['dive_time'],
                           STATS['recover'], STATS['damage'], None)
        self.dive_vx, self.dive_vy = 0.0, 0.0

    def choose_attacks(self):
        return [self.dive]

    def hover_target(self):
        ty = self.player.y + self.hover_height
        return self.player.x, min(ty, config.SCREEN_H - self.h - STATS['ceiling_margin'])

    def chase(self):
        self.vx, self.vy = 0, 0
        if self.player.dead:
            return
        self.face_player()
        tx, ty = self.hover_target()
        dx, dy = tx - self.x, ty - self.y
        if abs(dx) <= self.attack_range and abs(dy) <= self.hover_tolerance and self.attack_cooldown <= 0:
            self.attack_queue = self.choose_attacks()
            self.start_next_attack()
            return
        dist = math.hypot(dx, dy)
        dt = game_framework.frame_time
        if dist > 0 and dt > 0:
            # 목표점을 지나치지 않게 이번 프레임에 갈 수 있는 거리로 속도를 줄인다
            speed = min(self.speed, dist / dt)
            self.vx, self.vy = dx / dist * speed, dy / dist * speed

    def next_phase(self):
        super().next_phase()
        if self.state == ACTIVE:
            # 돌진 방향은 판정 시작 순간 플레이어 몸 중심으로 고정한다
            dx = self.player.x - self.x
            dy = (self.player.y + config.PLAYER_H / 2) - (self.y + self.h / 2)
            dist = math.hypot(dx, dy) or 1
            self.dive_vx = dx / dist * STATS['dive_speed']
            self.dive_vy = dy / dist * STATS['dive_speed']
            if dx != 0:
                self.face_dir = 1 if dx > 0 else -1

    def on_parried(self):
        self.die()

    def move(self, dt):
        if self.state == ACTIVE:
            self.vx, self.vy = self.dive_vx, self.dive_vy
        elif self.state != CHASE:
            self.vx, self.vy = 0, 0
        self.move_x(dt)
        prev_y = self.y
        self.y += self.vy * dt
        self.y, self.vy, self.on_ground = terrain.resolve_y(
            self.x, prev_y, self.y, self.vy, self.w, self.h, self.platforms)
        self.y = clamp(0, self.y, config.SCREEN_H - self.h)
        if self.state == ACTIVE and self.on_ground:
            # 바닥에 부딪히면 돌진을 끝내고 그 자리에서 후딜레이
            self.set_state(RECOVER, self.attack.recover)

    def get_attack_bb(self):
        # 돌진 중에는 몸 전체가 공격 판정
        if self.state != ACTIVE:
            return None
        return self.get_bb()

    def draw_weapon(self, l, b, r, t):
        # 날개: 평소엔 수평, 예고·공격 모션·돌진 중엔 위로 접는다
        wing = self.w / 2
        thick = self.h / 6
        mid = (b + t) / 2
        if self.attack is not None and self.state != RECOVER:
            draw_rectangle(l - thick, mid, l, t + thick, *config.COLOR_ENEMY_WINDUP, filled=True)
            draw_rectangle(r, mid, r + thick, t + thick, *config.COLOR_ENEMY_WINDUP, filled=True)
        else:
            draw_rectangle(l - wing, mid, l, mid + thick, *self.color, filled=True)
            draw_rectangle(r, mid, r + wing, mid + thick, *self.color, filled=True)
