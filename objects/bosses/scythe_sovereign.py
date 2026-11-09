import math
import random

from pico2d import *

import config
import game_world
from objects import effect, projectile
from objects.bosses.boss_base import GROGGY, BossBase
from objects.enemy_base import ACTIVE, RECOVER, TELEGRAPH, WINDUP, Attack
from systems import camera, sound, terrain

STATS = config.BOSS_SCYTHE
COMBO_POSE = ('combo', 'feint')   # 두 낫을 교차하는 자세 (페이크는 4연속 베기 자세만 하고 멈춘다)


class ScytheSovereign(BossBase):
    # B5 쌍낫 군주 — 어둠 속의 사냥꾼 (11.4)
    # 1~: 4연속 베기(흰, 리듬 연속 패링) · 순간이동 기습(빨강, 2칸) · 낫날 투척(흰, 반사)
    # 2페이즈(50%): 속도 × phase2_speed_mult, 빨강 비율 증가, 그림자 낫 소용돌이(빨강) 추가, 페이크(원칙 14)
    boss_key = 'scythe'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.phase2 = False
        self.since_feint = STATS['feint_cycle']   # 마지막 페이크 뒤 쓴 패턴 수 (feint_cycle 이상이어야 다시 페이크)
        self.force_white = False                  # 페이크 다음 패턴은 반드시 흰 패턴
        self.ground_y = y                         # 소용돌이로 떠오르기 전 발 높이
        self.dive_x = x                           # 소용돌이가 내리꽂힐 자리 (예고가 끝날 때 정한다)
        self.build_patterns(1)

    def build_patterns(self, mult):
        # 패턴 이름 → 이어서 쓸 Attack 목록. 예고·동작 시간 ÷ mult (예고는 Attack이 TELEGRAPH_MIN 이상으로 맞춘다)
        # 패턴 끝 반격 틈(마지막 recover)은 페이즈와 상관없이 그대로 (원칙 3)
        dmg, heavy = STATS['damage'], STATS['heavy_damage']

        def timed(name, parryable, spec, telegraph, recover, damage, hitbox):
            return Attack(name, parryable, telegraph / mult, spec['windup'] / mult, spec['active'] / mult,
                          recover, damage, hitbox)

        c, tp, th, vt = STATS['combo'], STATS['teleport'], STATS['throw'], STATS['vortex']
        combo = []
        for i in range(c['count']):
            last = i == c['count'] - 1
            telegraph = c['telegraph'] if i == 0 else c['next_telegraph']
            recover = c['last_recover'] if last else c['recover'] / mult
            combo.append(timed('combo', True, c, telegraph, recover, dmg, c['hitbox']))
        self.patterns = dict(
            combo=combo,
            teleport=[timed('teleport', False, tp, tp['telegraph'], tp['recover'], heavy, tp['hitbox'])],
            throw=[timed('throw', True, th, th['telegraph'], th['recover'], dmg, None)],
            # 소용돌이는 착지할 때까지 Active (active는 상한이라 나누지 않는다)
            vortex=[Attack('vortex', False, vt['telegraph'] / mult, vt['windup'] / mult, vt['active'],
                           vt['recover'], dmg, vt['hitbox'])],
            # 페이크: 4연속 베기 첫 예고(흰)만 하고 feint_recover 동안 멈춘다 (next_phase)
            feint=[Attack('feint', True, c['telegraph'] / mult, 0, 0, STATS['feint_recover'], dmg, None)])

    # ---------- 패턴 선택 ----------

    def pattern_table(self, near):
        if self.phase2:
            table = STATS['phase2_near'] if near else STATS['phase2_far']
        else:
            table = STATS['near'] if near else STATS['far']
        if self.force_white:
            # 페이크 다음은 흰 패턴만 (원칙 14). 먼 거리 표에 4연속 베기가 없으면 낫날 투척
            table = {n: max(table.get(n, 0), 1) for n in STATS['feint_next']}
        return table

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        dist = abs(self.player.x - self.x)
        if self.attack_cooldown <= 0:
            name = self.pick_pattern(self.pattern_table(dist <= STATS['near_range']))
            if name:
                self.start_pattern(name)
                return
        if dist > STATS['near_range'] / 2:
            self.vx = self.face_dir * self.speed

    def can_feint(self):
        # 마지막 페이즈에서만, 패턴 feint_cycle개에 최대 1회, 페이크 바로 다음은 안 됨 (원칙 14)
        return self.phase2 and not self.force_white and self.since_feint >= STATS['feint_cycle']

    def start_pattern(self, name):
        if name == 'combo' and self.can_feint() and random.random() < STATS['feint_chance']:
            name = 'feint'
        cooldown = STATS.get(name + '_cooldown', 0)
        self.remember_pattern(name, cooldown)
        if name == 'feint':
            self.since_feint = 0
            self.force_white = True
        else:
            self.since_feint += 1
            self.force_white = False
        self.attack_queue = list(self.patterns[name])
        self.start_next_attack()
        if name == 'vortex':
            self.ground_y = self.y

    def next_phase(self):
        if self.state == TELEGRAPH and self.attack is not None and self.attack.name == 'feint':
            # 페이크: 예고만 하고 공격 없이 멈춘다
            self.set_state(RECOVER, self.attack.recover)
            return
        super().next_phase()
        if self.attack is None:
            return
        name = self.attack.name
        if self.state == WINDUP and name == 'teleport':
            self.teleport_behind_player()
        elif self.state == WINDUP and name == 'vortex':
            self.lock_dive()
        elif self.state == ACTIVE and name == 'throw':
            self.throw_blade()
        elif self.state == ACTIVE and name == 'vortex':
            self.start_dive()
        elif self.state == ACTIVE and name == 'combo':
            self.step_forward()

    # ---------- 4연속 베기 ----------

    def step_forward(self):
        # 타마다 조금씩 파고든다 (플레이어 쪽, 벽·아레나 끝에서 멈춤)
        self.x = self.fit_x(self.x + self.face_dir * STATS['combo']['step'], self.y)

    def recoil(self):
        # 4연속 베기 도중엔 패링당해도 멈추지 않고 다음 타로 이어간다 (자세만 쌓인다)
        if self.attack_queue:
            return
        super().recoil()

    # ---------- 순간이동 기습 ----------

    def is_lunging(self):
        return self.state == ACTIVE and self.attack is not None and self.attack.name == 'teleport'

    def teleport_behind_player(self):
        effect.burst(self.x, self.y + self.h / 2, config.TELEPORT_PUFF, self.color)
        # 등 뒤가 벽·아레나 끝이라 밀려나면 앞쪽으로 나타난다
        offset = STATS['teleport']['offset']
        x = self.x
        for side in (-self.player.face_dir, self.player.face_dir):
            want = self.player.x + side * offset
            x = self.fit_x(want, self.player.y)
            if abs(x - want) < 1:
                break
        self.x = x
        # 플레이어가 공중이면 지금 높이 그대로 두고 떨어지게 한다
        if self.player.on_ground:
            self.y = self.player.y
        self.vy = 0
        self.face_player()
        effect.burst(self.x, self.y + self.h / 2, config.TELEPORT_PUFF, self.color)
        sound.play('dash')

    def fit_x(self, x, y):
        half_w = self.w / 2
        x = terrain.resolve_x(x, y, self.w, self.h, self.platforms)
        return clamp(half_w, x, game_world.room_w - half_w)

    # ---------- 낫날 투척 ----------

    def throw_blade(self):
        # 플레이어 몸 높이에 맞춰 수평으로 회전 낫날 (패링·반사 가능)
        x = self.x + self.face_dir * self.w / 2
        y = self.y + config.PLAYER_H / 2
        projectile.fire(x, y, self.face_dir, 0, STATS['throw']['speed'], self.attack_damage(),
                        self.attack.parryable, self.platforms, config.SCYTHE_BLADE, owner=self)

    # ---------- 그림자 낫 소용돌이 ----------

    def is_vortex(self, *states):
        return self.attack is not None and self.attack.name == 'vortex' and self.state in states

    def lock_dive(self):
        # 예고가 끝난 순간의 플레이어 x (가로 max_dx까지)를 내리꽂을 자리로 정한다. windup 동안 그 바닥에 빨간 표시
        vt = STATS['vortex']
        dx = max(-vt['max_dx'], min(vt['max_dx'], self.player.x - self.x))
        self.dive_x = self.fit_x(self.x + dx, self.ground_y)
        sound.play('telegraph_red')

    def start_dive(self):
        # 정해 둔 자리, 떠오르기 전 바닥 높이로 대각선 내리꽂기
        vt = STATS['vortex']
        dx = self.dive_x - self.x
        dy = self.ground_y - self.y
        length = math.hypot(dx, dy) or 1
        self.vx = dx / length * vt['dive_speed']
        self.vy = dy / length * vt['dive_speed']
        if dx:
            self.face_dir = 1 if dx > 0 else -1
        sound.play('dash')

    def land(self):
        effect.burst(self.x, self.y, STATS['dust'], config.COLOR_ROCK)
        camera.shake(*STATS['land_shake'])
        sound.play('door')
        self.vx, self.vy = 0, 0
        self.set_state(RECOVER, self.attack.recover)

    # ---------- 상태 진행 · 이동 ----------

    def update_ai(self):
        # 대시 베기·내리꽂기 중에는 vx를 지우지 않는다 (기본 update_ai는 공격 상태에서 vx = 0)
        if self.is_lunging():
            self.vx = self.face_dir * STATS['teleport']['lunge_speed']
            if self.state_timer <= 0:
                self.vx = 0
                self.next_phase()
            return
        if self.is_vortex(ACTIVE):
            if self.state_timer <= 0:
                # 상한까지 착지하지 못하면(공중에서 막힘) 그대로 떨어지며 반격 틈
                self.vx = 0
                self.set_state(RECOVER, self.attack.recover)
            return
        super().update_ai()

    def move(self, dt):
        if self.is_vortex(TELEGRAPH, WINDUP):
            self.rise(dt)
            return
        if self.is_vortex(ACTIVE):
            self.dive(dt)
            return
        super().move(dt)

    def rise(self, dt):
        # 중력 없이 바닥에서 rise px 위까지 rise_time초 동안 떠오른 뒤 그 자리에서 회전 (천장에 닿으면 멈춤)
        vt = STATS['vortex']
        prev_y = self.y
        target = self.ground_y + vt['rise']
        self.y = min(target, self.y + vt['rise'] / vt['rise_time'] * dt)
        self.y, _, _ = terrain.resolve_y(self.x, prev_y, self.y, 1, self.w, self.h, self.platforms)
        self.vx, self.vy = 0, 0
        self.on_ground = False

    def dive(self, dt):
        # 정해 둔 방향으로 중력 없이 직선. 바닥에 닿으면 착지
        self.move_x(dt)
        prev_y = self.y
        self.y += self.vy * dt
        self.y, vy, self.on_ground = terrain.resolve_y(
            self.x, prev_y, self.y, self.vy, self.w, self.h, self.platforms)
        if self.on_ground:
            self.land()
        elif vy == 0:
            self.vy = -STATS['vortex']['dive_speed']   # 천장에 걸리면 곧장 아래로

    # ---------- 페이즈 ----------

    def on_phase(self, phase):
        # 2페이즈: 갑각이 짙은 보라로 물들고 모든 동작이 빨라진다 (포효·무적·투사체 제거는 boss_base)
        self.phase2 = True
        mult = STATS['phase2_speed_mult']
        self.speed *= mult
        self.color = STATS['color_phase2']
        self.build_patterns(mult)
        effect.burst(self.x, self.y + self.h / 2, config.TELEPORT_PUFF, self.color)

    # ---------- 판정 ----------

    def get_attack_bb(self):
        if self.is_vortex(ACTIVE):
            # 내리꽂는 동안 몸 둘레 (회전하는 낫)
            w, h = self.attack.hitbox
            cy = self.y + self.h / 2
            return self.x - w / 2, cy - h / 2, self.x + w / 2, cy + h / 2
        return super().get_attack_bb()

    # ---------- 그리기 (도형) ----------

    def draw(self):
        if self.is_vortex(WINDUP):
            # 내리꽂힐 자리 바닥에 빨간 표시 (9.1 몸이 아닌 곳의 예고)
            vt = STATS['vortex']
            half = vt['mark_w'] / 2
            effect.draw_alpha_rect(self.dive_x - half, self.ground_y, self.dive_x + half, self.ground_y + vt['mark_h'],
                                   config.COLOR_UNPARRYABLE, config.MAGIC_CIRCLE['warn_alpha'])
        super().draw()

    def pose(self, names, *states):
        return self.attack is not None and self.attack.name in names and self.state in states

    def draw_body(self):
        if self.state == GROGGY:
            super().draw_body()
            return
        l, b, r, t = self.get_bb()
        color = self.body_color()
        if self.pose(('teleport',), TELEGRAPH):
            # 그림자로 녹아듦: 예고가 끝날수록 옅어진다
            k = max(0.0, self.state_timer) / self.attack.telegraph
            alpha = STATS['fade_alpha'] + (255 - STATS['fade_alpha']) * k
            effect.draw_alpha_rect(l, b, r, t, color, alpha)
        else:
            camera.draw_rect(l, b, r, t, *color, filled=True)
        self.draw_cracks()
        eye = self.w / 8
        for dx in (self.w / 6, self.w / 3):   # 사마귀 겹눈 두 개
            ex = self.x + self.face_dir * dx
            camera.draw_rect(ex - eye / 2, t - eye * 3, ex + eye / 2, t - eye * 2, *config.COLOR_TEXT, filled=True)
        if self.state == TELEGRAPH and not self.attack.parryable:
            # 패링 불가 '!' (enemy_base와 같은 모양)
            camera.draw_rect(self.x - eye / 2, t + eye * 2, self.x + eye / 2, t + eye * 5,
                             *config.COLOR_UNPARRYABLE, filled=True)
            camera.draw_rect(self.x - eye / 2, t + eye / 2, self.x + eye / 2, t + eye * 1.5,
                             *config.COLOR_UNPARRYABLE, filled=True)
        self.draw_weapon(l, b, r, t)

    def draw_scythe(self, hx, hb, length, blade_dir, up=True):
        # 자루(세로) + 자루 끝에서 blade_dir 쪽으로 뻗은 날. up=False면 날이 아래 끝에 붙는다
        s = STATS['scythe']
        half = s['thick'] / 2
        camera.draw_rect(hx - half, hb, hx + half, hb + length, *config.COLOR_SCYTHE_HANDLE, filled=True)
        by = hb + length if up else hb
        tip = hx + blade_dir * s['blade']
        camera.draw_rect(min(hx, tip), by - s['blade_h'], max(hx, tip), by, *config.COLOR_SCYTHE, filled=True)

    def draw_flat_scythe(self, x0, y, direction):
        # 자루를 수평으로 앞에 겨눈 낫 (대시 베기)
        s = STATS['scythe']
        half = s['thick'] / 2
        x1 = x0 + direction * s['handle']
        camera.draw_rect(min(x0, x1), y - half, max(x0, x1), y + half, *config.COLOR_SCYTHE_HANDLE, filled=True)
        camera.draw_rect(x1 - s['blade_h'] / 2, y - s['blade'], x1 + s['blade_h'] / 2, y, *config.COLOR_SCYTHE,
                         filled=True)

    def draw_weapon(self, l, b, r, t):
        s = STATS['scythe']
        f = self.face_dir
        cy = b + self.h / 2
        if self.pose(('vortex',), TELEGRAPH, WINDUP, ACTIVE):
            # 소용돌이: 두 낫이 몸 둘레를 돈다
            sp = STATS['spin']
            ang = self.state_timer * sp['speed']
            size = s['blade'] / 2
            for i in range(sp['blades']):
                a = ang + 2 * math.pi * i / sp['blades']
                x, y = self.x + math.cos(a) * sp['radius'], cy + math.sin(a) * sp['radius']
                camera.draw_rect(x - size / 2, y - size / 2, x + size / 2, y + size / 2, *config.COLOR_SCYTHE,
                                 filled=True)
            return
        if self.pose(COMBO_POSE, TELEGRAPH):
            # 두 낫을 가슴 앞에서 교차 (날이 서로 반대쪽)
            for side in (-1, 1):
                self.draw_scythe(self.x + side * self.w / 4, cy - s['handle'] / 3, s['handle'], -side)
            return
        if self.pose(('combo',), WINDUP, ACTIVE, RECOVER):
            # 베는 중: 앞쪽 낫은 날을 아래로 휘두르고, 뒤쪽 낫은 머리 위로
            front = r if f > 0 else l
            self.draw_scythe(front + f * s['thick'], cy - s['handle'], s['handle'], f, up=False)
            back = l if f > 0 else r
            self.draw_scythe(back, t - s['handle'] / 3, s['handle'], f)
            return
        if self.pose(('throw',), TELEGRAPH, WINDUP):
            # 한 팔을 뒤로 젖혀 낫을 든다
            back = l if f > 0 else r
            self.draw_scythe(back - f * s['thick'] * 2, t - s['handle'] / 4, s['handle'], -f)
            front = r if f > 0 else l
            self.draw_scythe(front, b + self.h / 4, s['handle'], f)
            return
        if self.pose(('throw',), ACTIVE, RECOVER):
            # 던진 뒤: 앞쪽 낫 하나만
            front = r if f > 0 else l
            self.draw_scythe(front, b + self.h / 4, s['handle'], f)
            return
        if self.pose(('teleport',), WINDUP, ACTIVE):
            # 대시 베기: 두 낫을 수평으로 앞에 겨눈다
            front = r if f > 0 else l
            for dy in (-self.h / 6, self.h / 6):
                self.draw_flat_scythe(front, cy + dy, f)
            return
        if self.pose(('teleport',), TELEGRAPH):
            return   # 녹아드는 중에는 낫도 보이지 않는다
        # 평소: 양옆에 낫을 세워 들고 날은 앞쪽
        for side in (l, r):
            self.draw_scythe(side, b + self.h / 4, s['handle'], f)
