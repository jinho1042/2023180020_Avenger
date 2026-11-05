import math

from pico2d import *

import config
from objects import effect, projectile
from objects.enemy_base import ACTIVE, TELEGRAPH, WINDUP, Attack, EnemyBase
from systems import camera

STATS = config.CRYSTAL_SPRITE


class CrystalSprite(EnemyBase):
    # 수정 유생 (10.2, ← v2 견습 마법사): keep_distance를 유지하며 (가까우면 걸어서 후퇴) 플레이어를 조준해 느린 마력탄 1발 (흰색, 반사 가능)
    # 수정 술사가 이 클래스를 이어받아 공격만 바꾼다
    stats = STATS

    def __init__(self, x, y, player, platforms):
        s = self.stats
        # 근접 공격이 없으므로 attack_range는 사거리, 공격 쿨타임은 시전 쿨타임으로 쓴다
        super().__init__(x, y, dict(s, attack_range=s['shoot_range'], attack_cooldown=s['cast_cooldown']),
                         player, platforms)
        self.bolt = Attack('bolt', True, s['telegraph'], s['windup'], s['active'],
                           s['recover'], s['damage'], None)

    def choose_attacks(self):
        return [self.bolt]

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        s = self.stats
        dist = abs(self.player.x - self.x)
        if dist <= self.attack_range and self.attack_cooldown <= 0:
            self.attack_queue = self.choose_attacks()
            self.start_next_attack()
        elif dist < s['keep_distance'] - s['distance_tolerance']:
            # 플레이어를 바라본 채로 뒷걸음질
            self.vx = -self.face_dir * self.speed
        elif dist > s['keep_distance'] + s['distance_tolerance']:
            self.vx = self.face_dir * self.speed

    def orb_pos(self):
        # 지팡이 끝 구슬 (마력탄이 나가는 자리)
        return self.x + self.face_dir * self.w * 3 / 4, self.y + self.h * 3 / 4

    def aim(self, x, y):
        # (x, y)에서 플레이어 몸 중심을 향하는 각도 (라디안)
        return math.atan2(self.player.y + config.PLAYER_H / 2 - y, self.player.x - x)

    def fire_bolt(self, angle):
        x, y = self.orb_pos()
        projectile.fire(x, y, math.cos(angle), math.sin(angle), self.stats['bolt_speed'], self.attack_damage(),
                        self.attack.parryable, self.platforms, config.MAGIC_BOLT, owner=self)

    def next_phase(self):
        super().next_phase()
        if self.state == ACTIVE and self.attack.name == 'bolt':
            self.cast_bolts()

    def cast_bolts(self):
        # 발사 순간 플레이어를 조준한다
        self.fire_bolt(self.aim(*self.orb_pos()))

    def draw_weapon(self, l, b, r, t):
        # 지팡이: 몸 앞쪽 세로 막대 + 끝의 구슬. 예고·시전 중에는 구슬이 커지며 빛난다
        ox, oy = self.orb_pos()
        thick = self.w / 8
        camera.draw_rect(ox - thick / 2, b, ox + thick / 2, oy, *config.COLOR_STAFF, filled=True)
        if self.state in (TELEGRAPH, WINDUP):
            effect.draw_disc(ox, oy, config.MAGIC_BOLT['size'] / 2, config.COLOR_ENEMY_WINDUP)
        else:
            effect.draw_disc(ox, oy, thick, config.COLOR_STAFF_ORB)
