import config
import game_world
from objects import effect, magic_circle
from objects.air_vent import AirVent
from objects.bosses.boss_base import DORMANT, GROGGY, BossBase
from objects.enemy_base import ACTIVE, RECOVER, TELEGRAPH, WINDUP, Attack, EnemyBase
from systems import camera, sound

STATS = config.BOSS_BORER
CHARGES = ('charge', 'double_charge')
OFFSCREEN = -100000   # 땅속에 있는 동안 몸 판정을 치울 자리


class FallingRock(magic_circle.MagicCircle):
    # 낙석 (빨강, 패링 불가): 떨어질 자리(바닥·발판)에 빨간 그림자 shadow초 → 천장에서 돌이 떨어져
    # 닿는 순간부터 hit_time 동안 판정. 마법진을 이어받아 페이즈 전환·처치 때 함께 지워진다 (boss_base)
    def __init__(self, x, floor_y, ceiling_y, damage, player):
        spec = STATS['rockfall']
        super().__init__(x, floor_y, spec['rock_w'] / 2, spec['shadow'], damage, player)
        self.active_timer = spec['hit_time']
        self.ceiling_y = ceiling_y
        self.landed = False

    def update(self):
        if self.is_exploding() and not self.landed:
            self.landed = True
            trap = config.ROCKFALL_TRAP
            effect.burst(self.x, self.y, trap['debris'], config.COLOR_ROCK)
            camera.shake(*trap['shake'])
        super().update()

    def rock_bottom(self):
        # 그림자가 끝나기 fall_time 전부터 천장에서 떨어지기 시작해 그림자 끝에 바닥에 닿는다
        fall = STATS['rockfall']['fall_time']
        if self.timer >= fall:
            return None
        return self.y + (self.ceiling_y - self.y) * max(0, self.timer) / fall

    def draw(self):
        spec, trap = STATS['rockfall'], config.ROCKFALL_TRAP
        l, r = self.x - self.radius, self.x + self.radius
        if not self.is_exploding():
            k = 1 - self.timer / self.delay
            effect.draw_alpha_rect(l, self.y, r, self.y + trap['shadow_h'], config.COLOR_ROCK_SHADOW,
                                   trap['shadow_alpha'] * k)
        bottom = self.y if self.is_exploding() else self.rock_bottom()
        if bottom is not None:
            camera.draw_rect(l, bottom, r, bottom + spec['rock_h'], *config.COLOR_ROCK, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        return self.x - self.radius, self.y, self.x + self.radius, self.y + STATS['rockfall']['hit_h']


class RockshellBorer(BossBase):
    # B1 바위껍질 굴착충 — 공기를 쫓은 것 (11.4)
    # 돌진(흰) · 꼬리 휘두르기(흰) · 잠행 돌격(빨강) · 낙석(빨강) + 2페이즈 연속 돌진(흰)
    # 등장: 아레나 왼쪽 벽을 뚫고 나온다 (잠들어 있는 동안은 보이지 않음)
    boss_key = 'borer'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.charge_speed = STATS['charge_speed']
        self.burrow_x = x      # 잠행 돌격이 솟구칠 자리
        self.span = None       # 아레나 안쪽 (왼쪽 벽 오른쪽 면, 오른쪽 벽 왼쪽 면). 등장 때 잰다
        self.build_patterns()

    def build_patterns(self):
        def attack(name, spec, parryable, telegraph=None, recover=None):
            return Attack(name, parryable, spec['telegraph'] if telegraph is None else telegraph, spec['windup'],
                          spec['active'], spec['recover'] if recover is None else recover,
                          STATS['damage'], spec.get('hitbox'))   # 11.4 표: 모든 패턴 1칸 (빨강 포함)

        c, d = STATS['charge'], STATS['double_charge']
        self.patterns = dict(
            charge=[attack('charge', c, True)],
            # 연속 돌진: 같은 자세 → 첫 충돌 뒤 짧게 돌아서 다시 돌진. 마지막 충돌 뒤에만 charge.recover
            double_charge=[attack('double_charge', c, True, recover=d['turn_recover']),
                           attack('double_charge', c, True, telegraph=d['next_telegraph'])],
            tail=[attack('tail', STATS['tail'], True)],
            burrow=[attack('burrow', STATS['burrow'], False)],
            rockfall=[attack('rockfall', STATS['rockfall'], False)])

    # ---------- 등장 ----------

    def wake(self, first):
        self.span = self.measure_span()
        super().wake(first)
        # 벽을 뚫고 나온다: 몸 뒤쪽 벽에서 돌 파편
        wall_x = self.span[0] if self.x - self.span[0] < self.span[1] - self.x else self.span[1]
        effect.burst(wall_x, self.y + self.h / 2, STATS['shell_burst'], config.COLOR_ROCK)
        camera.shake(*STATS['wall_shake'])

    def measure_span(self):
        # 몸 높이에서 좌우로 가장 가까운 단단한 지형 (벽·흙벽). 없으면 방 끝
        l, r = 0, game_world.room_w
        for p in self.platforms:
            if p.kind != 'solid' or p.top <= self.y or p.bottom >= self.y + self.h:
                continue
            if p.right <= self.x:
                l = max(l, p.right)
            elif p.left >= self.x:
                r = min(r, p.left)
        return l, r

    # ---------- 패턴 선택 ----------

    def pattern_weights(self, dist):
        weights = dict(STATS['phase2_base'] if self.phase >= 2 else STATS['base'])
        if dist > STATS['far_dist']:
            weights['charge'] = STATS['far_weight']
        if dist < STATS['near_range']:
            weights['tail'] = STATS['near_weight']
        if self.history and self.history[-1] == 'burrow':
            weights['burrow'] = 0   # 잠행은 연속 금지
        return weights

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        dist = abs(self.player.x - self.x)
        if self.attack_cooldown <= 0:
            name = self.pick_pattern(self.pattern_weights(dist))
            if name:
                self.start_pattern(name)
                return
        if dist > STATS['near_range']:
            self.vx = self.face_dir * self.speed

    def start_pattern(self, name):
        self.remember_pattern(name, STATS['rockfall_cooldown'] if name == 'rockfall' else 0)
        self.attack_queue = list(self.patterns[name])
        self.start_next_attack()
        if name == 'tail':
            self.face_dir = -self.face_dir   # 등을 돌려 꼬리를 플레이어 쪽으로
        elif name == 'burrow':
            half = self.w / 2
            self.burrow_x = min(max(self.player.x, self.span[0] + half), self.span[1] - half)

    def next_phase(self):
        super().next_phase()
        if self.attack is None:
            return
        name = self.attack.name
        if self.state == WINDUP and name == 'burrow':
            self.x = self.burrow_x   # 땅속으로 이동
        elif self.state == ACTIVE and name == 'burrow':
            effect.burst(self.x, self.y, STATS['dig_dust'], config.COLOR_ROCK)
            camera.shake(*STATS['wall_shake'])
        elif self.state == ACTIVE and name == 'rockfall':
            self.drop_rocks()

    # ---------- 돌진 ----------

    def is_charging(self):
        return self.state == ACTIVE and self.attack is not None and self.attack.name in CHARGES

    def move(self, dt):
        if not self.is_charging():
            super().move(dt)
            return
        # 바라본 방향으로 벽에 닿을 때까지 직진. 제대로 나아가지 못하면 벽에 부딪힌 것
        self.vx = self.face_dir * self.charge_speed
        prev = self.x
        super().move(dt)
        if dt > 0 and abs(self.x - prev) < self.charge_speed * dt / 2:
            self.hit_wall()

    def hit_wall(self):
        front = self.x + self.face_dir * self.w / 2
        effect.burst(front, self.y + self.h / 2, STATS['dig_dust'], config.COLOR_ROCK)
        camera.shake(*STATS['wall_shake'])
        sound.play('door')
        self.vx = 0
        self.set_state(RECOVER, self.attack.recover)   # 벽에 박혀 멈춤 = 반격 틈

    # ---------- 잠행 · 낙석 ----------

    def is_underground(self):
        # 잠행 돌격: 파고들기 시작(예고)부터 솟구치기 직전까지 땅속. 맞지 않고 닿아도 피해 없음
        return (self.attack is not None and self.attack.name == 'burrow'
                and self.state in (TELEGRAPH, WINDUP))

    def dig_progress(self):
        # 땅으로 파고든 정도 0~1 (예고 처음 dig초 동안)
        if self.state != TELEGRAPH:
            return 1.0
        elapsed = self.attack.telegraph - self.state_timer
        return min(1.0, max(0.0, elapsed / STATS['burrow']['dig']))

    def invulnerable(self):
        return super().invulnerable() or self.is_underground()

    def deals_contact(self):
        return not self.is_underground() and super().deals_contact()

    def drop_rocks(self):
        # 천장 박치기 순간: rock_count개. 플레이어 발밑과 숨구멍 위에 하나씩, 나머지는 아레나에 고르게
        spec = STATS['rockfall']
        count = STATS['rock_count'][min(self.phase, len(STATS['rock_count'])) - 1]
        l, r = self.span[0] + spec['margin'], self.span[1] - spec['margin']
        xs = [l + (r - l) * (i + 0.5) / count for i in range(count)]
        vents = [v.x for layer in game_world.world for v in layer if isinstance(v, AirVent)]
        taken = set()
        for want in [self.player.x] + vents:
            free = [i for i in range(count) if i not in taken]
            if not free:
                break
            i = min(free, key=lambda k: abs(xs[k] - want))
            xs[i] = min(max(want, self.span[0] + spec['rock_w'] / 2), self.span[1] - spec['rock_w'] / 2)
            taken.add(i)
        damage = self.attack_damage()
        for x in xs:
            ceiling = self.ceiling_above(x)
            floor = magic_circle.floor_below(x, ceiling - 1, self.platforms)
            game_world.add_object(FallingRock(x, floor, ceiling, damage, self.player), config.DEPTH_MAP)
        camera.shake(*STATS['wall_shake'])
        sound.play('door')

    def ceiling_above(self, x):
        tops = [p.bottom for p in self.platforms
                if p.kind == 'solid' and p.left <= x <= p.right and p.bottom >= self.y + self.h]
        return min(tops) if tops else game_world.room_h

    # ---------- 페이즈 ----------

    def on_phase(self, phase):
        # 2페이즈: 껍질 앞부분이 깨지고(몸통 노출) 빨라진다. 연속 돌진·낙석 6개 (11.4)
        mult = STATS['p2_speed_mult']
        self.speed = STATS['speed'] * mult
        self.charge_speed = STATS['charge_speed'] * mult
        self.color = STATS['color_phase2']

    def die(self):
        super().die()
        effect.burst(self.x, self.y + self.h / 2, STATS['shell_burst'], config.COLOR_BORER_SHELL)   # 껍질이 쪼개짐

    # ---------- 판정 ----------

    def get_bb(self):
        # 벽 속(잠듦)·땅속에서는 맞지도 닿지도 않는다
        if self.state == DORMANT or self.is_underground():
            return self.x, OFFSCREEN, self.x, OFFSCREEN
        return self.body_bb()

    def body_bb(self):
        return EnemyBase.get_bb(self)

    def get_attack_bb(self):
        if self.state != ACTIVE or self.attack is None:
            return None
        name = self.attack.name
        w, h = self.attack.hitbox if self.attack.hitbox else (0, 0)
        if name == 'tail':
            # 몸 뒤쪽 반원 (등 쪽 = 플레이어 쪽)
            back = self.x - self.face_dir * self.w / 2
            l = back - w if self.face_dir > 0 else back
            return l, self.y, l + w, self.y + h
        if name == 'burrow':
            return self.x - w / 2, self.y, self.x + w / 2, self.y + h   # 솟구치는 기둥
        return super().get_attack_bb()

    # ---------- 그리기 (도형) ----------

    def draw(self):
        if self.state == DORMANT:
            return   # 벽 속에 숨어 있다
        if self.is_underground():
            self.draw_burrow_warning()
            if self.dig_progress() >= 1:
                return
        super().draw()

    def draw_burrow_warning(self):
        # 솟구칠 자리에 균열 + 빨간 예고 (예고가 끝날수록 진해짐)
        spec = STATS['burrow']
        x, y = self.burrow_x, self.y
        half = spec['crack_w'] / 2
        a = self.attack
        left = self.state_timer + (a.windup if self.state == TELEGRAPH else 0)
        k = 1 - left / (a.telegraph + a.windup)
        effect.draw_alpha_rect(x - half, y, x + half, y + spec['hitbox'][1], config.COLOR_UNPARRYABLE,
                               config.MAGIC_CIRCLE['warn_alpha'] * k)
        step = spec['crack_w'] / 6
        for i in range(6):
            cx = x - half + step * (i + 0.5)
            hh = spec['crack_h'] * (1 if i % 2 else 0.5)
            camera.draw_rect(cx - 3, y, cx + 3, y + hh, *config.COLOR_BORER_CRACK, filled=True)

    def draw_body(self):
        if self.state == GROGGY:
            super().draw_body()   # 쓰러진 몸 + 약점 (boss_base) → draw_weapon에서 드러난 몸통
            return
        l, b, r, t = self.body_bb()
        f = self.face_dir
        sink = 0
        if self.is_underground():
            sink = self.h * self.dig_progress()   # 땅으로 파고드는 중
        crouch = self.attack is not None and self.attack.name in CHARGES and self.state == TELEGRAPH
        if crouch:
            # 몸을 뒤로 웅크림 (낮고 뒤로 물러난 모양)
            l, r = l - f * self.w * 0.08, r - f * self.w * 0.08
            t = b + self.h * 0.8
        t -= sink
        if t <= b:
            return
        color = self.body_color()
        camera.draw_rect(l, b, r, t, *color, filled=True)
        # 껍질 마디
        seg = (r - l) / STATS['segments']
        for i in range(1, STATS['segments']):
            sx = l + seg * i
            camera.draw_rect(sx - 2, b + (t - b) * 0.35, sx + 2, t, *config.COLOR_BORER_SHELL, filled=True)
        if self.phase >= 2:
            # 깨진 껍질 앞부분: 몸통이 드러남
            fl = r - seg if f > 0 else l
            camera.draw_rect(fl, b, fl + seg, b + (t - b) * 0.7, *config.COLOR_BORER_BELLY, filled=True)
        self.draw_cracks()
        self.draw_head(l, b, r, t, color)
        self.draw_tail(l, b, r, t, color)

    def draw_head(self, l, b, r, t, color):
        f = self.face_dir
        hw, hh = STATS['head_w'], min(STATS['head_h'], t - b)
        front = r if f > 0 else l
        raised = self.attack is not None and self.attack.name == 'rockfall' and self.state in (TELEGRAPH, WINDUP, ACTIVE)
        hb = t - hh / 2 if raised else b   # 낙석: 머리를 천장 쪽으로 치켜듦
        hl = front if f > 0 else front - hw
        camera.draw_rect(hl, hb, hl + hw, hb + hh, *color, filled=True)
        eye = hw / 4
        ex = hl + hw / 2 + f * eye
        camera.draw_rect(ex - eye / 2, hb + hh - eye * 2, ex + eye / 2, hb + hh - eye, *config.COLOR_TEXT, filled=True)

    def draw_tail(self, l, b, r, t, color):
        f = self.face_dir
        back = l if f > 0 else r
        length, th = STATS['tail_len'], STATS['tail_h']
        raised = self.attack is not None and self.attack.name == 'tail' and self.state in (TELEGRAPH, WINDUP)
        if raised:
            # 꼬리를 높이 듦
            camera.draw_rect(back - th / 2, t, back + th / 2, t + length, *color, filled=True)
        else:
            tl = back - length if f > 0 else back
            camera.draw_rect(tl, b, tl + length, b + th, *color, filled=True)

    def draw_weapon(self, l, b, r, t):
        # 그로기: 껍질이 벌어져 몸통이 드러난다 (boss_base.draw_groggy가 부름)
        if self.state == GROGGY:
            inset = (r - l) * 0.15
            camera.draw_rect(l + inset, b, r - inset, t, *config.COLOR_BORER_BELLY, filled=True)
