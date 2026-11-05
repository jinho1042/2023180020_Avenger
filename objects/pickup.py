import math
import random

import config
import game_framework
import game_world
from objects import effect
from systems import camera, economy, engravings, sound, terrain


class OrePiece:
    # 바닥 광석 조각 (13.2): 위로 튀어 떨어진 뒤, 흡수 범위 안에 플레이어가 오면 몸으로 빨려 들어가 소지 광석이 된다
    # 방을 나가면 game_world.clear()로 사라진다 (주운 적 없는 조각은 잃는다)
    def __init__(self, x, y, value, player):
        spec = config.ORE_PIECE
        angle = math.pi / 2 + random.uniform(-spec['spread'], spec['spread'])
        speed = random.uniform(*spec['speed'])
        self.x, self.y = x, y   # 아래 가운데
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.value = value
        self.size = spec['size'] + spec['size_per_value'] * value
        self.player = player
        self.delay = spec['delay']
        self.absorbing = False
        self.on_ground = False

    def pickup_radius(self):
        if engravings.is_set('ore_magnet'):
            return config.ORE_MAGNET_RADIUS
        return config.ORE_PICKUP_RADIUS

    def update(self):
        dt = game_framework.frame_time
        self.delay = max(0, self.delay - dt)
        if self.absorbing:
            self.update_absorb(dt)
            return
        self.fall(dt)
        p = self.player
        if self.delay <= 0 and not (p.dead or p.blackout):
            px, py = p.x, p.y + config.PLAYER_H / 2
            if math.hypot(px - self.x, py - (self.y + self.size / 2)) <= self.pickup_radius() + config.PLAYER_W / 2:
                self.absorbing = True

    def fall(self, dt):
        # 중력을 받고 지형에 내려앉는다. 바닥에서는 미끄러지다 멈춘다
        self.vy += config.GRAVITY * dt
        if self.on_ground:
            slow = config.ORE_PIECE['friction'] * dt
            self.vx = 0 if abs(self.vx) <= slow else self.vx - math.copysign(slow, self.vx)
        platforms = self.player.platforms
        self.x += self.vx * dt
        resolved = terrain.resolve_x(self.x, self.y, self.size, self.size, platforms)
        if resolved != self.x:
            self.vx = 0
        half = self.size / 2
        self.x = min(max(resolved, half), game_world.room_w - half)
        prev_y = self.y
        self.y += self.vy * dt
        self.y, self.vy, self.on_ground = terrain.resolve_y(self.x, prev_y, self.y, self.vy,
                                                            self.size, self.size, platforms)

    def update_absorb(self, dt):
        # 몸 중심으로 곧장 날아간다. 닿으면 소지 광석에 더한다
        p = self.player
        tx, ty = p.x, p.y + config.PLAYER_H / 2
        dx, dy = tx - self.x, ty - (self.y + self.size / 2)
        dist = math.hypot(dx, dy)
        step = config.ORE_PIECE['absorb_speed'] * dt
        if dist <= step or p.dead:
            if not p.dead:
                economy.add(self.value)
                effect.burst(tx, ty, config.ORE_COLLECT_SPARK, config.COLOR_ORE)
                sound.play('ore')
            game_world.remove_object(self)
            self.absorbing = False
            self.value = 0
            return
        self.x += dx / dist * step
        self.y += dy / dist * step

    def draw(self):
        if self.value <= 0:
            return
        l, b, r, t = self.get_bb()
        # 어두운 테두리 + 밝은 가운데 (광석 덩어리와 같은 색)
        camera.draw_rect(l, b, r, t, *config.COLOR_ORE_CHUNK, filled=True)
        inset = self.size / 4
        camera.draw_rect(l + inset, b + inset, r - inset, t - inset, *config.COLOR_ORE, filled=True)

    def get_bb(self):
        half = self.size / 2
        return self.x - half, self.y, self.x + half, self.y + self.size


def spill(x, y, amount, player):
    # (x, y)에서 amount만큼을 1~max_value짜리 조각으로 나눠 위로 튀게 뿌린다 (10.1)
    pieces = []
    while amount > 0:
        value = random.randint(1, min(amount, config.ORE_PIECE['max_value']))
        pieces.append(OrePiece(x, y, value, player))
        amount -= value
    game_world.add_objects(pieces, config.DEPTH_ENEMY)
