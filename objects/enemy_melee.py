import random

from pico2d import *

import config
from objects.enemy_base import ACTIVE, RECOVER, Attack, EnemyBase

STATS = config.MELEE


class EnemyMelee(EnemyBase):
    # 근거리 병사: 접근해서 베기 2연타 (흰색 예고). 확률적으로 방패 돌진 (빨간색 예고, 패링 불가)
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.slash1 = Attack('slash1', True, STATS['telegraph'], STATS['windup'], STATS['active'],
                             STATS['recover'], STATS['damage'], STATS['hitbox'])
        self.slash2 = Attack('slash2', True, STATS['combo_telegraph'], STATS['windup'], STATS['active'],
                             STATS['combo_recover'], STATS['damage'], STATS['hitbox'])
        self.shield_rush = Attack('shield_rush', False, STATS['rush_telegraph'], STATS['rush_windup'],
                                  STATS['rush_time'], STATS['rush_recover'], STATS['rush_damage'],
                                  STATS['rush_hitbox'])

    def choose_attacks(self):
        if random.random() < STATS['shield_rush_chance']:
            return [self.shield_rush]
        return [self.slash1, self.slash2]

    def is_rushing(self):
        return self.state == ACTIVE and self.attack is self.shield_rush

    def move(self, dt):
        # 돌진 방향은 예고 시작 때 바라본 방향으로 고정 (도중에 플레이어를 따라 꺾지 않는다)
        if self.is_rushing():
            self.vx = self.face_dir * STATS['rush_speed']
        super().move(dt)

    def draw_weapon(self, l, b, r, t):
        if self.attack is not self.shield_rush or self.state == RECOVER:
            super().draw_weapon(l, b, r, t)
            return
        # 예고·모션·돌진 중엔 몸 앞에 방패를 세운다
        shield_w, shield_h = STATS['rush_hitbox']
        sb = b + (self.h - shield_h) / 2
        if self.face_dir > 0:
            draw_rectangle(r, sb, r + shield_w, sb + shield_h, *config.COLOR_SHIELD, filled=True)
        else:
            draw_rectangle(l - shield_w, sb, l, sb + shield_h, *config.COLOR_SHIELD, filled=True)
