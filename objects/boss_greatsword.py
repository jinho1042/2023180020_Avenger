from pico2d import *

import config
from objects.boss_base import GROGGY, BossBase, boss_damage
from objects.enemy_base import ACTIVE, RECOVER, WINDUP, Attack
from systems import camera

STATS = config.BOSS_GREATSWORD


class BossGreatsword(BossBase):
    # 중간 보스 대검 기사: 내려찍기(흰색) · 회전 베기(빨간색, 광역) · 돌진 찌르기(흰색)
    boss_key = 'greatsword'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.patterns = {}
        for name, parryable in (('slam', True), ('spin', False), ('thrust', True)):
            p = STATS[name]
            self.patterns[name] = Attack(name, parryable, p['telegraph'], p['windup'], p['active'],
                                         p['recover'], boss_damage(STATS, parryable), p['hitbox'])

    def choose_pattern(self, dist):
        if dist <= STATS['near_range']:
            return self.pick_pattern(STATS['near'])
        if dist <= STATS['thrust_range']:
            return self.pick_pattern(STATS['far'])
        return None

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        dist = abs(self.player.x - self.x)
        name = self.choose_pattern(dist) if self.attack_cooldown <= 0 else None
        if name:
            self.remember_pattern(name)
            self.attack_queue = [self.patterns[name]]
            self.start_next_attack()
        elif dist > STATS['near_range'] / 2:
            self.vx = self.face_dir * self.speed

    def is_thrusting(self):
        return self.state == ACTIVE and self.attack is self.patterns['thrust']

    def move(self, dt):
        # 돌진 방향은 예고 시작 때 바라본 방향으로 고정
        if self.is_thrusting():
            self.vx = self.face_dir * STATS['thrust']['speed']
        super().move(dt)

    def get_attack_bb(self):
        if self.state == ACTIVE and self.attack is self.patterns['spin']:
            # 회전 베기는 몸 중심 좌우로 펼쳐진다
            w, h = self.attack.hitbox
            b = self.y + (self.h - h) / 2
            return self.x - w / 2, b, self.x + w / 2, b + h
        return super().get_attack_bb()

    def draw_weapon(self, l, b, r, t):
        # 평소엔 대검을 몸 앞에 세워 든다. 모션 중엔 패턴별 자세
        blade = self.w / 6
        if self.state == WINDUP and self.attack is self.patterns['spin']:
            # 회전 직전: 대검을 몸 뒤로 수평으로 뺀다
            sx = self.x - self.face_dir * (self.w / 2 + self.h / 2)
            cy = b + self.h / 2
            camera.draw_rect(min(sx, self.x), cy - blade / 2, max(sx, self.x), cy + blade / 2,
                           *config.COLOR_GREATSWORD, filled=True)
        elif self.state == WINDUP:
            super().draw_weapon(l, b, r, t)
        elif self.state in (ACTIVE, RECOVER, GROGGY):
            # 휘두른 뒤·그로기: 대검 끝이 바닥에 닿아 있다
            fx = r if self.face_dir > 0 else l
            camera.draw_rect(fx + self.face_dir * blade - blade / 2, b, fx + self.face_dir * blade + blade / 2,
                           b + self.h / 2, *config.COLOR_GREATSWORD, filled=True)
        else:
            fx = r if self.face_dir > 0 else l
            camera.draw_rect(fx - blade / 2, b + self.h / 3, fx + blade / 2, t + self.h / 4,
                           *config.COLOR_GREATSWORD, filled=True)
