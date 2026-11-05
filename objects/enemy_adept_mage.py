import math
import random

from pico2d import *

import config
import game_framework
import game_world
from objects import effect, magic_circle
from objects.enemy_apprentice_mage import EnemyApprenticeMage
from objects.enemy_base import Attack
from systems import terrain

STATS = config.ADEPT_MAGE


class EnemyAdeptMage(EnemyApprenticeMage):
    # 숙련 마법사: ① 마력탄 bolt_count발 부채꼴 (흰색, 각각 반사 가능)
    # ② circle_chance 확률로 플레이어 발밑 마법진 (빨간색, 패링 불가, 대시·이동으로 회피)
    # 플레이어가 blink_trigger_dist 안으로 들어오면 blink_dist만큼 순간 후퇴 (공격이 아니라 예고 없음)
    stats = STATS

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, player, platforms)
        self.circle = Attack('circle', False, STATS['circle_telegraph'], STATS['circle_windup'],
                             STATS['active'], STATS['circle_recover'], STATS['circle_damage'], None)
        self.blink_cooldown = 0.0

    def choose_attacks(self):
        if random.random() < STATS['circle_chance']:
            return [self.circle]
        return [self.bolt]

    def start_next_attack(self):
        super().start_next_attack()
        if self.attack.name == 'circle':
            # 시전자가 빨갛게 번쩍이는 동안 마법진 자리에도 빨간 테두리 예고가 뜬다
            magic_circle.cast(self.player.x, self.player.y, STATS['circle_radius'], STATS['circle_delay'],
                              self.attack_damage(), self.player, self.platforms)

    def cast_bolts(self):
        # 가운데 탄은 플레이어를 조준하고, 나머지는 bolt_spread도 간격으로 부채꼴
        center = self.aim(*self.orb_pos())
        count = STATS['bolt_count']
        for i in range(count):
            self.fire_bolt(center + math.radians(STATS['bolt_spread'] * (i - (count - 1) / 2)))

    def update(self):
        self.blink_cooldown = max(0, self.blink_cooldown - game_framework.frame_time)
        super().update()

    def chase(self):
        if (not self.player.dead and self.blink_cooldown <= 0
                and abs(self.player.x - self.x) <= STATS['blink_trigger_dist']):
            self.blink()
        super().chase()

    def blink(self):
        blink_away(self, STATS['blink_dist'])
        self.blink_cooldown = STATS['blink_cooldown']


def blink_away(enemy, dist):
    # 플레이어 반대쪽으로 dist만큼 순간 후퇴. 벽·화면 밖에 막혀 거리가 모자라면 플레이어 너머 쪽으로 간다
    # 둘 다 막히면 플레이어에게서 더 먼 쪽. 높이는 그대로 두고 중력으로 바닥에 내려선다
    # [v2] 대마법사도 같은 규칙으로 순간이동한다
    away = 1 if enemy.x >= enemy.player.x else -1
    spots = []
    for side in (away, -away):
        want = enemy.x + side * dist
        x = fit_x(enemy, want)
        if abs(x - want) < 1:
            break
        spots.append(x)
    else:
        x = max(spots, key=lambda s: abs(s - enemy.player.x))
    effect.burst(enemy.x, enemy.y + enemy.h / 2, config.TELEPORT_PUFF, enemy.color)
    enemy.x = x
    enemy.vy = 0
    enemy.face_player()
    effect.burst(enemy.x, enemy.y + enemy.h / 2, config.TELEPORT_PUFF, enemy.color)


def fit_x(enemy, x):
    # 벽 안·화면 밖이 아닌 가장 가까운 x
    half_w = enemy.w / 2
    x = terrain.resolve_x(x, enemy.y, enemy.w, enemy.h, enemy.platforms)
    return clamp(half_w, x, game_world.room_w - half_w)
