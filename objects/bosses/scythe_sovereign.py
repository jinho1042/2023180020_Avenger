import random

from pico2d import *

import config
import game_world
from objects import effect, projectile
from objects.bosses.boss_base import BossBase, boss_damage
from objects.enemy_base import ACTIVE, RECOVER, TELEGRAPH, WINDUP, Attack
from systems import camera, terrain

STATS = config.BOSS_TWINBLADE


class ScytheSovereign(BossBase):
    # B5 쌍낫 군주 (← v2 쌍검 기사). 아직 v2 패턴 그대로: 4연속 베기(흰색) · 순간이동 기습(빨간색) · 검기 발사(흰색, 반사 가능)
    # 체력이 phase_hp 이하가 되면 2페이즈 (boss_base 페이즈 전환 → on_phase): 더 빠르고, 페이크를 섞고, 빨간 예고가 잦아진다
    # 소용돌이·페이크 규칙(원칙 14)·B5 수치(BOSS_SCYTHE)는 T56
    boss_key = 'scythe'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.phase2 = False
        self.feint = False  # 이번 패턴이 예고만 하는 페이크인지
        self.build_patterns(1)

    def build_patterns(self, speed_mult):
        # 패턴 이름 → 이어서 쓸 Attack 목록. 시간은 모두 speed_mult로 나눈다
        def timed(name, parryable, telegraph, recover, spec, hitbox):
            return Attack(name, parryable, telegraph / speed_mult, spec['windup'] / speed_mult,
                          spec['active'] / speed_mult, recover / speed_mult, boss_damage(STATS, parryable), hitbox)

        c = STATS['combo']
        combo = []
        for i in range(c['count']):
            telegraph = c['telegraph'] if i == 0 else c['next_telegraph']
            recover = c['last_recover'] if i == c['count'] - 1 else c['recover']
            combo.append(timed('combo', True, telegraph, recover, c, c['hitbox']))
        tp, wv = STATS['teleport'], STATS['wave']
        self.patterns = dict(
            combo=combo,
            teleport=[timed('teleport', False, tp['telegraph'], tp['recover'], tp, tp['hitbox'])],
            wave=[timed('wave', True, wv['telegraph'], wv['recover'], wv, None)])

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        dist = abs(self.player.x - self.x)
        if self.attack_cooldown <= 0:
            key = 'near' if dist <= STATS['near_range'] else 'far'
            name = self.pick_pattern(STATS['phase2_' + key] if self.phase2 else STATS[key])
            if name:
                self.remember_pattern(name)
                self.feint = self.phase2 and random.random() < STATS['feint_chance']
                self.attack_queue = list(self.patterns[name])
                self.start_next_attack()
                return
        if dist > STATS['near_range'] / 2:
            self.vx = self.face_dir * self.speed

    def next_phase(self):
        if self.state == TELEGRAPH and self.feint:
            # 페이크: 예고만 하고 공격하지 않은 채 잠깐 멈춘다
            self.feint = False
            self.attack_queue = []
            self.set_state(RECOVER, STATS['feint_recover'])
            return
        super().next_phase()
        if self.state == WINDUP and self.attack.name == 'teleport':
            self.teleport_behind_player()
        elif self.state == ACTIVE and self.attack.name == 'wave':
            self.fire_wave()

    def teleport_behind_player(self):
        effect.burst(self.x, self.y + self.h / 2, config.TELEPORT_PUFF, self.color)
        # 등 뒤가 벽·화면 밖이라 밀려나면 앞쪽으로 나타난다
        offset = STATS['teleport']['offset']
        for side in (-self.player.face_dir, self.player.face_dir):
            want = self.player.x + side * offset
            x = self.fit_x(want, self.player.y)
            if abs(x - want) < 1:
                break
        self.x = x
        # 플레이어가 공중이면 지금 높이 그대로 두고 떨어지게 한다
        if self.player.on_ground:
            self.y = self.player.y
        self.vy = 0
        self.face_player()
        effect.burst(self.x, self.y + self.h / 2, config.TELEPORT_PUFF, self.color)

    def fit_x(self, x, y):
        half_w = self.w / 2
        x = terrain.resolve_x(x, y, self.w, self.h, self.platforms)
        return clamp(half_w, x, game_world.room_w - half_w)

    def fire_wave(self):
        # 플레이어 몸 높이에 맞춰 수평으로 쏜다
        x = self.x + self.face_dir * self.w / 2
        y = self.y + config.PLAYER_H / 2
        projectile.fire(x, y, self.face_dir, 0, STATS['wave']['speed'], self.attack_damage(),
                        self.attack.parryable, self.platforms, config.TWIN_WAVE, owner=self)

    def recoil(self):
        # 4연속 베기 도중엔 멈추지 않고 다음 타로 이어간다 (자세만 쌓인다)
        if self.attack_queue:
            return
        super().recoil()

    def on_phase(self, phase):
        # 2페이즈: 색이 바뀌고 모든 동작이 빨라진다 (포효·무적·투사체 제거는 boss_base)
        self.phase2 = True
        mult = STATS['phase2_speed_mult']
        self.speed *= mult
        self.color = STATS['color_phase2']
        self.build_patterns(mult)

    def draw_weapon(self, l, b, r, t):
        # 양손에 짧은 검: 평소엔 몸 양옆에 비스듬히 내려 들고, 모션 중엔 둘 다 앞으로 치켜든다
        blade = self.w / 7
        length = self.h / 2
        if self.state == WINDUP:
            wx = self.x - self.face_dir * self.w / 2
            for dx in (0, self.face_dir * blade * 2):
                camera.draw_rect(wx + dx - blade / 2, t - blade, wx + dx + blade / 2, t + length - blade,
                               *config.COLOR_TWINBLADE, filled=True)
        else:
            cy = b + self.h / 3
            for side in (l, r):
                camera.draw_rect(side - blade / 2, cy - length / 2, side + blade / 2, cy + length / 2,
                               *config.COLOR_TWINBLADE, filled=True)
