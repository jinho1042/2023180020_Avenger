import config
import game_framework
import game_world
from objects import effect, magic_circle
from objects.bosses.boss_base import GROGGY, BossBase
from objects.bosses.rockshell_borer import FallingRock
from objects.enemies.ruin_golem import GroundWave
from objects.enemy_base import ACTIVE, RECOVER, TELEGRAPH, WINDUP, Attack
from objects.platform import Platform
from systems import camera, sound

STATS = config.BOSS_COLOSSUS
FISTS = ('fist', 'combo', 'combo2')   # 주먹을 내려찍는 동작
STUCK = ('fist', 'combo2')            # 박힌 동안 팔이 발판이 되는 동작 (연타 첫 타는 금방 뽑는다)


def boxes_union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def draw_segment(x0, y0, x1, y1, thick, color):
    # 두 점 사이를 두께 thick의 사각형을 이어 그린다 (팔)
    steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / (thick / 2)))
    half = thick / 2
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i / steps
        y = y0 + (y1 - y0) * i / steps
        camera.draw_rect(x - half, y - half, x + half, y + half, *color, filled=True)


class TempleColossus(BossBase):
    # B4 신전 골렘 거상 — 가라앉은 수호상 (11.4). 2×1 아레나 가운데를 천천히 걷는 거대한 석상
    # 피해 부위는 머리 핵과 주먹뿐 (2페이즈부터 가슴 핵도). 몸통·다리는 회색 스파크 (피해 0, 자세 0)
    # 1~: 주먹 내려찍기(흰, 2칸, 박히면 팔이 발판) · 충격파(빨강) · 룬 광선(빨강, 2칸, 낮게/높게 번갈아) · 잔해 낙하(빨강)
    # 2페이즈(50%): 가슴판이 떨어져 가슴 핵 노출, 충격파 2 → 3줄, 양주먹 연타(흰) 추가
    # 그로기: 무릎을 꿇어 머리 핵이 내려온다 + 가슴 틈에서 공기 (boss_base)
    boss_key = 'colossus'

    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.arm = 1             # 지금 내려찍는 팔 (1 오른팔, -1 왼팔)
        self.fist_x = None       # 내려찍은 자리 (Active·Recover 동안). None이면 들고 있거나 쉬는 자리
        self.parried_stuck = False
        self.beam_high = False   # 다음 룬 광선 높이 (서 있는 높이부터 번갈아)
        self.beam_level = 'low'  # 이번 광선 높이
        self.waves_left = 0      # 이번 충격파에 남은 줄 수
        self.wave_timer = 0.0
        self.arm_platforms = []  # 박힌 팔 발판 (지형 목록에 잠깐 넣는다)
        self.build_patterns()

    def build_patterns(self):
        f, wv, bm, db = STATS['fist'], STATS['wave'], STATS['beam'], STATS['debris']
        heavy, dmg = STATS['heavy_damage'], STATS['damage']
        lines = self.wave_lines()
        self.patterns = dict(
            fist=[Attack('fist', True, f['telegraph'], f['windup'], f['active'], STATS['fist_stuck'], heavy, None)],
            wave=[Attack('wave', False, wv['telegraph'], wv['windup'], (lines - 1) * STATS['shockwave_gap'] + 0.05,
                         wv['recover'], dmg, None)],
            beam=[Attack('beam', False, STATS['beam_charge'], bm['windup'], bm['active'], bm['recover'], heavy, None)],
            debris=[Attack('debris', False, db['telegraph'], db['windup'], db['active'], db['recover'], dmg, None)],
            combo=[Attack('combo', True, f['telegraph'], f['windup'], f['active'], STATS['combo_stuck'], heavy, None),
                   Attack('combo2', True, STATS['combo_gap'], f['windup'], f['active'], STATS['combo_recover'],
                          heavy, None)])

    def wave_lines(self):
        return STATS['shockwave_lines'][min(self.phase, len(STATS['shockwave_lines'])) - 1]

    # ---------- 부위 ----------

    def torso_bb(self):
        half_w = self.w / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + self.h

    def head_bb(self):
        hw, hh = STATS['head']
        bottom = self.y + self.h - (STATS['groggy_head_drop'] if self.state == GROGGY else 0)
        return self.x - hw / 2, bottom, self.x + hw / 2, bottom + hh

    def chest_bb(self):
        cw, ch = STATS['chest']
        cy = self.y + self.h * STATS['chest_y']
        return self.x - cw / 2, cy - ch / 2, self.x + cw / 2, cy + ch / 2

    def fist_center(self, side):
        # 주먹 중심: 내려찍은 주먹은 그 자리 바닥, 드는 중이면 어깨 위, 아니면 몸 옆 아래
        fw, fh = STATS['fist_size']
        if side == self.arm and self.fist_x is not None:
            return self.fist_x, self.y + fh / 2
        rest_x = self.x + side * (self.w / 2 + fw / 2 + STATS['arm']['gap'])
        if side == self.arm and self.raising():
            return rest_x, self.y + self.h + fh / 2
        return rest_x, self.y + STATS['fist_rest_y'] + fh / 2

    def fist_bb(self, side):
        fw, fh = STATS['fist_size']
        cx, cy = self.fist_center(side)
        return cx - fw / 2, cy - fh / 2, cx + fw / 2, cy + fh / 2

    def raising(self):
        return self.attack is not None and self.attack.name in FISTS and self.state in (TELEGRAPH, WINDUP)

    def hurt_bbs(self):
        parts = [self.head_bb(), self.fist_bb(1), self.fist_bb(-1)]
        if self.phase >= 2:
            parts.append(self.chest_bb())
        return parts

    def armor_bbs(self):
        return [self.torso_bb()]

    def contact_bbs(self):
        return [self.torso_bb()]

    def get_bb(self):
        # 모든 부위를 감싼다 (반사탄 충돌 쌍·hitbox 표시용). 실제 판정은 부위별 (combat.struck_part)
        return boxes_union([self.torso_bb(), self.head_bb(), self.fist_bb(1), self.fist_bb(-1)])

    # ---------- 패턴 선택 · 이동 ----------

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        if self.attack_cooldown <= 0:
            name = self.pick_pattern(self.pattern_weights())
            if name:
                self.start_pattern(name)
                return
        if abs(self.player.x - self.x) > STATS['keep_range']:
            self.vx = self.face_dir * self.speed

    def pattern_weights(self):
        weights = dict(STATS['phase2_base'] if self.phase >= 2 else STATS['base'])
        if self.player.y >= self.y + STATS['head_height_y']:
            weights['beam'] = STATS['head_weight']   # 머리 높이에 있으면 룬 광선 (11.4 선택 규칙)
        return weights

    def start_pattern(self, name):
        cooldown = dict(wave=STATS['wave_cooldown'], debris=STATS['debris_cooldown']).get(name, 0)
        self.remember_pattern(name, cooldown)
        self.attack_queue = list(self.patterns[name])
        if name in ('fist', 'combo'):
            self.arm = 1 if self.player.x >= self.x else -1
        elif name == 'beam':
            self.beam_level = 'high' if self.beam_high else 'low'
            self.beam_high = not self.beam_high
        self.start_next_attack()

    def start_next_attack(self):
        if self.attack is not None and self.attack.name == 'combo':
            self.arm = -self.arm   # 양주먹 연타: 두 번째는 다른 팔
        self.fist_x = None
        self.parried_stuck = False
        super().start_next_attack()
        sound.play('door' if self.attack.name in FISTS else 'swing')   # 돌 갈리는 소리 / 휘두르는 소리

    # ---------- 진행 ----------

    def next_phase(self):
        prev = self.state
        super().next_phase()
        if self.attack is None:
            self.fist_x = None
            return
        name = self.attack.name
        if self.state == ACTIVE and prev == WINDUP:
            if name in FISTS:
                self.slam()
            elif name == 'wave':
                self.waves_left = self.wave_lines()
                self.wave_timer = 0.0
            elif name == 'debris':
                self.drop_debris()
            elif name == 'beam':
                camera.shake(*STATS['shake'])
                sound.play('door')

    def update_ai(self):
        # 충격파 줄은 Active가 끝나는 프레임보다 먼저 내보내서 마지막 줄이 빠지지 않게 한다
        if self.state == ACTIVE and self.attack is not None and self.attack.name == 'wave' and self.waves_left > 0:
            self.wave_timer -= game_framework.frame_time
            if self.wave_timer <= 0:
                self.waves_left -= 1
                self.wave_timer += STATS['shockwave_gap']
                self.release_waves()
        super().update_ai()

    def update(self):
        super().update()
        self.sync_arm_platforms()

    def cancel_attack(self):
        super().cancel_attack()
        self.fist_x = None
        self.waves_left = 0
        self.sync_arm_platforms()

    def on_parried(self):
        # 주먹을 패링당하면 비틀거리지 않고 주먹이 더 오래(fist_stuck_parried) 박힌다 (11.4). 남은 연타는 취소
        if self.add_posture(config.POSTURE_PARRY):
            return
        if self.attack is not None and self.attack.name in FISTS and self.fist_x is not None:
            self.attack_queue = []
            self.parried_stuck = True   # 연타 첫 타도 패링하면 팔을 발판으로 쓸 수 있다 (stuck)
            self.set_state(RECOVER, STATS['fist_stuck_parried'])
            return
        self.recoil()

    def slam(self):
        # 내려찍는 순간 플레이어 x를 겨눈다. 주먹이 닿는 거리(fist_reach)와 몸 바깥, 방 안으로 자른다
        fw = STATS['fist_size'][0]
        side = 1 if self.player.x >= self.x else -1
        if self.attack.name in ('fist', 'combo'):
            self.arm = side
        near = self.w / 2 + fw / 2 + STATS['arm']['gap']
        dx = min(STATS['fist_reach'], max(near, abs(self.player.x - self.x)))
        x = self.x + side * dx
        self.fist_x = min(max(x, fw / 2 + 40), game_world.room_w - fw / 2 - 40)
        effect.burst(self.fist_x, self.y, STATS['dust'], config.COLOR_ROCK)
        camera.shake(*STATS['shake'])
        sound.play('door')

    def release_waves(self):
        # 몸 양옆 바닥에서 한 줄씩 (빨강, 점프·디딤으로 넘김)
        for d in (-1, 1):
            x = self.x + d * (self.w / 2 + STATS['wave_w'] / 2)
            game_world.add_object(GroundWave(x, self.y, d, self.attack_damage(), self.player, self.platforms, STATS),
                                  config.DEPTH_MAP)
        effect.burst(self.x, self.y, STATS['dust'], config.COLOR_ROCK)
        camera.shake(*STATS['shake'])
        sound.play('door')

    def drop_debris(self):
        # 천장을 친 순간: debris_count개. 하나는 플레이어 발밑, 나머지는 아레나에 고르게
        spec, rock_w = STATS['debris'], config.BOSS_BORER['rockfall']['rock_w']
        count = STATS['debris_count']
        l, r = spec['margin'], game_world.room_w - spec['margin']
        xs = [l + (r - l) * (i + 0.5) / count for i in range(count)]
        i = min(range(count), key=lambda k: abs(xs[k] - self.player.x))
        xs[i] = min(max(self.player.x, rock_w / 2), game_world.room_w - rock_w / 2)
        for x in xs:
            ceiling = self.ceiling_above(x)
            floor = magic_circle.floor_below(x, ceiling - 1, [p for p in self.platforms if p.kind == 'solid'])
            game_world.add_object(FallingRock(x, floor, ceiling, self.attack_damage(), self.player), config.DEPTH_MAP)
        camera.shake(*STATS['shake'])
        sound.play('door')

    def ceiling_above(self, x):
        tops = [p.bottom for p in self.platforms
                if p.kind == 'solid' and p.left <= x <= p.right and p.bottom >= self.y + self.h]
        return min(tops) if tops else game_world.room_h

    # ---------- 팔 발판 (아레나 기믹) ----------

    def stuck(self):
        return (self.state == RECOVER and self.attack is not None and self.fist_x is not None
                and (self.attack.name in STUCK or self.parried_stuck))

    def arm_spans(self):
        # 박힌 팔: 몸 옆(gap)에서 주먹 안쪽 끝까지를 반으로 나눠 아래팔(낮음, 주먹 쪽) · 위팔(높음, 몸 쪽)
        # 반환: [(왼쪽, 오른쪽, 윗면 높이)]. 팔이 짧으면 위팔 하나만
        arm, fw = STATS['arm'], STATS['fist_size'][0]
        side = 1 if self.fist_x >= self.x else -1
        inner = self.x + side * (self.w / 2 + arm['gap'])
        outer = self.fist_x - side * fw / 2
        length = (outer - inner) * side
        if length <= 0:
            return []
        if length < fw * 1.5:
            return [(min(inner, outer), max(inner, outer), self.y + arm['upper_h'])]
        mid = (inner + outer) / 2
        return [(min(mid, outer), max(mid, outer), self.y + arm['fore_h']),
                (min(inner, mid), max(inner, mid), self.y + arm['upper_h'])]

    def sync_arm_platforms(self):
        # 주먹이 박혀 있는 동안만 팔 발판을 지형 목록에 둔다 (플레이어와 같은 목록. 방을 다시 불러오면 새로 만들어진다)
        want = self.stuck() and self.is_alive()
        if want and not self.arm_platforms:
            thick = STATS['arm']['thick']
            self.arm_platforms = [Platform(l, top - thick, r - l, thick, 'oneway') for l, r, top in self.arm_spans()]
            self.platforms.extend(self.arm_platforms)
        elif not want and self.arm_platforms:
            for p in self.arm_platforms:
                if p in self.platforms:
                    self.platforms.remove(p)
            self.arm_platforms = []

    # ---------- 판정 ----------

    def get_attack_bb(self):
        if self.state != ACTIVE or self.attack is None:
            return None
        name = self.attack.name
        if name in FISTS and self.fist_x is not None:
            w, h = STATS['fist']['hitbox']
            return self.fist_x - w / 2, self.y, self.fist_x + w / 2, self.y + h
        if name == 'beam':
            return self.beam_bb()
        return None

    def beam_bb(self):
        # 바라보는 쪽 몸 끝에서 방 끝까지 수평 광선
        low, h = STATS['beam'][self.beam_level]
        b = self.y + low
        if self.face_dir > 0:
            return self.x + self.w / 2, b, game_world.room_w, b + h
        return 0, b, self.x - self.w / 2, b + h

    # ---------- 페이즈 · 처치 ----------

    def on_phase(self, phase):
        # 2페이즈: 가슴판이 떨어져 가슴 핵이 드러나고 몸 색이 바뀐다. 충격파 줄 수·연타는 패턴표가 정한다
        self.color = STATS['color_phase2']
        cx, cy = self.x, self.y + self.h * STATS['chest_y']
        effect.burst(cx, cy, STATS['plate_fall'], config.COLOR_COLOSSUS_PLATE)
        self.build_patterns()

    def die(self):
        super().die()
        self.sync_arm_platforms()

    # ---------- 그리기 (도형) ----------

    def draw_body(self):
        groggy = self.state == GROGGY
        l, b, r, t = self.torso_bb()
        color = self.body_color()
        if groggy:
            # 무릎을 꿇음: 다리를 접어 몸통이 낮아진다 (판정은 그대로)
            t = b + self.h * config.GROGGY_SQUASH
        camera.draw_rect(l, b, r, t, *color, filled=True)
        self.draw_chest(l, b, r, t)
        self.draw_head()
        for side in (-1, 1):
            self.draw_arm(side, t)
        if not groggy:
            self.draw_torso_cracks()
        if self.state == TELEGRAPH and self.attack is not None and not self.attack.parryable:
            # 패링 불가 예고: 머리 위 '!'
            hl, hb, hr, ht = self.head_bb()
            e = self.w / 16
            camera.draw_rect(self.x - e / 2, ht + e * 2, self.x + e / 2, ht + e * 5, *config.COLOR_UNPARRYABLE, filled=True)
            camera.draw_rect(self.x - e / 2, ht + e / 2, self.x + e / 2, ht + e * 1.5, *config.COLOR_UNPARRYABLE,
                             filled=True)
        self.draw_beam_warning()

    def draw_chest(self, l, b, r, t):
        cl, cb, cr, ct = self.chest_bb()
        if self.phase >= 2 or self.state == GROGGY:
            # 드러난 가슴 핵 (그로기 중에는 가슴 틈에서 공기가 뿜어져 나온다, boss_base)
            camera.draw_rect(cl, cb, cr, ct, *config.COLOR_COLOSSUS_CORE, filled=True)
        else:
            pad = STATS['chest'][0] * 0.4
            camera.draw_rect(cl - pad, cb - pad / 2, cr + pad, ct + pad / 2, *config.COLOR_COLOSSUS_PLATE, filled=True)

    def draw_head(self):
        l, b, r, t = self.head_bb()
        camera.draw_rect(l, b, r, t, *self.body_color(), filled=True)
        # 머리 핵 (이마) + 눈. 룬 광선 예고 중에는 눈이 빨갛게 충전된다
        core = (r - l) * 0.3
        camera.draw_rect(self.x - core / 2, t - core, self.x + core / 2, t - core * 0.2, *config.COLOR_COLOSSUS_CORE,
                         filled=True)
        charging = self.attack is not None and self.attack.name == 'beam' and self.state in (TELEGRAPH, WINDUP, ACTIVE)
        eye = (r - l) * 0.14
        ex = self.x + self.face_dir * (r - l) * 0.25
        ey = b + (t - b) * 0.4
        color = config.COLOR_UNPARRYABLE if charging else config.COLOR_COLOSSUS_CORE
        camera.draw_rect(ex - eye / 2, ey - eye / 2, ex + eye / 2, ey + eye / 2, *color, filled=True)

    def draw_arm(self, side, shoulder_top):
        fw, fh = STATS['fist_size']
        thick = STATS['arm']['thick'] * 1.6
        sx = self.x + side * self.w / 2
        sy = shoulder_top - thick
        cx, cy = self.fist_center(side)
        if side == self.arm and self.stuck():
            # 박힌 팔: 발판 모양 그대로 (위팔 → 아래팔 → 주먹)
            for l, r, top in self.arm_spans():
                camera.draw_rect(l, top - STATS['arm']['thick'], r, top, *config.COLOR_COLOSSUS_FIST, filled=True)
        else:
            draw_segment(sx, sy, cx, cy, thick, config.COLOR_COLOSSUS_FIST)
        l, b, r, t = self.fist_bb(side)
        color = config.COLOR_COLOSSUS_FIST
        if side == self.arm and self.raising():
            # 주먹 내려찍기 예고: 들어 올린 주먹에 빛 (흰)
            color = (config.COLOR_PARRYABLE if self.state == TELEGRAPH
                     and int(self.state_timer / config.TELEGRAPH_BLINK) % 2 == 0 else config.COLOR_ENEMY_WINDUP)
        camera.draw_rect(l, b, r, t, *color, filled=True)

    def draw_beam_warning(self):
        # 룬 광선 예고: 그 높이에 가는 빨간 선 (beam_charge)
        if not (self.attack is not None and self.attack.name == 'beam' and self.state in (TELEGRAPH, WINDUP)):
            return
        l, b, r, t = self.beam_bb()
        mid = (b + t) / 2
        half = STATS['beam']['line_h'] / 2
        camera.draw_rect(l, mid - half, r, mid + half, *config.COLOR_UNPARRYABLE, filled=True)

    def draw_torso_cracks(self):
        # 외형 단계 (66%·33%, 원칙 12): 몸통에만 균열
        stage = self.damage_stage()
        if stage <= 0:
            return
        l, b, r, t = self.torso_bb()
        w, h = r - l, t - b
        lines = [[(l + w * 0.2, t), (l + w * 0.45, b + h * 0.7), (l + w * 0.3, b + h * 0.45)],
                 [(r, b + h * 0.35), (l + w * 0.65, b + h * 0.5), (l + w * 0.75, b + h * 0.85)]]
        for points in lines[:stage]:
            self.draw_crack(points)

    def draw_weapon(self, l, b, r, t):
        pass
