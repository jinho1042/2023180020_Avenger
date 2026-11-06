import random

import config
import game_framework
import game_world
from objects import effect, magic_circle
from objects.enemy_base import ACTIVE, FLINCH, TELEGRAPH, WINDUP, Attack, EnemyBase
from systems import camera, sound, terrain

STATS = config.RUIN_GOLEM


class GroundWave(magic_circle.MagicCircle):
    # 바닥 충격파 (빨강, 패링 불가, 10.3): 내려친 자리에서 direction 쪽으로 speed px/s로 바닥을 따라 간다
    # 낮아서 점프로 넘는다. 벽·방 가장자리·발판 끝에 닿으면 흙먼지와 함께 사라진다. 닿으면 한 번 피해
    # 마법진을 이어받아 정예 처치 때 함께 지워진다 (boss_base.clear_hostile_projectiles). spec: w, h, speed, dust
    def __init__(self, x, y, direction, damage, player, platforms, spec):
        super().__init__(x, y, spec['wave_w'] / 2, 0, damage, player)
        self.dir = direction
        self.platforms = platforms
        self.spec = spec

    def update(self):
        dt = game_framework.frame_time
        spec = self.spec
        self.x += self.dir * spec['shockwave_speed'] * dt
        half = self.radius
        front = self.x + self.dir * half
        if (self.x - half <= 0 or self.x + half >= game_world.room_w
                or terrain.body_blocked(self.x, self.y + 1, spec['wave_w'], spec['wave_h'] - 1, self.platforms)
                or not terrain.resolve_y(front, self.y, self.y - 4, -1, 2, spec['wave_h'], self.platforms)[2]):
            effect.burst(self.x, self.y, spec['dust'], config.COLOR_ROCK)
            game_world.remove_object(self)
            return
        if not self.hit and game_world.collide(self, self.player):
            self.hit = self.player.take_hit(self.damage, self.x)
            if self.hit:
                effect.player_hit(self.player.x, self.player.y + config.PLAYER_H / 2)

    def draw(self):
        l, b, r, t = self.get_bb()
        # 진행 방향으로 기울어진 물결: 뒤쪽은 낮고 앞쪽이 높다
        steps = 4
        w = (r - l) / steps
        for i in range(steps):
            k = (i + 1) / steps if self.dir > 0 else (steps - i) / steps
            camera.draw_rect(l + w * i, b, l + w * (i + 1), b + (t - b) * k, *config.COLOR_SHOCKWAVE, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        return self.x - self.radius, self.y, self.x + self.radius, self.y + self.spec['wave_h']


def release_waves(enemy, spec, damage):
    # 몸 양옆 바닥에서 충격파 두 줄 (유적 골렘·정예 신전 골렘)
    for d in (-1, 1):
        x = enemy.x + d * (enemy.w / 2 + spec['wave_w'] / 2)
        game_world.add_object(GroundWave(x, enemy.y, d, damage, enemy.player, enemy.platforms, spec),
                              config.DEPTH_MAP)
    effect.burst(enemy.x, enemy.y, spec['dust'], config.COLOR_ROCK)
    camera.shake(*spec['shake'])
    sound.play('door')


def draw_golem(enemy, l, b, r, t, wave_raised):
    # 돌 골렘 그림 (14.5 도형): 어깨 돌덩이 + 가슴 룬 + 주먹. wave_raised면 두 팔을 머리 위로 든다
    w, h = r - l, t - b
    rune = config.COLOR_GOLEM_RUNE
    cx = enemy.x
    camera.draw_rect(cx - w * 0.12, b + h * 0.5, cx + w * 0.12, b + h * 0.62, *rune, filled=True)   # 가슴 룬
    fist = w * 0.3
    if wave_raised:
        for side in (-1, 1):
            fx = cx + side * w * 0.35
            camera.draw_rect(fx - fist / 2, t, fx + fist / 2, t + fist, *config.COLOR_ROCK, filled=True)
        return
    # 평소: 몸 앞쪽 아래에 주먹. 주먹을 내지르는 동안(Windup)은 뒤로 당긴다
    pulled = enemy.state == WINDUP and enemy.attack is not None and enemy.attack.name.startswith('fist')
    front = cx + enemy.face_dir * (w / 2 - (fist if pulled else 0))
    fl = front if enemy.face_dir > 0 else front - fist
    camera.draw_rect(fl, b + h * 0.2, fl + fist, b + h * 0.2 + fist, *config.COLOR_ROCK, filled=True)


class RuinGolem(EnemyBase):
    # 유적 골렘 (10.2, 10.3): 느린 접근, 넉백·경직 없음. 주먹 (흰) / 충격파 (빨강, 점프로 넘김)
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        f, wv = STATS['fist'], STATS['wave']
        self.fist = Attack('fist', True, STATS['telegraph'], f['windup'], f['active'], f['recover'],
                           STATS['damage'], f['hitbox'])
        self.wave = Attack('wave', False, wv['telegraph'], wv['windup'], wv['active'], wv['recover'],
                           STATS['damage'], None)

    def choose_attacks(self):
        return [self.wave if random.random() < STATS['shockwave_chance'] else self.fist]

    def chase(self):
        # 주먹이 닿지 않아도 wave_range 안이면 쿨이 끝날 때마다 한 번 충격파를 굴려 본다
        if self.player.dead:
            self.vx = 0
            return
        dist = abs(self.player.x - self.x)
        if (not self.in_attack_range() and dist <= STATS['wave_range'] and self.attack_cooldown <= 0
                and abs(self.player.y - self.y) < self.h * 2):
            if random.random() < STATS['shockwave_chance']:
                self.face_player()
                self.vx = 0
                self.attack_queue = [self.wave]
                self.start_next_attack()
                return
            self.attack_cooldown = STATS['reroll']
        super().chase()

    def next_phase(self):
        super().next_phase()
        if self.state == ACTIVE and self.attack is self.wave:
            release_waves(self, STATS, self.attack_damage())

    def take_damage(self, damage, knockback=0):
        # 넉백·경직(Flinch) 없음 (10.3). 떨림·스파크만
        prev = self.state
        super().take_damage(damage)
        if self.state == FLINCH:
            self.set_state(prev)

    def draw_weapon(self, l, b, r, t):
        raised = self.attack is self.wave and self.state in (TELEGRAPH, WINDUP)
        draw_golem(self, l, b, r, t, raised)
