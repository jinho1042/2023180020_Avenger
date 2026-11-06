from pico2d import clamp

import config
from objects import effect
from objects.enemy_base import ACTIVE, CHASE, RECOVER, Attack, EnemyBase
from systems import camera

STATS = config.LEECH
STRANDED = 'Stranded'


class Leech(EnemyBase):
    # 독 거머리 (10.2, 10.3): spawn이 들어 있는 water 영역 안에서만 수면 바로 아래를 헤엄친다
    # 플레이어 발이 수면 위이고 가로 trigger_dist 안이면 흰 예고 → 포물선 도약 (몸 전체가 공격 판정, 패링 가능)
    # 물로 떨어지면 다시 헤엄, 물 밖 땅에 떨어지면 STATS.stranded초 뒤 죽는다
    # water 영역은 systems/room.py가 set_water로 넘긴다. 물 밖에 놓이면 처음부터 땅 위 거머리 (곧 죽음)
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.leap = Attack('leap', True, STATS['telegraph'], STATS['windup'], STATS['active'], STATS['recover'],
                           STATS['damage'], None)
        self.pool = None          # (l, b, r, t) 헤엄치는 물 영역
        self.airborne = False     # 도약·패링으로 물 밖에 떠 있는 동안 (중력을 받는다)
        self.state = CHASE

    def set_water(self, rects):
        cx, cy = self.x, self.y + self.h / 2
        self.pool = next(((x, y, x + w, y + h) for x, y, w, h in (r[:4] for r in rects)
                          if x <= cx <= x + w and y <= cy <= y + h), None)
        if self.pool:
            self.y = self.swim_y()
            self.face_dir = 1
        else:
            self.airborne = True

    def swim_y(self):
        return self.pool[3] - STATS['depth'] - self.h

    def in_pool(self):
        if not self.pool:
            return False
        l, b, r, t = self.pool
        cx, cy = self.x, self.y + self.h / 2
        return l <= cx <= r and b <= cy <= t

    def player_above_surface(self):
        return (not self.player.dead and self.player.y >= self.pool[3] - config.PLAYER_H / 2
                and abs(self.player.x - self.x) <= STATS['trigger_dist'])

    # ---------- AI ----------

    def update_ai(self):
        if self.state == STRANDED:
            self.vx = 0
            if self.state_timer <= 0:
                self.die()
            return
        if self.airborne:
            # 물 밖에 떠 있는 동안: 도약 중이면 가로 속도 그대로, 아니면(패링당함 등) 수직으로 떨어진다
            if not (self.state == ACTIVE and self.attack is self.leap):
                self.vx = 0
            if self.state != CHASE and self.state_timer <= 0:
                self.next_phase()
            return
        if self.state == CHASE:
            self.swim()
            return
        super().update_ai()

    def swim(self):
        # 플레이어가 가까우면 그 아래로, 아니면 물 끝에서 끝까지 왕복
        l, _, r, _ = self.pool
        half = self.w / 2
        if self.player_above_surface() and self.attack_cooldown <= 0:
            self.vx = 0
            self.attack_queue = [self.leap]
            self.start_next_attack()
            return
        if not self.player.dead and abs(self.player.x - self.x) <= self.detect_range and l < self.player.x < r:
            if abs(self.player.x - self.x) > half:
                self.face_dir = 1 if self.player.x > self.x else -1
                self.vx = self.face_dir * STATS['swim_speed']
            else:
                self.vx = 0
            return
        if (self.face_dir > 0 and self.x + half >= r - 1) or (self.face_dir < 0 and self.x - half <= l + 1):
            self.face_dir = -self.face_dir
        self.vx = self.face_dir * STATS['swim_speed']

    def next_phase(self):
        super().next_phase()
        if self.state == ACTIVE and self.attack is self.leap:
            self.jump()

    def jump(self):
        # 위로 leap_speed. 같은 높이로 돌아올 때 플레이어 x에 닿도록 가로 속도 (leap_vx_max까지)
        t_air = 2 * STATS['leap_speed'] / -config.GRAVITY
        self.vx = clamp(-STATS['leap_vx_max'], (self.player.x - self.x) / t_air, STATS['leap_vx_max'])
        self.vy = STATS['leap_speed']
        self.airborne = True
        self.on_ground = False
        self.splash()

    def on_parried(self):
        # 공중에서 패링당하면 가로로 멈추고 그대로 떨어진다
        super().on_parried()
        self.vx = 0

    def splash(self):
        effect.burst(self.x, self.pool[3] if self.pool else self.y, STATS['splash'], config.COLOR_WATER_SURFACE)

    # ---------- 이동 ----------

    def move(self, dt):
        if not self.is_alive():
            return   # 이번 프레임 update_ai에서 죽었다 (땅 위 STRANDED 끝)
        if not self.airborne:
            # 헤엄: 중력 없이 수면 아래 높이 그대로, 물 영역 안에서만
            self.vy = 0
            self.move_x(dt)
            l, _, r, _ = self.pool
            self.x = clamp(l + self.w / 2, self.x, r - self.w / 2)
            self.y = self.swim_y()
            return
        super().move(dt)
        if self.vy < 0 and self.in_pool() and self.y <= self.swim_y():
            self.land_in_water()
        elif self.on_ground and self.state != STRANDED and not self.in_pool():
            self.vx = 0
            self.attack_queue = []
            self.attack = None
            self.set_state(STRANDED, STATS['stranded'])

    def land_in_water(self):
        self.airborne = False
        self.vy = 0
        self.y = self.swim_y()
        self.splash()
        if self.state == ACTIVE and self.attack is self.leap:
            self.vx = 0
            self.set_state(RECOVER, self.leap.recover)

    # ---------- 판정 · 그림 ----------

    def get_attack_bb(self):
        if self.state == ACTIVE and self.attack is self.leap and self.airborne:
            return self.get_bb()
        return None

    def draw_body(self):
        # 땅 위에서는 퍼덕인다 (그리는 방향만 번갈아 뒤집음)
        flip = self.state == STRANDED and int(self.state_timer / STATS['flop']) % 2
        if flip:
            self.face_dir = -self.face_dir
        super().draw_body()
        if flip:
            self.face_dir = -self.face_dir

    def draw_weapon(self, l, b, r, t):
        # 등의 노란 반점 두 개
        spot = self.h / 3
        for k in (0.3, 0.6):
            x = l + (r - l) * k
            camera.draw_rect(x - spot / 2, t - spot, x + spot / 2, t, *config.COLOR_LEECH_SPOT, filled=True)
