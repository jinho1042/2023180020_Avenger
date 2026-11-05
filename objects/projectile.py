from pico2d import *

import config
import game_framework
import game_world
from objects import effect
from systems import camera, combat, sound

GROUP_PLAYER = 'player:projectile'
GROUP_ENEMY = 'enemy:projectile'


class Projectile:
    # 직선으로 날아가는 투사체. x, y는 중심 좌표, (dir_x, dir_y)는 단위 방향 벡터
    # solid 지형이나 화면 밖에 닿으면 사라진다 (oneway 발판은 통과)
    # 패링당하면: 반사 해금 전에는 튕겨 사라지고(on_blocked), 해금 후에는 반사되어 플레이어 소유가 된다(on_parried)
    # damage는 플레이어에게 주는 피해. 반사되면 REFLECT_DAMAGE × reflect_mult × 각인 배율(적 체력 단위)로 새로 정한다
    def __init__(self, x, y, dir_x, dir_y, speed, damage, parryable, platforms, spec, owner=None):
        self.x, self.y = x, y
        self.owner = owner  # 쏜 적·함정 (패링 숨 판정 등에 쓴다, 9.3). 반사되면 플레이어
        self.dir_x, self.dir_y = dir_x, dir_y
        self.speed = speed
        self.damage = damage
        self.parryable = parryable
        self.platforms = platforms
        self.size = spec['size']
        self.length = spec['length']
        self.color = spec['color']
        self.reflect_mult = spec.get('reflect_mult', 1)  # 반사 피해 배율 (기본 1)
        self.round = spec.get('round', False)  # [v2] 마력탄은 원형으로 그린다
        self.alive = True
        self.reflected = False

    def destroy(self):
        if self.alive:
            self.alive = False
            game_world.remove_object(self)

    def on_blocked(self):
        # 반사 해금 전 패링: 그 자리에서 튕겨 사라진다 (피해·자세 없음)
        effect.projectile_blocked(self.x, self.y, self.color)
        self.destroy()

    def on_parried(self, player, damage_mult):
        # 반사: 방향 반전 + 소유자를 플레이어로. 각인 배율은 바뀔 수 있어 반사 시점에 곱한다
        self.reflected = True
        self.owner = player
        self.dir_x, self.dir_y = -self.dir_x, -self.dir_y
        self.damage = config.REFLECT_DAMAGE * self.reflect_mult * damage_mult
        self.color = config.COLOR_REFLECTED

    def update(self):
        if not self.alive:
            return
        dt = game_framework.frame_time
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        half = self.size / 2
        if (self.x + half < 0 or self.x - half > game_world.room_w
                or self.y + half < 0 or self.y - half > game_world.room_h):
            self.destroy()
            return
        bb = self.get_bb()
        for p in self.platforms:
            if p.kind == 'solid' and game_world.overlap(bb, p.get_bb()):
                self.destroy()
                return

    def draw(self):
        if self.round:
            effect.draw_disc(self.x, self.y, self.size / 2, self.color)
        else:
            self.draw_arrow()
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *config.COLOR_DEBUG_ATTACK)

    def draw_arrow(self):
        # 진행 방향으로 늘어선 작은 사각형으로 화살 몸통을 그리고, 앞쪽 끝에 촉을 그린다
        dot = self.size / 4
        steps = int(self.length / dot)
        for i in range(steps):
            d = i * dot - self.length / 2
            cx, cy = self.x + self.dir_x * d, self.y + self.dir_y * d
            camera.draw_rect(cx - dot / 2, cy - dot / 2, cx + dot / 2, cy + dot / 2, *self.color, filled=True)
        hx = self.x + self.dir_x * self.length / 2
        hy = self.y + self.dir_y * self.length / 2
        camera.draw_rect(hx - dot, hy - dot, hx + dot, hy + dot, *self.color, filled=True)

    def get_bb(self):
        half = self.size / 2
        return self.x - half, self.y - half, self.x + half, self.y + half

    def handle_collision(self, group, other):
        if not self.alive:
            return
        if group == GROUP_PLAYER and not self.reflected:
            combat.projectile_hit(other, self)
        elif group == GROUP_ENEMY and self.reflected and other.is_alive():
            other.take_damage(self.damage)
            # 반사탄이 보스에 맞으면 자세가 쌓인다 (9.3. 정예는 T48)
            if other.is_boss and other.is_alive():
                other.add_posture()
            if other.is_alive():
                effect.enemy_hurt(self.x, self.y, self.dir_x)
            self.destroy()


def fire(x, y, dir_x, dir_y, speed, damage, parryable, platforms, spec, owner=None):
    p = Projectile(x, y, dir_x, dir_y, speed, damage, parryable, platforms, spec, owner)
    sound.play('shoot')
    game_world.add_object(p, config.DEPTH_ENEMY)
    # 반사 후 그룹을 옮기면 충돌 순회 중 목록이 바뀌므로 처음부터 양쪽에 등록하고 reflected로 거른다
    game_world.add_collision_pair(GROUP_PLAYER, None, p)
    game_world.add_collision_pair(GROUP_ENEMY, None, p)
    return p
