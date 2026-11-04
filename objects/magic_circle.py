from pico2d import *

import config
import game_framework
import game_world
from objects import effect
from systems import terrain

SPEC = config.MAGIC_CIRCLE


class MagicCircle:
    # 바닥 마법진 (패링 불가): 빨간 테두리로 예고하다가 delay 뒤 빛 기둥이 솟는다
    # 기둥이 있는 active 동안 플레이어가 안에 있으면 한 번 피해. 패링 중이어도 맞고, 대시 무적이면 피한다
    # x, y는 바닥 위 중심 좌표
    def __init__(self, x, y, radius, delay, damage, player):
        self.x, self.y = x, y
        self.radius = radius
        self.delay = delay
        self.damage = damage
        self.player = player
        self.timer = delay
        self.active_timer = SPEC['active']
        self.hit = False

    def is_exploding(self):
        return self.timer <= 0

    def update(self):
        dt = game_framework.frame_time
        if not self.is_exploding():
            self.timer -= dt
            return
        if not self.hit and game_world.collide(self, self.player):
            # 무적이라 피해가 없었으면 기둥이 남아 있는 동안 다시 검사한다
            self.hit = self.player.take_hit(self.damage, self.x)
            if self.hit:
                effect.player_hit(self.player.x, self.player.y + config.PLAYER_H / 2)
        self.active_timer -= dt
        if self.active_timer <= 0:
            game_world.remove_object(self)

    def draw(self):
        if self.is_exploding():
            l, b, r, t = self.get_bb()
            effect.draw_alpha_rect(l, b, r, t, SPEC['pillar_color'],
                                   SPEC['pillar_alpha'] * max(0, self.active_timer) / SPEC['active'])
        else:
            # 예고: 기둥이 솟을 자리를 옅게 칠하고, 터질 때가 가까울수록 진해진다
            k = 1 - self.timer / self.delay
            l, b, r, t = self.get_bb()
            effect.draw_alpha_rect(l, b, r, t, config.COLOR_UNPARRYABLE, SPEC['warn_alpha'] * k)
        effect.draw_ring(self.x, self.y, self.radius, self.radius * SPEC['ring_flat'],
                         SPEC['ring_dots'], SPEC['dot'], config.COLOR_UNPARRYABLE)
        if game_world.show_hitbox:
            draw_rectangle(*self.get_bb(), *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        return self.x - self.radius, self.y, self.x + self.radius, self.y + SPEC['pillar_h']

    def handle_collision(self, group, other):
        pass


def floor_below(x, y, platforms):
    # (x, y)에서 아래로 내려가 처음 닿는 지형 윗면 (공중에 있는 플레이어의 발밑). 없으면 y 그대로
    tops = [p.top for p in platforms if terrain.overlaps_x(x, 1, p) and p.top <= y]
    return max(tops) if tops else y


def cast(x, y, radius, delay, damage, player, platforms):
    c = MagicCircle(x, floor_below(x, y, platforms), radius, delay, damage, player)
    game_world.add_object(c, config.DEPTH_MAP)
    return c
