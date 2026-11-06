from pico2d import *

import config
import game_framework
import game_world
from objects import effect
from systems import camera, combat, sound

GROUP_PLAYER = 'player:projectile'
GROUP_ENEMY = 'enemy:projectile'
GROUP_SWITCH = 'switch:projectile'   # 수정 스위치 (objects/switch.py)


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
        self.posture = config.POSTURE_REFLECT   # 플레이어 소유일 때 보스·정예에 맞으면 쌓는 자세 (9.3)

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
            # 수정 스위치는 지형이지만 투사체를 통과시킨다 (반사탄은 handle_collision에서 받는다)
            if p.kind == 'solid' and not getattr(p, 'passes_projectiles', False) and game_world.overlap(bb, p.get_bb()):
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
        elif group == GROUP_SWITCH:
            if self.reflected and other.on_reflected_hit(self):
                self.destroy()
        elif group == GROUP_ENEMY and self.reflected and other.is_alive():
            part, _ = combat.struck_part(self.get_bb(), other)
            if part is None:
                return   # 부위 사이 빈 곳 (거상의 머리·주먹 사이 등)은 지나간다
            if other.invulnerable() or part == 'armor':
                effect.statue_spark(self.x, self.y)
                self.destroy()
                return
            other.take_damage(self.damage)
            # 반사탄이 보스·정예(is_boss)에 맞으면 자세가 쌓인다 (9.3. 결정 화살은 POSTURE_PER_SKILL)
            if other.is_boss and other.is_alive():
                other.add_posture(self.posture)
            if other.is_alive():
                effect.enemy_hurt(self.x, self.y, self.dir_x)
            self.destroy()


class CrystalArrow(Projectile):
    # 결정 화살 (결정 Lv2, 8.2): 플레이어가 쏘는 수평 화살. 처음부터 플레이어 소유(reflected)라
    # 적·보스에 SKILLS.crystal_arrow.damage(적 체력 단위), 보스·정예 자세 +POSTURE_PER_SKILL, 수정 스위치도 켠다 (18장 110번)
    def __init__(self, x, y, direction, player, platforms):
        spec = config.SKILLS['crystal_arrow']
        super().__init__(x, y, direction, 0, spec['speed'], spec['damage'], False, platforms,
                         dict(size=spec['size'][1], length=spec['size'][0], color=config.COLOR_CRYSTAL_ARROW),
                         owner=player)
        self.reflected = True
        self.posture = config.POSTURE_PER_SKILL
        self.w, self.h = spec['size']

    def draw(self):
        # 길쭉한 결정 몸통 + 앞쪽 끝 촉
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b + self.h / 4, r, t - self.h / 4, *self.color, filled=True)
        tip = r if self.dir_x > 0 else l
        camera.draw_rect(tip - self.h / 2, b, tip + self.h / 2, t, *self.color, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        return self.x - self.w / 2, self.y - self.h / 2, self.x + self.w / 2, self.y + self.h / 2


def fire_arrow(x, y, direction, player, platforms):
    a = CrystalArrow(x, y, direction, player, platforms)
    sound.play('shoot')
    game_world.add_object(a, config.DEPTH_ENEMY)
    game_world.add_collision_pair(GROUP_ENEMY, None, a)
    game_world.add_collision_pair(GROUP_SWITCH, None, a)
    return a


def fire(x, y, dir_x, dir_y, speed, damage, parryable, platforms, spec, owner=None):
    p = Projectile(x, y, dir_x, dir_y, speed, damage, parryable, platforms, spec, owner)
    sound.play('shoot')
    game_world.add_object(p, config.DEPTH_ENEMY)
    # 반사 후 그룹을 옮기면 충돌 순회 중 목록이 바뀌므로 처음부터 양쪽에 등록하고 reflected로 거른다
    game_world.add_collision_pair(GROUP_PLAYER, None, p)
    game_world.add_collision_pair(GROUP_ENEMY, None, p)
    game_world.add_collision_pair(GROUP_SWITCH, None, p)
    return p
