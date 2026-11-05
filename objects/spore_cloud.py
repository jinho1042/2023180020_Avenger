import math

import config
import game_framework
import game_world
from objects import effect
from objects.breath_zone import BreathZone
from systems import breath, camera

SPEC = config.SPORE_CLOUD


class SporeCloud(BreathZone):
    # 포자 구름 (10.3): 포자 버섯이 부풀어 터뜨리거나 죽을 때 남기는 지속 장판 (패링 불가)
    # 닿으면 한 번 피해, 몸 중심이 안에 있는 동안 숨 소모 spore 배율 (breath.clouds, 7.2 순서 2)
    # x, y는 바닥 위 중심. 판정은 가로 반지름 radius, 높이 radius × hit_h인 사각형
    def __init__(self, x, y, radius, life, damage, player):
        super().__init__(x - radius, y, radius * 2, radius * SPEC['hit_h'], 'spore')
        self.cx = x
        self.radius = radius
        self.life = life
        self.timer = life
        self.damage = damage
        self.player = player
        self.hit = False
        self.time = 0.0

    def update(self):
        dt = game_framework.frame_time
        self.time += dt
        self.timer -= dt
        if self.timer <= 0:
            remove(self)
            return
        if not self.hit and not self.player.dead and game_world.collide(self, self.player):
            # 무적이라 피해가 없었으면 구름이 남아 있는 동안 다시 검사한다
            self.hit = self.player.take_hit(self.damage, self.cx)
            if self.hit:
                effect.player_hit(self.player.x, self.player.y + config.PLAYER_H / 2)

    def draw(self):
        if not camera.visible(self.get_bb()):
            return
        # 사라질 때 fade초 동안 옅어진다
        k = min(1.0, self.timer / SPEC['fade'])
        l, b, r, t = self.get_bb()
        effect.draw_alpha_rect(l, b, r, t, config.COLOR_SPORE_CLOUD, SPEC['alpha'] * k)
        # 떠다니는 포자 점
        half = SPEC['dot'] / 2
        for i in range(SPEC['dots']):
            angle = i * 2.399 + self.time   # 황금각으로 흩뿌림
            fx = (i + 0.5) / SPEC['dots']
            x = self.cx + math.cos(angle) * self.radius * math.sqrt(fx)
            y = b + (t - b) * ((fx + self.time * SPEC['drift'] / (t - b)) % 1)
            camera.draw_rect(x - half, y - half, x + half, y + half, *config.COLOR_SPORE_CLOUD, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_ATTACK)


def spawn(x, y, radius, life, damage, player):
    cloud = SporeCloud(x, y, radius, life, damage, player)
    game_world.add_object(cloud, config.DEPTH_ENEMY)
    breath.clouds.append(cloud)
    return cloud


def remove(cloud):
    game_world.remove_object(cloud)
    if cloud in breath.clouds:
        breath.clouds.remove(cloud)
