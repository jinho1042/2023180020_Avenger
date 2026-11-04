import random

import config
from objects.enemy_base import CHASE, STAGGER, EnemyBase
from objects import effect

GROGGY = 'Groggy'


class BossBase(EnemyBase):
    # 보스 공통: 패링당할 때마다 자세(posture)가 쌓이고 POSTURE_MAX에 도달하면 그로기
    # 패턴은 가중치 랜덤으로 고르고, 같은 패턴 3연속은 금지한다
    is_boss = True

    def __init__(self, x, y, stats, player, platforms):
        # 공격 사거리는 패턴마다 다르므로 attack_range는 쓰지 않는다
        super().__init__(x, y, dict(stats, attack_range=stats['near_range']), player, platforms)
        self.max_hp = self.hp
        self.posture = 0
        self.history = []  # 최근 사용한 패턴 이름

    def pick_pattern(self, weights):
        names = [n for n, w in weights.items()
                 if w > 0 and self.history[-2:] != [n, n]]
        if not names:
            return None
        return random.choices(names, [weights[n] for n in names])[0]

    def remember_pattern(self, name):
        self.history = (self.history + [name])[-2:]

    def next_phase(self):
        if self.state == GROGGY:
            self.attack_cooldown = self.attack_cooldown_time
            self.set_state(CHASE)
        else:
            super().next_phase()

    def on_parried(self):
        if not self.add_posture():
            self.recoil()

    def add_posture(self):
        # 자세 +1. POSTURE_MAX에 도달하면 그로기에 들어가고 True. 이미 그로기 중이면 쌓지 않는다
        # [v2] 보스의 투사체를 반사한 것도 패링 성공이므로 combat에서 이것을 부른다
        if self.state == GROGGY:
            return False
        self.posture += 1
        if self.posture < config.POSTURE_MAX:
            return False
        self.posture = 0
        self.cancel_attack()
        self.set_state(GROGGY, config.GROGGY_TIME)
        effect.boss_groggy(self.x, self.y + self.h / 2)
        return True

    def recoil(self):
        # 보스는 길게 비틀거리지 않고 잠깐만 멈칫한다
        self.cancel_attack()
        self.set_state(STAGGER, config.BOSS_PARRY_RECOIL)

    def cancel_attack(self):
        self.attack_queue = []
        self.attack = None
        self.attack_cooldown = self.attack_cooldown_time

    def take_damage(self, damage, knockback=0):
        # 묵직해서 넉백을 받지 않는다
        if self.state == GROGGY:
            damage *= config.GROGGY_DAMAGE_MULT
        super().take_damage(damage)

    def body_color(self):
        if self.state == GROGGY:
            return config.COLOR_BOSS_GROGGY
        return super().body_color()
