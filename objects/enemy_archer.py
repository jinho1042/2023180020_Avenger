import math

from pico2d import *

import config
from objects import projectile
from objects.enemy_base import ACTIVE, TELEGRAPH, WINDUP, Attack, EnemyBase

STATS = config.ARCHER


class EnemyArcher(EnemyBase):
    # 원거리 궁수: keep_distance를 유지하며 (가까우면 후퇴) 플레이어를 조준해 화살 발사 (흰색 예고)
    def __init__(self, x, y, player, platforms):
        # 근접 공격이 없으므로 attack_range는 사거리로 쓴다
        super().__init__(x, y, dict(STATS, attack_range=STATS['shoot_range']), player, platforms)
        self.shoot = Attack('arrow', True, STATS['telegraph'], STATS['windup'], STATS['active'],
                            STATS['recover'], STATS['damage'], None)

    def choose_attacks(self):
        return [self.shoot]

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        dist = abs(self.player.x - self.x)
        if dist <= self.attack_range and self.attack_cooldown <= 0:
            self.attack_queue = self.choose_attacks()
            self.start_next_attack()
        elif dist < STATS['keep_distance'] - STATS['distance_tolerance']:
            # 플레이어를 바라본 채로 뒷걸음질
            self.vx = -self.face_dir * self.speed
        elif dist > STATS['keep_distance'] + STATS['distance_tolerance']:
            self.vx = self.face_dir * self.speed

    def bow_pos(self):
        return self.x + self.face_dir * self.w / 2, self.y + self.h * 2 / 3

    def next_phase(self):
        super().next_phase()
        if self.state == ACTIVE:
            # 발사 순간 플레이어 몸 중심을 조준한다
            bx, by = self.bow_pos()
            dx = self.player.x - bx
            dy = (self.player.y + config.PLAYER_H / 2) - by
            dist = math.hypot(dx, dy) or 1
            projectile.fire(bx, by, dx / dist, dy / dist, STATS['arrow_speed'], self.attack.damage,
                            self.attack.parryable, self.platforms, config.ARROW)

    def draw_weapon(self, l, b, r, t):
        # 활: 몸 앞쪽 세로 막대. 예고·시위 당김 중에는 화살을 메긴 모습
        bx, by = self.bow_pos()
        half = self.h / 4
        thick = self.w / 8
        draw_rectangle(bx, by - half, bx + self.face_dir * thick, by + half, *config.COLOR_BOW, filled=True)
        if self.state in (TELEGRAPH, WINDUP):
            length = config.ARROW['length']
            tail = bx - self.face_dir * length / 2
            draw_rectangle(min(tail, bx), by - thick / 2, max(tail, bx), by + thick / 2,
                           *config.COLOR_ENEMY_WINDUP, filled=True)
