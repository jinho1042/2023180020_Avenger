import math

from pico2d import *

import config
from objects import projectile
from objects.enemy_base import ACTIVE, TELEGRAPH, WINDUP, Attack, EnemyBase
from systems import camera

STATS = config.THORN_FLOWER


class ThornFlower(EnemyBase):
    # 가시꽃 (10.2, ← v2 궁수): 제자리에 고정된 채 플레이어를 조준해 가시 발사 (흰색 예고, 반사 해금 후 반사 가능)
    # 행동은 v2 궁수 그대로이고 이동만 뺐다 (keep_distance 후퇴·접근 없음)
    def __init__(self, x, y, player, platforms):
        # 근접 공격이 없으므로 attack_range는 사거리, 공격 쿨타임은 발사 쿨타임으로 쓴다
        super().__init__(x, y, dict(STATS, attack_range=STATS['shoot_range'], attack_cooldown=STATS['cooldown']),
                         player, platforms)
        self.shoot = Attack('thorn', True, STATS['telegraph'], STATS['windup'], STATS['active'],
                            STATS['recover'], STATS['damage'], None)

    def choose_attacks(self):
        return [self.shoot]

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        if abs(self.player.x - self.x) <= self.attack_range and self.attack_cooldown <= 0:
            self.attack_queue = self.choose_attacks()
            self.start_next_attack()

    def bud_pos(self):
        # 꽃봉오리 (가시가 나가는 자리)
        return self.x + self.face_dir * self.w / 2, self.y + self.h * 2 / 3

    def next_phase(self):
        super().next_phase()
        if self.state == ACTIVE:
            # 발사 순간 플레이어 몸 중심을 조준한다
            bx, by = self.bud_pos()
            dx = self.player.x - bx
            dy = (self.player.y + config.PLAYER_H / 2) - by
            dist = math.hypot(dx, dy) or 1
            projectile.fire(bx, by, dx / dist, dy / dist, STATS['thorn_speed'], self.attack_damage(),
                            self.attack.parryable, self.platforms, config.ARROW, owner=self)

    def draw_weapon(self, l, b, r, t):
        # 꽃봉오리: 몸 앞쪽 위. 예고·조준 중에는 벌어지며 가시가 보인다
        bx, by = self.bud_pos()
        half = self.w / 4
        camera.draw_rect(bx - half, by - half, bx + half, by + half, *config.COLOR_THORN_BUD, filled=True)
        if self.state in (TELEGRAPH, WINDUP):
            length = config.ARROW['length'] / 2
            thick = self.w / 8
            tip = bx + self.face_dir * length
            camera.draw_rect(min(tip, bx), by - thick / 2, max(tip, bx), by + thick / 2,
                           *config.COLOR_ENEMY_WINDUP, filled=True)
