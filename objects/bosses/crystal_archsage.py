import math

from pico2d import *

import config
import game_framework
from objects import effect, magic_circle, projectile
from objects.bosses.boss_base import BossBase
from objects.enemies.crystal_sage import blink_away, fit_x
from objects.enemies.crystal_sprite import CrystalSprite
from objects.enemy_base import ACTIVE, TELEGRAPH, WINDUP, Attack
from systems import camera

STATS = config.BOSS_MAGE


class CrystalArchsage(BossBase):
    # B3 수정 대술사 (← v2 대마법사, 1페이즈). 거리를 벌리고 투사체로 압박한다. 반사가 가장 큰 딜 수단
    # 2페이즈·B3 수치(BOSS_ARCHSAGE)는 T52
    # 마력탄 연사(흰색) · 대형 마력구(흰색, 반사하면 큰 피해) · 마법진 폭격(빨간색) · 견습 소환(흰색 번쩍임)
    # 플레이어가 blink_trigger_dist 안이면 반대쪽으로 순간이동 (공격 아님, 예고 없음)
    # 근접 공격이 없으므로 자세는 반사탄(+POSTURE_REFLECT)과 곡괭이 적중으로 쌓인다
    boss_key = 'archsage'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        v, o, c, s = STATS['volley'], STATS['orb'], STATS['barrage'], STATS['summon']
        # 연사·폭격은 Active 동안 interval마다 한 번씩 시전한다
        self.patterns = dict(
            volley=Attack('volley', True, v['telegraph'], v['windup'],
                          STATS['volley_count'] * STATS['volley_interval'], v['recover'], STATS['damage'], None),
            orb=Attack('orb', True, o['telegraph'], o['windup'], o['active'], o['recover'],
                       STATS['orb_damage'], None),
            barrage=Attack('barrage', False, c['telegraph'], c['windup'],
                           STATS['circle_count'] * STATS['circle_interval'], c['recover'],
                           STATS['circle_damage'], None),
            summon=Attack('summon', True, s['telegraph'], s['windup'], s['active'], s['recover'], 0, None))
        self.casts_left = 0    # 이번 Active에 남은 시전 횟수 (연사·폭격)
        self.cast_timer = 0.0  # 다음 시전까지 남은 시간
        self.cast_interval = 0.0
        self.blink_cooldown = 0.0

    def update(self):
        self.blink_cooldown = max(0, self.blink_cooldown - game_framework.frame_time)
        super().update()

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        dist = abs(self.player.x - self.x)
        if self.blink_cooldown <= 0 and dist <= STATS['blink_trigger_dist']:
            blink_away(self, STATS['blink_dist'])
            self.blink_cooldown = STATS['blink_cooldown']
            dist = abs(self.player.x - self.x)
        self.face_player()
        if self.attack_cooldown <= 0:
            name = self.pick_pattern(self.pattern_weights(dist))
            if name:
                cooldown = STATS['summon_cooldown'] if name == 'summon' else 0
                self.remember_pattern(name, cooldown)
                self.attack_queue = [self.patterns[name]]
                self.start_next_attack()
                return
        # 견습 마법사처럼 keep_distance를 유지한다 (가까우면 바라본 채 뒷걸음질)
        if dist < STATS['keep_distance'] - STATS['distance_tolerance']:
            self.vx = -self.face_dir * self.speed
        elif dist > STATS['keep_distance'] + STATS['distance_tolerance']:
            self.vx = self.face_dir * self.speed

    def pattern_weights(self, dist):
        weights = dict(STATS['near'] if dist <= STATS['near_range'] else STATS['far'])
        if len(self.alive_summons()) >= STATS['summon_max']:
            weights['summon'] = 0
        return weights

    def next_phase(self):
        super().next_phase()
        if self.state != ACTIVE:
            return
        name = self.attack.name
        if name == 'volley':
            self.start_casts(STATS['volley_count'], STATS['volley_interval'])
        elif name == 'barrage':
            self.start_casts(STATS['circle_count'], STATS['circle_interval'])
        elif name == 'orb':
            self.fire(STATS['orb_speed'], config.MAGE_ORB)
        elif name == 'summon':
            self.summon()

    def start_casts(self, count, interval):
        # 첫 시전은 Active 시작 직후, 이후 interval마다
        self.casts_left = count
        self.cast_timer = 0.0
        self.cast_interval = interval

    def update_ai(self):
        # 시전은 Active가 끝나는 프레임보다 먼저 처리해서 마지막 1회가 빠지지 않게 한다
        if self.state == ACTIVE and self.casts_left > 0:
            self.cast_timer -= game_framework.frame_time
            if self.cast_timer <= 0:
                self.casts_left -= 1
                self.cast_timer += self.cast_interval
                if self.attack.name == 'volley':
                    self.fire(STATS['bolt_speed'], config.BOSS_BOLT)
                else:
                    magic_circle.cast(self.player.x, self.player.y, STATS['circle_radius'], STATS['circle_delay'],
                                      self.attack_damage(), self.player, self.platforms)
        super().update_ai()

    def cancel_attack(self):
        super().cancel_attack()
        self.casts_left = 0

    def orb_pos(self):
        # 지팡이 끝 구슬 (투사체가 나가는 자리)
        return self.x + self.face_dir * self.w * 3 / 4, self.y + self.h * 3 / 4

    def fire(self, speed, spec):
        # 쏘는 순간 플레이어 몸 중심을 조준한다
        x, y = self.orb_pos()
        angle = math.atan2(self.player.y + config.PLAYER_H / 2 - y, self.player.x - x)
        projectile.fire(x, y, math.cos(angle), math.sin(angle), speed, self.attack_damage(),
                        self.attack.parryable, self.platforms, spec, owner=self)

    def summon(self):
        # 비어 있는 자리만큼 보스 양옆에 견습 마법사를 불러낸다
        count = STATS['summon_max'] - len(self.alive_summons())
        for i in range(count):
            side = 1 if i % 2 == 0 else -1
            x = fit_x(self, self.x + side * STATS['summon_offset'])
            mage = CrystalSprite(x, self.y, self.player, self.platforms)
            self.summons.append(mage)
            self.new_summons.append(mage)
            effect.burst(x, self.y + mage.h / 2, config.TELEPORT_PUFF, mage.color)

    def draw_weapon(self, l, b, r, t):
        # 긴 지팡이 + 끝의 구슬. 예고·시전 준비 중엔 구슬이 빛나고, 대형 마력구는 구체 크기까지 부풀어 오른다
        ox, oy = self.orb_pos()
        thick = self.w / 8
        camera.draw_rect(ox - thick / 2, b, ox + thick / 2, oy, *config.COLOR_STAFF, filled=True)
        if self.state in (TELEGRAPH, WINDUP) and self.attack.name == 'orb':
            a = self.attack
            left = self.state_timer + (a.windup if self.state == TELEGRAPH else 0)
            k = min(1, max(0, 1 - left / (a.telegraph + a.windup)))
            radius = thick + (config.MAGE_ORB['size'] / 2 - thick) * k
            effect.draw_disc(ox, oy, radius, config.MAGE_ORB['color'])
        elif self.state in (TELEGRAPH, WINDUP):
            effect.draw_disc(ox, oy, config.BOSS_BOLT['size'] / 2, config.COLOR_ENEMY_WINDUP)
        else:
            effect.draw_disc(ox, oy, thick, config.COLOR_BOSS_STAFF_ORB)
