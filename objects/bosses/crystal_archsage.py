import math

import config
import game_framework
from objects import effect, magic_circle, projectile
from objects.bosses.boss_base import GROGGY, BossBase
from objects.enemies.crystal_sage import blink_away, fit_x
from objects.enemies.crystal_sprite import CrystalSprite
from objects.enemy_base import ACTIVE, TELEGRAPH, WINDUP, Attack
from systems import camera, sound

STATS = config.BOSS_ARCHSAGE


class CrystalArchsage(BossBase):
    # B3 수정 대술사 — 결정이 된 학자 (11.4, ← v2 대마법사). 거리를 벌리고 투사체로 압박한다. 반사가 가장 큰 딜 수단
    # 1~: 수정탄 연사(흰) · 대형 마력구(흰, 반사하면 × orb_reflect_mult) · 결정 폭격(빨강 마법진) · 유생 소환(흰 번쩍임)
    #     순간이동(공격 아님): 플레이어가 가까우면 반대쪽 공중 발판 위로. 사라지는·나타나는 자리에 결정 파편
    # 2페이즈(50%): 결정 갑옷이 깨짐, 연사 5 → 7발, 순간이동 직후 바로 연사
    # 근접 공격이 없으므로 자세는 반사탄(+POSTURE_REFLECT)과 곡괭이·룬 기술 적중으로 쌓인다
    boss_key = 'archsage'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.perches = [p for p in platforms if p.kind == 'oneway']   # 순간이동 착지점 (아레나 공중 발판)
        self.perched = False    # 공중 발판 위에 있으면 걷지 않는다
        self.casts_left = 0     # 이번 Active에 남은 시전 횟수 (연사·폭격)
        self.cast_timer = 0.0   # 다음 시전까지 남은 시간
        self.cast_interval = 0.0
        self.blink_cooldown = 0.0
        self.build_patterns()

    def build_patterns(self):
        v, o, c, s = STATS['volley'], STATS['orb'], STATS['barrage'], STATS['summon']
        volley_time = self.volley_count() * STATS['volley_interval']
        self.patterns = dict(
            volley=Attack('volley', True, v['telegraph'], v['windup'], volley_time, v['recover'], STATS['damage'], None),
            orb=Attack('orb', True, o['telegraph'], o['windup'], o['active'], o['recover'], STATS['orb_damage'], None),
            barrage=Attack('barrage', False, c['telegraph'], c['windup'],
                           STATS['circle_count'] * STATS['circle_interval'], c['recover'], STATS['circle_damage'], None),
            summon=Attack('summon', True, s['telegraph'], s['windup'], s['active'], s['recover'], 0, None))

    def volley_count(self):
        return STATS['volley_count'][min(self.phase, len(STATS['volley_count'])) - 1]

    def update(self):
        self.blink_cooldown = max(0, self.blink_cooldown - game_framework.frame_time)
        super().update()

    # ---------- 패턴 선택 · 이동 ----------

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        dist = abs(self.player.x - self.x)
        if self.blink_cooldown <= 0 and dist <= STATS['blink_trigger_dist']:
            self.teleport()
            if self.phase >= 2:
                # 2페이즈: 나타나자마자 수정탄 연사
                self.start_pattern('volley')
                return
            dist = abs(self.player.x - self.x)
        self.face_player()
        if self.attack_cooldown <= 0:
            name = self.pick_pattern(self.pattern_weights(dist))
            if name:
                self.start_pattern(name)
                return
        if self.perched:
            return
        # 땅에서는 keep_distance를 유지한다 (가까우면 바라본 채 뒷걸음질)
        if dist < STATS['keep_distance'] - STATS['distance_tolerance']:
            self.vx = -self.face_dir * self.speed
        elif dist > STATS['keep_distance'] + STATS['distance_tolerance']:
            self.vx = self.face_dir * self.speed

    def pattern_weights(self, dist):
        weights = dict(STATS['near'] if dist <= STATS['near_range'] else STATS['far'])
        if len(self.alive_summons()) >= STATS['summon_max']:
            weights['summon'] = 0
        return weights

    def start_pattern(self, name):
        self.remember_pattern(name, STATS['summon_cooldown'] if name == 'summon' else 0)
        self.attack_queue = [self.patterns[name]]
        self.start_next_attack()

    def teleport(self):
        # 플레이어에게서 가로 blink_dist 이상 떨어진 공중 발판 위로 (여럿이면 가장 먼 곳, 없으면 가장 먼 발판)
        # 공중 발판이 없는 방(테스트 방 등)이면 v2처럼 뒤로 blink_dist
        self.blink_cooldown = STATS['blink_cooldown']
        if not self.perches:
            blink_away(self, STATS['blink_dist'])
            return
        spot = max(self.perches, key=lambda p: abs((p.left + p.right) / 2 - self.player.x))
        self.shatter(self.x, self.y + self.h / 2)
        self.x = fit_x(self, (spot.left + spot.right) / 2)
        self.y = spot.top
        self.vx = self.vy = 0
        self.perched = True
        self.face_player()
        self.shatter(self.x, self.y + self.h / 2)
        sound.play('dash')

    def shatter(self, x, y):
        effect.burst(x, y, STATS['shards'], config.COLOR_ARCHSAGE_ARMOR)

    # ---------- 시전 ----------

    def next_phase(self):
        super().next_phase()
        if self.state != ACTIVE or self.attack is None:
            return
        name = self.attack.name
        if name == 'volley':
            self.start_casts(self.volley_count(), STATS['volley_interval'])
        elif name == 'barrage':
            self.start_casts(STATS['circle_count'], STATS['circle_interval'])
        elif name == 'orb':
            self.fire(STATS['orb_speed'], config.MAGE_ORB)
        elif name == 'summon':
            self.summon()

    def start_casts(self, count, interval):
        # 첫 시전은 Active 시작 직후, 이후 interval마다
        self.casts_left = count
        self.cast_timer = 0.0
        self.cast_interval = interval

    def update_ai(self):
        # 시전은 Active가 끝나는 프레임보다 먼저 처리해서 마지막 1회가 빠지지 않게 한다
        if self.state == ACTIVE and self.casts_left > 0:
            self.cast_timer -= game_framework.frame_time
            if self.cast_timer <= 0:
                self.casts_left -= 1
                self.cast_timer += self.cast_interval
                if self.attack.name == 'volley':
                    self.fire(STATS['bolt_speed'], config.BOSS_BOLT)
                else:
                    magic_circle.cast(self.player.x, self.player.y, STATS['circle_radius'], STATS['circle_delay'],
                                      self.attack_damage(), self.player, self.platforms)
        super().update_ai()

    def cancel_attack(self):
        super().cancel_attack()
        self.casts_left = 0

    def orb_pos(self):
        # 지팡이 끝 구슬 (투사체가 나가는 자리)
        return self.x + self.face_dir * self.w * 3 / 4, self.y + self.h * 3 / 4

    def fire(self, speed, spec):
        # 쏘는 순간 플레이어 몸 중심을 조준한다
        x, y = self.orb_pos()
        angle = math.atan2(self.player.y + config.PLAYER_H / 2 - y, self.player.x - x)
        projectile.fire(x, y, math.cos(angle), math.sin(angle), speed, self.attack_damage(),
                        self.attack.parryable, self.platforms, spec, owner=self)

    def summon(self):
        # 비어 있는 자리만큼 보스 양옆에 수정 유생을 불러낸다 (일반 적이라 패링 숨 제한이 있다, 8.4)
        count = STATS['summon_max'] - len(self.alive_summons())
        for i in range(count):
            side = 1 if i % 2 == 0 else -1
            x = fit_x(self, self.x + side * STATS['summon_offset'])
            sprite = CrystalSprite(x, self.y, self.player, self.platforms)
            sprite.ore = STATS['summon_ore']   # 소환물로 광석을 벌 수 없게
            self.summons.append(sprite)
            self.new_summons.append(sprite)
            effect.burst(x, self.y + sprite.h / 2, config.TELEPORT_PUFF, sprite.color)

    # ---------- 페이즈 ----------

    def on_phase(self, phase):
        # 2페이즈: 결정 갑옷이 깨져 조각이 튀고 몸 색이 바뀐다. 연사 발수는 volley_count가 페이즈로 정한다
        self.color = STATS['color_phase2']
        effect.burst(self.x, self.y + self.h / 2, STATS['armor_break'], config.COLOR_ARCHSAGE_ARMOR)
        self.build_patterns()

    # ---------- 그리기 (도형) ----------

    def pattern_pose(self, *names):
        return self.attack is not None and self.attack.name in names and self.state in (TELEGRAPH, WINDUP)

    def draw_body(self):
        if self.state == GROGGY:
            super().draw_body()
            return
        super().draw_body()
        if self.phase == 1:
            self.draw_armor()

    def draw_armor(self):
        # 1페이즈 결정 갑옷: 어깨 위로 솟은 결정 조각 (2페이즈 전환 때 깨진다)
        l, b, r, t = self.get_bb()
        n, size = STATS['armor_plates'], STATS['armor_size']
        for i in range(n):
            x = l + (r - l) * (i + 0.5) / n
            h = size * (1.5 if i == n // 2 else 1)
            camera.draw_rect(x - size / 3, t - size / 2, x + size / 3, t + h, *config.COLOR_ARCHSAGE_ARMOR, filled=True)

    def draw_weapon(self, l, b, r, t):
        # 지팡이 + 끝의 구슬. 패턴마다 자세가 다르다 (원칙 1)
        #   연사: 지팡이를 앞으로 겨눔 · 마력구: 두 손 앞에서 구체가 커짐 · 폭격: 지팡이를 땅에 꽂음(빨강) · 소환: 머리 위로 들어올림
        thick = self.w / 8
        f = self.face_dir
        if self.pattern_pose('barrage') or (self.attack is not None and self.attack.name == 'barrage'
                                            and self.state == ACTIVE):
            sx = self.x + f * self.w * 0.7
            camera.draw_rect(sx - thick / 2, b - thick, sx + thick / 2, t, *config.COLOR_STAFF, filled=True)
            effect.draw_disc(sx, b, thick * 1.5, config.COLOR_UNPARRYABLE)
            return
        if self.pattern_pose('summon'):
            sx = self.x + f * self.w / 4
            camera.draw_rect(sx - thick / 2, t - self.h / 4, sx + thick / 2, t + self.h / 2, *config.COLOR_STAFF, filled=True)
            effect.draw_disc(sx, t + self.h / 2, thick * 1.5, config.COLOR_ENEMY_WINDUP)
            return
        if self.pattern_pose('volley') or (self.attack is not None and self.attack.name == 'volley'
                                           and self.state == ACTIVE):
            ox, oy = self.orb_pos()
            ex = self.x + f * self.w / 2
            camera.draw_rect(min(ex, ox), oy - thick / 2, max(ex, ox), oy + thick / 2, *config.COLOR_STAFF, filled=True)
            effect.draw_disc(ox, oy, config.BOSS_BOLT['size'] / 2, config.COLOR_ENEMY_WINDUP
                             if self.state != ACTIVE else config.COLOR_BOSS_STAFF_ORB)
            return
        ox, oy = self.orb_pos()
        camera.draw_rect(ox - thick / 2, b, ox + thick / 2, oy, *config.COLOR_STAFF, filled=True)
        if self.pattern_pose('orb'):
            a = self.attack
            left = self.state_timer + (a.windup if self.state == TELEGRAPH else 0)
            k = min(1, max(0, 1 - left / (a.telegraph + a.windup)))
            radius = thick + (config.MAGE_ORB['size'] / 2 - thick) * k
            effect.draw_disc(ox, oy, radius, config.MAGE_ORB['color'])
        else:
            effect.draw_disc(ox, oy, thick, config.COLOR_BOSS_STAFF_ORB)
