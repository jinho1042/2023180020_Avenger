import random

from pico2d import *

import config
import game_framework
from objects import effect
from objects.enemies.crystal_sage import fit_x
from objects.enemy_base import WINDUP, Attack, EnemyBase

STATS = config.SHADOW_STALKER


class ShadowStalker(EnemyBase):
    # 그림자 사냥꾼 (10.2, ← v2 그림자 암살자): 거리를 두고 배회하다가
    # ① 순간이동 기습 (빨간색, 대시로 회피): 예고 → fade_time 동안 흐려짐 → 플레이어 등 뒤에 나타나 베기
    # ② stab_chance 확률로 걸어서 접근해 정면 찌르기 (흰색)
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.stab = Attack('stab', True, STATS['telegraph'], STATS['stab_windup'], STATS['stab_active'],
                           STATS['stab_recover'], STATS['damage'], STATS['stab_hitbox'])
        # Windup = 흐려짐(fade_time) + 나타난 뒤 베기 전 동작(appear_windup)
        self.ambush = Attack('ambush', False, STATS['telegraph'], STATS['fade_time'] + STATS['appear_windup'],
                             STATS['slash_active'], STATS['slash_recover'], STATS['damage'],
                             STATS['slash_hitbox'])
        self.plan = None  # 다음에 쓸 공격 ('stab' | 'ambush')
        self.vanishing = False  # 기습을 시작해 아직 플레이어 뒤로 순간이동하지 않았는지
        # 방에 들어오자마자 기습하지 않게 쿨타임을 채운 채 시작한다
        self.teleport_cooldown = STATS['teleport_cooldown']

    def update(self):
        self.teleport_cooldown = max(0, self.teleport_cooldown - game_framework.frame_time)
        super().update()

    def choose_plan(self):
        if self.teleport_cooldown <= 0 and random.random() >= STATS['stab_chance']:
            return 'ambush'
        return 'stab'

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        if self.attack_cooldown <= 0 and self.plan is None:
            self.plan = self.choose_plan()
        # 플레이어가 다른 높이에 있어 찌르기가 닿지 않으면 기습으로 바꾼다
        if (self.plan == 'stab' and self.teleport_cooldown <= 0
                and abs(self.player.y - self.y) >= self.h):
            self.plan = 'ambush'

        if self.plan == 'ambush':
            self.teleport_cooldown = STATS['teleport_cooldown']
            self.start_plan(self.ambush)
        elif self.plan == 'stab':
            if self.in_attack_range():
                self.start_plan(self.stab)
            else:
                self.vx = self.face_dir * self.speed
        else:
            self.roam()

    def start_plan(self, attack):
        self.plan = None
        self.vanishing = attack is self.ambush
        self.attack_queue = [attack]
        self.start_next_attack()

    def roam(self):
        # keep_distance ± distance_tolerance를 유지한다 (가까우면 플레이어를 바라본 채 뒷걸음질)
        dist = abs(self.player.x - self.x)
        if dist < STATS['keep_distance'] - STATS['distance_tolerance']:
            self.vx = -self.face_dir * self.speed
        elif dist > STATS['keep_distance'] + STATS['distance_tolerance']:
            self.vx = self.face_dir * self.speed

    def is_fading(self):
        # 기습 Windup 중 아직 순간이동하지 않은 구간
        return (self.state == WINDUP and self.attack.name == 'ambush'
                and self.state_timer > STATS['appear_windup'])

    def update_ai(self):
        super().update_ai()
        # 흐려짐이 끝나는 순간 플레이어 뒤로 순간이동한다
        if self.vanishing and self.state == WINDUP and not self.is_fading():
            self.vanishing = False
            self.teleport_behind_player()

    def teleport_behind_player(self):
        # 등 뒤가 벽·화면 밖이라 밀려나면 앞쪽(플레이어가 바라보는 쪽)에 나타난다
        offset = STATS['offset']
        if self.player.on_ground:
            self.y = self.player.y
        for side in (-self.player.face_dir, self.player.face_dir):
            want = self.player.x + side * offset
            x = fit_x(self, want)
            if abs(x - want) < 1:
                break
        self.x = x
        self.vy = 0
        self.face_player()
        effect.burst(self.x, self.y + self.h / 2, config.TELEPORT_PUFF, self.color)

    def draw_body(self):
        if not self.is_fading():
            super().draw_body()
            return
        # 흐려지는 중: 몸이 점점 투명해진다
        start, end = STATS['fade_alpha']
        progress = (self.state_timer - STATS['appear_windup']) / STATS['fade_time']
        effect.draw_alpha_rect(*self.get_bb(), self.color, end + (start - end) * progress)
