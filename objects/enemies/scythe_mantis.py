from pico2d import *

import config
from objects.enemy_base import WINDUP, Attack, EnemyBase
from systems import camera

STATS = config.SCYTHE_MANTIS


class ScytheMantis(EnemyBase):
    # 쌍낫 사마귀 (10.2, ← v2 쌍단검 병사): 빠르게 접근해 combo연속 베기 (흰색). 첫 타만 telegraph, 이후 각 타는 combo_interval로 짧게 번쩍인다
    # 쌍검 기사 4연속 베기의 축소판. 패링해도 연타가 끊기지 않아 전부 이어서 패링해야 한다
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.combo = []
        for i in range(STATS['combo']):
            telegraph = STATS['telegraph'] if i == 0 else STATS['combo_interval']
            recover = STATS['last_recover'] if i == STATS['combo'] - 1 else STATS['recover']
            self.combo.append(Attack('slash', True, telegraph, STATS['windup'], STATS['active'],
                                     recover, STATS['damage'], STATS['hitbox']))

    def choose_attacks(self):
        return list(self.combo)

    def on_parried(self):
        # 남은 타가 있으면 멈추지 않고 다음 타로 이어간다. 마지막 타를 패링당하면 비틀거린다
        if self.attack_queue:
            return
        super().on_parried()

    def draw_weapon(self, l, b, r, t):
        if self.state == WINDUP:
            super().draw_weapon(l, b, r, t)
            return
        # 양손에 짧은 단검을 몸 양옆에 내려 든다
        blade = self.w / 8
        length = self.h / 3
        cy = b + self.h / 3
        for side in (l, r):
            camera.draw_rect(side - blade / 2, cy - length / 2, side + blade / 2, cy + length / 2,
                           *config.COLOR_DAGGER, filled=True)
