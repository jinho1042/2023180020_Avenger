import math

import config
import game_framework
import game_world
from objects import effect, magic_circle
from objects.bosses.boss_base import GROGGY, BossBase
from objects.enemy_base import ACTIVE, RECOVER, STAGGER, TELEGRAPH, WINDUP, Attack
from systems import camera, sound, terrain

STATS = config.BOSS_MOSS_WARDEN
SLAMS = ('slam', 'slam_wave')   # 대검을 머리 위로 드는 패턴 (내려찍기 + 충격파의 첫 동작 포함)


class Shockwave(magic_circle.MagicCircle):
    # 바닥 충격파 (빨강, 패링 불가): 내려찍은 자리에서 dir 쪽으로 shockwave_speed로 벽까지 미끄러진다
    # 낮아서 점프로 넘는다. 닿으면 한 번 피해 (무적이면 남아 있는 동안 다시 검사).
    # 마법진을 이어받아 페이즈 전환·처치 때 함께 지워진다 (boss_base.clear_hostile_projectiles)
    def __init__(self, x, y, direction, damage, player, platforms):
        spec = STATS['slam_wave']
        super().__init__(x, y, spec['wave_w'] / 2, 0, damage, player)
        self.dir = direction
        self.platforms = platforms

    def update(self):
        dt = game_framework.frame_time
        spec = STATS['slam_wave']
        self.x += self.dir * STATS['shockwave_speed'] * dt
        half = self.radius
        if (self.x - half <= 0 or self.x + half >= game_world.room_w
                or terrain.body_blocked(self.x, self.y + 1, spec['wave_w'], spec['wave_h'] - 1, self.platforms)):
            effect.burst(self.x, self.y, STATS['dust'], config.COLOR_ROCK)
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
        return self.x - self.radius, self.y, self.x + self.radius, self.y + STATS['slam_wave']['wave_h']


class MossWarden(BossBase):
    # B2 이끼 수문장 — 수문을 버티는 석상 (11.4)
    # 1~: 내려찍기(흰) · 회전 베기(빨강, 2칸) · 돌진 찌르기(흰)
    # 2페이즈(50%): 이끼 갑옷이 벗겨지고 균열 + 내려찍기·충격파(흰 → 빨강) · 도약 내려찍기(흰)
    boss_key = 'moss_warden'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.thrust_left = 0.0   # 돌진 찌르기로 더 나아갈 거리
        self.land_x = x          # 도약 내려찍기가 떨어질 자리
        self.left_ground = False
        self.build_patterns()

    def build_patterns(self):
        dmg, heavy = STATS['damage'], STATS['heavy_damage']
        s, sp, th, sw, lp = STATS['slam'], STATS['spin'], STATS['thrust'], STATS['slam_wave'], STATS['leap']

        def slam(name, recover):
            return Attack(name, True, s['telegraph'], s['windup'], s['active'], recover, dmg, s['hitbox'])

        self.patterns = dict(
            slam=[slam('slam', s['recover'])],
            spin=[Attack('spin', False, sp['telegraph'], sp['windup'], sp['active'], sp['recover'], heavy,
                         (STATS['spin_radius'] * 2, sp['hitbox_h']))],
            thrust=[Attack('thrust', True, th['telegraph'], th['windup'], th['active'], th['recover'], dmg,
                           th['hitbox'])],
            # 내려찍기 → 바로 바닥이 빛남(빨강 예고 glow초) → 충격파. 충격파는 몸 판정이 아니라 Shockwave가 맞힌다
            slam_wave=[slam('slam_wave', 0), Attack('wave', False, sw['glow'], 0, 0.05, sw['recover'], dmg, None)],
            # 도약은 착지할 때까지 Active (active 시간은 상한)
            leap=[Attack('leap', True, lp['telegraph'], lp['windup'], lp['air_time'] * 2, lp['recover'], dmg,
                         lp['hitbox'])])

    # ---------- 패턴 선택 ----------

    def pattern_table(self, near):
        if self.phase >= 2:
            return STATS['phase2_near'] if near else STATS['phase2_far']
        return STATS['near'] if near else STATS['far']

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        dist = abs(self.player.x - self.x)
        near = dist < STATS['near_range']
        if self.attack_cooldown <= 0:
            name = self.pick_pattern(self.pattern_table(near))
            if name:
                self.start_pattern(name, dist)
                return
        if dist > STATS['near_range'] / 2:
            self.vx = self.face_dir * self.speed

    def start_pattern(self, name, dist):
        self.remember_pattern(name, STATS['spin_cooldown'] if name == 'spin' else 0)
        self.attack_queue = list(self.patterns[name])
        self.start_next_attack()
        if name == 'thrust':
            th = STATS['thrust']
            self.thrust_left = max(th['min_dist'], dist + th['overshoot'])

    def next_phase(self):
        super().next_phase()
        if self.attack is None or self.state != ACTIVE:
            return
        if self.attack.name == 'wave':
            self.release_shockwaves()
        elif self.attack.name == 'leap':
            self.take_off()
        elif self.attack.name in SLAMS:
            self.slam_impact()

    # ---------- 내려찍기 · 충격파 ----------

    def slam_impact(self):
        fx = self.x + self.face_dir * (self.w / 2 + STATS['slam']['hitbox'][0] / 2)
        effect.burst(fx, self.y, STATS['dust'], config.COLOR_ROCK)
        camera.shake(*STATS['land_shake'])

    def release_shockwaves(self):
        damage = self.attack_damage()
        for d in (-1, 1):
            x = self.x + d * (self.w / 2 + STATS['slam_wave']['wave_w'] / 2)
            game_world.add_object(Shockwave(x, self.y, d, damage, self.player, self.platforms), config.DEPTH_MAP)
        camera.shake(*STATS['land_shake'])
        sound.play('door')

    # ---------- 돌진 찌르기 · 도약 ----------

    def is_thrusting(self):
        return self.state == ACTIVE and self.attack is not None and self.attack.name == 'thrust'

    def is_leaping(self):
        return self.state == ACTIVE and self.attack is not None and self.attack.name == 'leap'

    def take_off(self):
        # 플레이어 발밑(최대 max_dist)으로 air_time초 포물선. 높이는 air_time으로 정해진다
        lp = STATS['leap']
        t = lp['air_time']
        dx = max(-lp['max_dist'], min(lp['max_dist'], self.player.x - self.x))
        self.land_x = self.x + dx
        self.vx = dx / t
        self.vy = -config.GRAVITY * t / 2
        self.left_ground = False
        sound.play('dash')

    def land(self):
        effect.burst(self.x, self.y, STATS['dust'], config.COLOR_ROCK)
        camera.shake(*STATS['land_shake'])
        sound.play('door')
        self.vx = 0
        self.set_state(RECOVER, self.attack.recover)

    def update_ai(self):
        # 도약 중에는 vx를 지우지 않는다 (기본 update_ai는 공격 상태에서 vx = 0). 착지는 move가 정한다
        if self.is_leaping():
            if self.state_timer <= 0:
                self.next_phase()
            return
        super().update_ai()

    def move(self, dt):
        if self.is_thrusting():
            # 예고 때 바라본 방향으로 정해 둔 거리만큼 직진. 벽에 막히거나 다 가면 끝
            th = STATS['thrust']
            self.vx = self.face_dir * th['speed']
            prev = self.x
            super().move(dt)
            moved = abs(self.x - prev)
            self.thrust_left -= moved
            if self.thrust_left <= 0 or (dt > 0 and moved < th['speed'] * dt / 2):
                self.vx = 0
                self.set_state(RECOVER, self.attack.recover)
            return
        leaping = self.is_leaping()
        super().move(dt)
        if leaping:
            if not self.on_ground:
                self.left_ground = True
            elif self.left_ground:
                self.land()

    def on_parried(self):
        # 공중에서 패링당하면 그대로 떨어지며 비틀거린다 (가로 속도는 멈춤)
        super().on_parried()
        if self.state in (STAGGER, GROGGY):
            self.vx = 0

    # ---------- 페이즈 ----------

    def on_phase(self, phase):
        # 2페이즈: 이끼 갑옷이 벗겨지며 돌 몸통의 균열이 드러난다 (패턴표는 pattern_table이 바꾼다)
        self.color = STATS['color_phase2']
        effect.burst(self.x, self.y + self.h / 2, STATS['peel'], config.COLOR_MOSS_ARMOR)

    # ---------- 판정 ----------

    def get_attack_bb(self):
        if self.state != ACTIVE or self.attack is None:
            return None
        name = self.attack.name
        if name == 'spin':
            # 회전 베기는 몸 중심 좌우로 펼쳐진다 (반경 spin_radius)
            w, h = self.attack.hitbox
            b = self.y + (self.h - h) / 2
            return self.x - w / 2, b, self.x + w / 2, b + h
        if name == 'leap':
            # 내려오는 동안만 몸 아래쪽 넓은 판정 (올라가는 중에는 없음)
            if self.vy > 0:
                return None
            w, h = self.attack.hitbox
            return self.x - w / 2, self.y - h / 2, self.x + w / 2, self.y + h / 2
        return super().get_attack_bb()

    # ---------- 그리기 (도형) ----------

    def pattern_pose(self, *names):
        return self.attack is not None and self.attack.name in names and self.state in (TELEGRAPH, WINDUP)

    def draw(self):
        if self.is_leaping():
            self.draw_leap_shadow()
        if self.attack is not None and self.attack.name == 'wave' and self.state == TELEGRAPH:
            self.draw_floor_glow()
        super().draw()
        if self.state == RECOVER and self.attack is not None and self.attack.name == 'spin':
            self.draw_dizzy()

    def draw_body(self):
        if self.state == GROGGY:
            super().draw_body()
            return
        l, b, r, t = self.get_bb()
        if self.pattern_pose('leap'):
            t = b + self.h * 0.75   # 무릎을 굽힘
        color = self.body_color()
        camera.draw_rect(l, b, r, t, *color, filled=True)
        if self.phase == 1:
            self.draw_moss(l, b, r, t)
        self.draw_cracks()
        eye_x = self.x + self.face_dir * self.w / 4
        eye = self.w / 8
        camera.draw_rect(eye_x - eye / 2, t - eye * 3, eye_x + eye / 2, t - eye * 2, *config.COLOR_TEXT, filled=True)
        if self.state == TELEGRAPH and not self.attack.parryable and self.attack.name == 'spin':
            # 회전 베기 '!' (enemy_base와 같은 모양)
            camera.draw_rect(self.x - eye / 2, t + eye * 2, self.x + eye / 2, t + eye * 5,
                             *config.COLOR_UNPARRYABLE, filled=True)
            camera.draw_rect(self.x - eye / 2, t + eye / 2, self.x + eye / 2, t + eye * 1.5,
                             *config.COLOR_UNPARRYABLE, filled=True)
        self.draw_weapon(l, b, r, t)

    def draw_moss(self, l, b, r, t):
        # 1페이즈 이끼 갑옷: 어깨·몸통에 이끼 조각 (2페이즈 전환 때 벗겨진다)
        n, size = STATS['moss_tufts'], STATS['moss_size']
        for i in range(n):
            x = l + (r - l) * (i + 0.5) / n
            y = t - size * (1 + (i % 2))
            camera.draw_rect(x - size / 2, y, x + size / 2, y + size, *config.COLOR_MOSS_ARMOR, filled=True)
        camera.draw_rect(l, b + (t - b) * 0.45, r, b + (t - b) * 0.45 + size / 2, *config.COLOR_MOSS_ARMOR, filled=True)

    def draw_weapon(self, l, b, r, t):
        blade = self.w / 6
        c = config.COLOR_GREATSWORD
        f = self.face_dir
        if self.pattern_pose('spin'):
            # 회전 직전: 몸을 비틀어 대검을 몸 뒤로 수평으로 뺀다
            sx = self.x - f * (self.w / 2 + self.h / 2)
            cy = b + self.h / 2
            camera.draw_rect(min(sx, self.x), cy - blade / 2, max(sx, self.x), cy + blade / 2, *c, filled=True)
        elif self.pattern_pose(*SLAMS):
            # 내려찍기: 대검을 머리 위로 높이 든다
            camera.draw_rect(self.x - blade / 2, t, self.x + blade / 2, t + self.h * 0.8, *c, filled=True)
        elif self.attack is not None and self.attack.name == 'thrust' and self.state in (TELEGRAPH, WINDUP, ACTIVE):
            # 돌진 찌르기: 대검을 수평으로 앞에 겨눈다
            fx = r if f > 0 else l
            cy = b + self.h * 0.45
            tip = fx + f * self.h * 0.7
            camera.draw_rect(min(fx, tip), cy - blade / 2, max(fx, tip), cy + blade / 2, *c, filled=True)
        elif self.pattern_pose('leap') or self.is_leaping():
            # 도약: 대검을 거꾸로 쥐고 아래로 겨눈다
            camera.draw_rect(self.x - blade / 2, b - self.h * 0.3, self.x + blade / 2, b + self.h * 0.5, *c, filled=True)
        elif self.state in (ACTIVE, RECOVER, GROGGY):
            # 휘두른 뒤·그로기: 대검 끝이 바닥에 닿아 있다
            fx = r if f > 0 else l
            camera.draw_rect(fx + f * blade - blade / 2, b, fx + f * blade + blade / 2, b + self.h / 2, *c, filled=True)
        else:
            fx = r if f > 0 else l
            camera.draw_rect(fx - blade / 2, b + self.h / 3, fx + blade / 2, t + self.h / 4, *c, filled=True)

    def draw_leap_shadow(self):
        lp = STATS['leap']
        floor = magic_circle.floor_below(self.land_x, self.y, self.platforms)
        half = lp['shadow_w'] / 2
        effect.draw_alpha_rect(self.land_x - half, floor, self.land_x + half, floor + lp['shadow_h'],
                               config.COLOR_LEAP_SHADOW, 160)

    def draw_floor_glow(self):
        # 충격파 예고: 내려찍은 자리 양쪽 바닥이 빨갛게 빛남 (예고가 끝날수록 진해짐)
        a = self.attack
        k = 1 - max(0, self.state_timer) / a.telegraph
        h = STATS['slam_wave']['wave_h'] / 2
        effect.draw_alpha_rect(0, self.y, game_world.room_w, self.y + h, config.COLOR_SHOCKWAVE,
                               config.MAGIC_CIRCLE['warn_alpha'] * k)

    def draw_dizzy(self):
        # 회전 베기 뒤 어지러움: 머리 위를 도는 점
        d = STATS['dizzy']
        top = self.y + self.h + d['size']
        spin = (self.attack.recover - self.state_timer) * d['speed']
        for i in range(d['dots']):
            ang = spin + 2 * math.pi * i / d['dots']
            x = self.x + math.cos(ang) * d['radius']
            y = top + math.sin(ang) * d['radius'] * 0.3
            camera.draw_rect(x - d['size'] / 2, y - d['size'] / 2, x + d['size'] / 2, y + d['size'] / 2,
                             *config.COLOR_BOSS_GROGGY, filled=True)
