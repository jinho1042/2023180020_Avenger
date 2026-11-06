import math

from pico2d import *

import config
import game_framework
import game_world
from objects import effect, projectile
from systems import breath, camera, engravings, input, runes, sound, terrain

# 동작 시작 순서: 패링 → 대시 → 룬 기술 → 점프 → 공격 (같은 프레임에 버퍼에 있으면 이 순서로 처리)
# 입력은 handle_event에서 systems/input.py에 저장만 하고, 실제 동작은 update에서 버퍼를 꺼내 시작한다 (6.3 입력 버퍼)


def fall_motion(vy, t, wet=False):
    # 중력 가속을 t초 동안 정확히 적분한다 (프레임률과 상관없이 같은 궤적). 최대 낙하 속도에서 멈춘다
    # wet = 물 안 (6.4): 중력 × WATER_GRAVITY_MULT, 최대 낙하 속도 WATER_MAX_FALL_SPEED
    # 반환: (이동 거리, 새 vy)
    g, v_max = config.GRAVITY, config.MAX_FALL_SPEED
    if wet:
        g, v_max = g * config.WATER_GRAVITY_MULT, config.WATER_MAX_FALL_SPEED
    if vy <= v_max:
        return v_max * t, v_max
    t_cap = (v_max - vy) / g
    if t <= t_cap:
        return vy * t + 0.5 * g * t * t, vy + g * t
    return vy * t_cap + 0.5 * g * t_cap * t_cap + v_max * (t - t_cap), v_max


class Player:
    def __init__(self, platforms, start):
        # x, y는 발 중심 좌표
        self.x, self.y = start
        self.vx, self.vy = 0.0, 0.0
        self.face_dir = 1
        self.on_ground = False
        # 점프 (6.4): jump_rising인 동안 '누르는 만큼 상승' 처리. jump_elapsed는 점프 시작부터 지난 시간
        self.jump_rising = False
        self.jump_elapsed = 0.0
        self.coyote_timer = 0.0
        self.jumps_left = 0  # 공중 추가 점프(결정 디딤) 남은 횟수. 땅·벽·포고에서 max_jumps - 1로 채운다
        # ↓+Z 내려가기: drop_timer 동안 drop_platforms(밟고 있던 one-way 발판)에 서지 않는다
        self.drop_platforms = []
        self.drop_timer = 0.0
        # 강착지: 내려가는 동안 fall_time을 세고, 길면 착지 후 hard_land_timer 동안 입력 잠금
        self.fall_time = 0.0
        self.hard_land_timer = 0.0
        # 대시: dash_timer > 0인 동안 대시 중(중력 무시), 쿨타임은 대시 시작부터 센다. 공중에서는 1회
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.dash_dir = 1
        self.air_dash_used = False
        # 벽 매달리기 (WallSlide, 버팀의 룬, 6.4): wall_dir = 매달린 벽 쪽 (-1 왼쪽, 1 오른쪽, 0 아님)
        # 벽점프 (WallJump): wall_jump_lock 동안 수평 입력을 무시하고 wall_jump_dir 쪽으로 밀려난다
        self.wall_dir = 0
        self.wall_jump_lock = 0.0
        self.wall_jump_dir = 0
        self.wall_spark_timer = 0.0
        # 곡괭이 공격 (6.5): 단타. attack_active > 0인 동안 hitbox, attack_cooldown이 끝나야 다음 공격
        self.attack_dir = 'side'   # 'side' | 'up' | 'down'
        self.attack_active = 0.0
        self.attack_cooldown = 0.0
        self.swing_alt = False     # 옆 공격 모션 두 가지를 번갈아 (판정은 같음)
        self.swing_count = 0
        self.swing_landed = False  # 이번 휘두름이 무언가를 맞혔는가 (반동·포고는 휘두름당 1번)
        self.swing_strong = False  # 이번 휘두름이 세 번째 일격인가
        self.attack_hits = set()   # 이번 휘두름에 이미 맞힌 대상 (한 번 휘두름에 한 번만 피해)
        self.pickaxe_lv = 1
        # 반동: 옆 공격 적중 시 recoil_timer 동안 recoil_dir 쪽으로 ATTACK_RECOIL만큼 밀린다
        self.recoil_timer = 0.0
        self.recoil_dir = 0
        # 세 번째 일격 (각인, 8.4): 적중 사이 간격이 interval 이하인 연속 3번째 적중. 연속 적중 수는 항상 센다
        self.strike_chain = 0
        self.since_last_strike = math.inf
        # 패링: parry_timer > 0인 동안 판정 중. 아무것도 못 막고 끝나면 parry_stun_timer 동안 경직
        # 쿨타임은 패링 시작부터 세고, 성공하면 즉시 0
        self.parry_timer = 0.0
        self.parry_success = False
        self.parry_cooldown = 0.0
        self.parry_stun_timer = 0.0
        self.parry_count = 0  # 결과 화면 통계
        # 숨 고르기 (Mend, 6.7): mend_timer > 0인 동안 이동 불가, 끝나면 숨을 내고 1칸 회복
        # mend_wait = 시작하지 못했거나 끊긴 뒤 A를 뗄 때까지 다시 시작하지 않음
        self.mend_timer = 0.0
        self.mend_time = 0.0
        self.mend_wait = False
        # 숨 게이트 기절 (Blackout, 7.3): 입력 잠금·무적. 시작·끝은 systems/breath.py가 정한다
        self.blackout = False
        # 컷신 (Cutscene, 2.2 추락): 입력 잠금·무적, 중력만 받는다. 시작·끝은 systems/script.py가 정한다
        self.cutscene = False
        # 체력이 이 아래로 내려가지 않는다. 광산(R0)은 사망이 없어 1 (13.6, script.py가 방마다 정함)
        self.min_hp = 0
        # 피격: hit_timer > 0인 동안 경직(조작 불가, 밀려남), 무적은 invincible_timer로 따로 센다
        # 체력은 칸 단위 정수 (6.7)
        self.hp = config.HP_START
        self.hit_timer = 0.0
        self.hit_dir = 1
        self.invincible_timer = 0.0
        self.dead = False
        # 환경 피해 → 안전 지점 (6.8). hazard_timer > 0인 동안 HazardRespawn (어두워짐 → 이동 → 밝아짐)
        self.hazard_timer = 0.0
        self.hazard_warped = False
        self.safe_points = []        # 방 JSON의 safe_points
        self.safe_point = None       # safe_points 중 마지막으로 밟은 곳
        self.ground_spot = start     # 마지막으로 SAFE_GROUND_TIME 이상 서 있던 바닥
        self.ground_time = 0.0
        # 안전지대 의자에 앉음 (13.1): 움직이지 않고, ←·→·Z로 일어난다. 앉기는 play_mode가 sit()으로
        self.sitting = False
        # 충돌을 검사할 지형 목록
        self.platforms = platforms
        self.max_hp = config.HP_START
        # 룬·플래그를 담은 월드 상태 (play_mode가 넣어 준다). can()·rune_lv()가 유일한 확인 창구
        self.world_state = None
        self.swing_mult = 1.0  # 이번 한 번 휘두름의 추가 배율 (engravings.on_attack_start가 정함)
        self.dash_strike_timer = 0.0   # 「질풍 일격」: 대시가 끝난 뒤 남은 시간 (> 0이면 첫 공격 강화)
        # 룬 기술 (A 짧게, 8.2): cast_timer > 0인 동안 Cast (공중에 멈춤, 피격 시 취소)
        # 낙반(↓+A, 굴착 Lv2): Cast가 끝나면 숨을 내고 rockfall = True로 무적 낙하. 착지하면 shockwave를 한 번 남긴다
        # 결정 화살(그냥 A, 결정 Lv2): Cast가 끝나면 숨을 내고 바라보는 방향으로 화살 (T52)
        self.cast_timer = 0.0
        self.cast_skill = None       # 'rockfall' | 'arrow'
        self.rockfall = False
        self.rockfall_hits = set()   # 이번 낙하에 몸으로 이미 맞힌 적 (한 번 낙하에 한 번만 피해)
        self.shockwave = None        # 착지 충격파 판정 (l, b, r, t). combat이 한 번 꺼내 쓴다
        # 물 (6.4, T53): 지금 방의 water 영역 (x, y, w, h)과 이번 프레임에 몸 중심이 물 안인지
        # 배율은 wet일 때만 곱해 쓰고 값에 누적해 대입하지 않는다 (16장 '물 안 이동')
        self.water = []
        self.wet = False

    # ---------- 각인으로 바뀌는 수치 (8.4): 매번 기본값 × 장착 각인으로 계산 (누적 대입 없음) ----------

    @property
    def parry_window(self):
        return engravings.parry_window()

    @property
    def invincible_on_hit(self):
        return engravings.invincible_on_hit()

    @property
    def reflect_damage_mult(self):
        return engravings.reflect_mult()

    @property
    def dash_dist(self):
        # 기본값 × 각인(「긴 질주」) × 굴착 Lv3 (8.2)
        dist = engravings.dash_dist()
        if self.can('hard_soil'):
            dist *= config.RUNE_LV_EFFECT['burrow_lv3_dash_mult']
        return dist

    @property
    def max_jumps(self):
        # 땅 점프 1 + 결정 디딤 (결정 Lv1~2 1회, Lv3 crystal_lv3_steps회, 6.4)
        if self.can('crystal_step2'):
            return 1 + config.RUNE_LV_EFFECT['crystal_lv3_steps']
        return 2 if self.can('crystal_step') else 1

    @property
    def dash_cooldown_time(self):
        return engravings.dash_cooldown()

    def enter_room(self, platforms, start, safe_points=(), water=()):
        # 다음 방으로 옮길 때 위치·속도·지형만 바꾸고 체력 등 런 상태는 유지한다
        self.x, self.y = start
        self.water = [tuple(w[:4]) for w in water]
        self.wet = self.in_water()
        self.safe_points = list(safe_points)
        self.safe_point = None
        self.ground_spot = start
        self.ground_time = 0.0
        self.hazard_timer = 0.0
        self.sitting = False
        self.vx, self.vy = 0.0, 0.0
        self.on_ground = False
        self.jump_rising = False
        self.fall_time = 0.0
        self.hard_land_timer = 0.0
        self.dash_timer = 0.0
        self.recoil_timer = 0.0
        self.attack_active = 0.0
        self.hit_timer = 0.0
        self.wall_dir = 0
        self.wall_jump_lock = 0.0
        self.drop_platforms = []
        self.drop_timer = 0.0
        self.end_skill()
        self.platforms = platforms

    def clear_input(self):
        input.clear()

    def handle_event(self, e):
        input.handle_event(e)

    # ---------- 상태 조회 ----------

    def can(self, ability):
        # 'dash', 'reflect' 등 능력 해금 여부 (6.2)
        return runes.can(self.world_state, ability)

    def rune_lv(self, rune):
        return runes.rune_lv(self.world_state, rune)

    def in_water(self):
        # 몸 중심이 water 영역 안인가 (6.4)
        cx, cy = self.x, self.y + config.PLAYER_H / 2
        return any(x <= cx <= x + w and y <= cy <= y + h for x, y, w, h in self.water)

    @property
    def water_speed_mult(self):
        # 물 안이면 좌우 속도·대시 거리 × WATER_SPEED_MULT (6.4)
        return config.WATER_SPEED_MULT if self.wet else 1.0

    def is_dashing(self):
        return self.dash_timer > 0

    def is_invincible(self):
        # 낙반 낙하 중 무적 (8.2)
        return ((self.is_dashing() and config.DASH_INVINCIBLE) or self.invincible_timer > 0 or self.dead
                or self.is_hazard_respawning() or self.blackout or self.cutscene or self.rockfall)

    def is_hazard_respawning(self):
        return self.hazard_timer > 0

    def is_hit(self):
        return self.hit_timer > 0

    def is_parrying(self):
        # 6장의 parry_active
        return self.parry_timer > 0

    def is_parry_stunned(self):
        return self.parry_stun_timer > 0

    def is_mending(self):
        return self.mend_timer > 0

    def is_hard_landing(self):
        return self.hard_land_timer > 0

    def is_wall_sliding(self):
        return self.wall_dir != 0

    def is_casting(self):
        return self.cast_timer > 0

    def is_skill_active(self):
        # Cast 또는 낙반 낙하 중
        return self.is_casting() or self.rockfall

    def is_attacking(self):
        # 공격 hitbox가 살아 있는 동안 (공격은 이동을 막지 않는다)
        return self.attack_active > 0

    def is_locked(self):
        # 새 동작을 시작할 수 없는 상태. 패링은 캔슬 불가 (6.3)
        return (self.dead or self.is_hit() or self.is_parrying() or self.is_parry_stunned()
                or self.is_hard_landing() or self.is_hazard_respawning() or self.sitting
                or self.is_mending() or self.blackout or self.cutscene or self.is_skill_active())

    # ---------- 동작 시작 ----------

    def handle_actions(self):
        # 버퍼에 남은 입력을 가능한 것부터 꺼내 쓴다. 지금 못 하면 버퍼 시간 동안 남겨 둔다
        if self.is_locked():
            return
        if input.buffered('parry') and self.can_parry():
            input.consume('parry')
            self.start_parry()
            return
        if input.buffered('dash') and self.can_dash():
            input.consume('dash')
            self.start_dash()
        if self.is_dashing():
            return  # 대시는 점프·공격으로 캔슬되지 않는다
        if input.buffered('rune_tap'):
            # A 짧게: ↓+A = 낙반, 그냥 A = 결정 화살. 해금 전·숨 부족이면 아무 반응 없이 버린다 (6.1)
            input.consume('rune_tap')
            skill = 'rockfall' if input.pressed('down') else 'arrow'
            if self.can_skill(skill):
                self.start_cast(skill)
                return
        if input.buffered('jump') and self.can_drop():
            input.consume('jump')
            self.start_drop()
        elif input.buffered('jump') and self.is_wall_sliding() and not self.on_ground:
            input.consume('jump')
            self.start_wall_jump()
        elif input.buffered('jump') and self.can_jump():
            input.consume('jump')
            self.start_jump()
        if input.buffered('attack') and self.attack_cooldown <= 0:
            input.consume('attack')
            self.start_attack()

    def can_parry(self):
        return self.parry_cooldown <= 0 and not self.is_dashing()

    def start_parry(self):
        self.parry_timer = self.parry_window
        self.parry_success = False
        self.parry_cooldown = config.PARRY_COOLDOWN
        self.attack_active = 0  # 공격 캔슬
        move = input.axis_x()
        if move != 0:
            self.face_dir = move

    def can_dash(self):
        # 굴착의 룬이 없으면 C는 아무 반응도 하지 않는다 (6.1)
        return (self.can('dash') and not self.is_dashing() and self.dash_cooldown <= 0
                and (self.on_ground or not self.air_dash_used))

    def start_dash(self):
        # 방향키를 누르고 있으면 그쪽으로, 아니면 바라보는 방향으로
        move = input.axis_x()
        self.dash_dir = move if move != 0 else self.face_dir
        self.face_dir = self.dash_dir
        self.dash_timer = config.DASH_TIME
        self.dash_cooldown = self.dash_cooldown_time
        if not self.on_ground:
            self.air_dash_used = True
        self.vy = 0
        self.jump_rising = False
        self.fall_time = 0.0  # 대시는 체공 시간 리셋 (강착지)
        self.attack_active = 0  # 공격 캔슬
        sound.play('dash')

    def can_skill(self, skill):
        ability = 'rockfall' if skill == 'rockfall' else 'crystal_arrow'
        return self.can(ability) and (breath.infinite or breath.value >= config.SKILL_BREATH_COST)

    def start_cast(self, skill):
        # Cast (8.2): SKILL_CAST_TIME 동안 그 자리에 멈춘다. 공격·매달리기는 끊는다
        self.cast_skill = skill
        self.cast_timer = config.SKILL_CAST_TIME
        self.attack_active = 0
        self.jump_rising = False
        self.wall_dir = 0
        self.vx, self.vy = 0.0, 0.0

    def start_rockfall(self):
        # Cast가 끝난 순간 숨을 낸다. 그새 숨이 모자라졌으면 취소 (숨 그대로)
        if not breath.spend(config.SKILL_BREATH_COST):
            return
        self.rockfall = True
        self.rockfall_hits.clear()
        self.vy = -config.SKILLS['rockfall']['fall_speed']
        self.on_ground = False
        self.fall_time = 0.0

    def fire_arrow(self):
        # 결정 화살 (8.2): Cast가 끝난 순간 숨을 낸다. 그새 숨이 모자라졌으면 취소 (숨 그대로)
        if not breath.spend(config.SKILL_BREATH_COST):
            return
        spec = config.SKILLS['crystal_arrow']
        x = self.x + self.face_dir * (config.PLAYER_W + spec['size'][0]) / 2
        projectile.fire_arrow(x, self.y + config.PLAYER_H / 2, self.face_dir, self, self.platforms)

    def end_skill(self):
        # 피격·환경 피해·기절·방 이동 시 룬 기술을 끊는다 (Cast 중 취소면 숨 차감 없음)
        self.cast_timer = 0.0
        self.rockfall = False
        self.shockwave = None

    def can_drop(self):
        # ↓를 누른 채 Z: one-way 발판 위에 서 있으면 점프 대신 아래로 내려간다 (명세 밖 조작, 18장)
        return (self.on_ground and input.pressed('down')
                and bool(terrain.oneway_under(self.x, self.y, config.PLAYER_W, self.platforms)))

    def start_drop(self):
        self.drop_platforms = terrain.oneway_under(self.x, self.y, config.PLAYER_W, self.platforms)
        self.drop_timer = config.DROP_THROUGH_TIME
        self.on_ground = False
        self.coyote_timer = 0.0   # 내려가는 중에 코요테 점프로 다시 올라가지 않게
        self.vy = 0.0

    def can_jump(self):
        # 공중에서는 결정 디딤이 남아 있어야 한다. 착지까지 JUMP_BUFFER 이내면 디딤을 쓰지 않고
        # 버퍼에 남겨 착지 순간 보통 점프로 처리한다 (6.4)
        if self.on_ground or self.coyote_timer > 0:
            return True
        return self.jumps_left > 0 and not self.landing_soon()

    def landing_soon(self):
        # 지금 속도로 JUMP_BUFFER초 떨어지는 동안 발밑 지형 윗면에 닿는가
        if self.vy > 0 or self.jump_rising:
            return False
        dy, _ = fall_motion(self.vy, config.JUMP_BUFFER, self.wet)   # 아래로 움직이므로 음수
        ignore = self.drop_platforms if self.drop_timer > 0 else ()
        return any(p.kind is not None and p not in ignore and terrain.overlaps_x(self.x, config.PLAYER_W, p)
                   and self.y >= p.top >= self.y + dy for p in self.platforms)

    def start_jump(self):
        if not (self.on_ground or self.coyote_timer > 0):
            self.jumps_left -= 1  # 결정 디딤: 발밑에 결정 발판이 생겼다 부서지며 다시 도약
            effect.crystal_step(self.x, self.y)
        self.vy = config.JUMP_SPEED
        self.jump_rising = True
        self.jump_elapsed = 0.0
        self.on_ground = False
        self.coyote_timer = 0.0
        self.fall_time = 0.0
        sound.play('jump')

    def start_wall_jump(self):
        # 벽점프 (6.4): 벽 반대쪽으로 도약. 높이는 보통 점프와 같다 (누르는 만큼). 공중 추가 점프는 쓰지 않는다
        self.wall_jump_dir = -self.wall_dir
        self.face_dir = self.wall_jump_dir
        self.wall_jump_lock = config.WALL_JUMP_LOCK
        self.wall_dir = 0
        self.vy = config.JUMP_SPEED
        self.jump_rising = True
        self.jump_elapsed = 0.0
        self.coyote_timer = 0.0
        self.fall_time = 0.0
        sound.play('jump')

    def start_attack(self):
        move = input.axis_x()
        if move != 0:
            self.face_dir = move  # 누르고 있는 방향으로 돌아서 공격
        if input.pressed('up'):
            self.attack_dir = 'up'
        elif input.pressed('down') and not self.on_ground:
            self.attack_dir = 'down'
        else:
            self.attack_dir = 'side'
            self.swing_alt = not self.swing_alt
        self.attack_active = config.ATTACK_ACTIVE
        self.attack_cooldown = engravings.attack_cooldown()
        self.attack_hits.clear()
        self.swing_landed = False
        self.swing_strong = False
        self.swing_count += 1
        self.swing_mult = engravings.on_attack_start(self)
        sound.play('swing')

    # ---------- 패링 · 피격 ----------

    def on_parry_success(self, target):
        # 판정 시간은 끝까지 유지해서 동시에 들어온 공격도 막는다
        # 히트스톱·흔들림·섬광은 combat에서
        self.parry_success = True
        self.parry_cooldown = 0
        self.parry_count += 1
        breath.add(engravings.parry_breath_gain(target))   # 패링 숨은 여기서 한 번만 (8.4)
        engravings.on_parry_success(self, target)

    def update_parry(self, dt):
        self.parry_cooldown = max(0, self.parry_cooldown - dt)
        self.parry_stun_timer = max(0, self.parry_stun_timer - dt)
        if self.is_parrying():
            self.parry_timer -= dt
            if self.parry_timer <= 0:
                self.parry_timer = 0
                if not self.parry_success:
                    # 헛입력
                    self.parry_stun_timer = config.PARRY_FAIL_STUN
                    effect.parry_miss(self.x, self.y + config.PLAYER_H / 2)

    def final_damage(self, damage):
        # 칸 단위 최종 피해 (6.8): 패링 실패 경직 중이면 +STUN_DAMAGE_BONUS, 마지막에 DAMAGE_CAP으로 자른다
        damage = int(damage)
        if self.is_parry_stunned():
            damage += config.STUN_DAMAGE_BONUS
        return min(damage, config.DAMAGE_CAP)

    def lose_hp(self, damage):
        # 체력을 깎고 무적을 건다. 체력 0이면 사망 (부활은 play_mode가 DEATH_DELAY 뒤에 한다)
        self.hp = max(self.min_hp, self.hp - self.final_damage(damage))
        self.sitting = False
        self.parry_timer = 0
        self.parry_stun_timer = 0
        self.invincible_timer = self.invincible_on_hit
        self.attack_active = 0  # 공격 중이면 끊는다
        self.cancel_mend()      # 숨 고르기 중이면 숨 차감 없이 취소 (6.3)
        self.cast_timer = 0.0   # Cast 중 피격 시 취소 (6.3). 숨은 낙하를 시작할 때 내므로 잃지 않는다
        self.jump_rising = False
        if self.hp == 0:
            self.dead = True
            effect.player_dead()

    def suffocate_hit(self):
        # 질식 피해 (7.3): 1칸. 히트스톱·경직·무적 없이, 피격 무적 중에도 들어간다
        self.hp = max(self.min_hp, self.hp - 1)
        self.sitting = False
        self.cancel_mend()
        if self.hp == 0:
            self.dead = True
            effect.player_dead()

    def take_hit(self, damage, from_x):
        # 적 공격·접촉·투사체. 피해를 받았으면 True. 무적이면 무시
        if self.is_invincible():
            return False
        self.lose_hp(damage)
        self.hit_timer = config.PLAYER_HIT_STUN
        self.hit_dir = 1 if self.x >= from_x else -1
        engravings.on_hurt(self)   # 「가시 갑각」
        return True

    def hazard_hit(self):
        # 환경 피해 (가시·산성·구덩이, 6.8): HAZARD_DAMAGE → 어두워짐 → 마지막 안전 지점 → 밝아짐
        # 피격 무적 중이면 피해 없이 안전 지점으로만 돌아간다. 숨은 되돌리지 않는다
        if self.dead or self.is_hazard_respawning():
            return
        if not self.is_invincible():
            self.lose_hp(config.HAZARD_DAMAGE)
            effect.player_hit(self.x, self.y + config.PLAYER_H / 2)
            if self.dead:
                return
        self.hazard_timer = config.HAZARD_RESPAWN_FADE * 2
        self.hazard_warped = False
        self.hit_timer = 0
        self.dash_timer = 0
        self.end_skill()
        self.recoil_timer = 0
        self.vx, self.vy = 0.0, 0.0
        input.clear_buffers()
        effect.screen_fade(config.HAZARD_RESPAWN_FADE)

    def respawn_spot(self):
        # safe_points 중 마지막으로 밟은 곳, 없으면 마지막으로 SAFE_GROUND_TIME 이상 서 있던 바닥 (없으면 방 시작 지점)
        return self.safe_point or self.ground_spot

    def update_hazard_respawn(self, dt):
        # 화면이 완전히 어두워진 순간 안전 지점으로 옮긴다. 복귀 중에는 무적 (is_invincible)
        self.hazard_timer = max(0, self.hazard_timer - dt)
        self.vx, self.vy = 0.0, 0.0
        if not self.hazard_warped and self.hazard_timer <= config.HAZARD_RESPAWN_FADE:
            self.hazard_warped = True
            self.x, self.y = self.respawn_spot()
            self.on_ground = False
            self.jump_rising = False
            self.fall_time = 0.0
            self.ground_time = 0.0

    # ---------- 숨 고르기 · 기절 ----------

    def update_mend(self, dt):
        # 숨 고르기 (6.7): A를 RUNE_HOLD_THRESHOLD 이상 누르면 시작. 떼면 취소 (숨은 완료 시에만 내므로 잃는 숨 없음)
        # 계속 누르고 있으면 다음 칸을 이어서 시작한다 (다시 시작 조건 확인). 짧게 누르는 룬 기술은 input의 rune_tap
        if not input.pressed('rune'):
            self.mend_timer = 0.0
            self.mend_wait = False
            return
        if self.is_mending():
            self.mend_timer -= dt
            if self.mend_timer <= 0:
                self.mend_timer = 0.0
                self.finish_mend()
            return
        if not self.mend_wait and input.held_for('rune') >= config.RUNE_HOLD_THRESHOLD and not self.is_locked():
            self.start_mend()

    def start_mend(self):
        # 숨이 비용보다 적으면(질식 중 포함) 시작하지 않는다. 체력이 가득이어도 시작하지 않는다
        if self.hp >= self.max_hp or breath.value < breath.heal_cost():
            self.mend_wait = True
            return
        self.mend_time = self.mend_timer = breath.heal_time()
        self.attack_active = 0

    def finish_mend(self):
        # 그 순간 숨이 비용 이상이면 차감하고 1칸, 모자라면 회복 없이 취소하고 숨은 그대로 (6.3)
        if breath.spend(breath.heal_cost()):
            self.hp = min(self.max_hp, self.hp + 1)
        else:
            self.mend_wait = True

    def cancel_mend(self):
        if self.is_mending():
            self.mend_timer = 0.0
            self.mend_wait = True

    def start_blackout(self):
        # 숨 게이트 기절: 하던 동작을 모두 끊고 쓰러진다 (7.3)
        self.blackout = True
        self.sitting = False
        self.cancel_mend()
        self.attack_active = 0
        self.dash_timer = 0
        self.end_skill()
        self.parry_timer = 0
        self.recoil_timer = 0
        self.jump_rising = False
        input.clear_buffers()

    def end_blackout(self):
        self.blackout = False

    def start_cutscene(self):
        # 컷신 (2.2 추락): 기절과 같이 하던 동작을 끊고 입력을 잠근다. 몸은 그대로 떨어진다
        self.start_blackout()
        self.blackout = False
        self.cutscene = True

    def end_cutscene(self):
        self.cutscene = False
        input.clear_buffers()

    def raise_max_hp(self, max_hp):
        # 갑옷 강화 (13.3): 늘어난 칸만큼 지금 체력도 채운다
        self.hp += max_hp - self.max_hp
        self.max_hp = max_hp

    def revive(self):
        # 사망 부활 (13.2): 체력 전부. 자리·속도는 방에 들어올 때 enter_room이 정한다
        self.dead = False
        self.hp = self.max_hp
        self.invincible_timer = 0.0
        self.parry_timer = 0.0
        self.parry_stun_timer = 0.0
        self.mend_timer = 0.0
        self.mend_wait = False
        self.blackout = False
        self.end_skill()
        input.clear_buffers()

    def sit(self, seat_x):
        # 의자 가운데에 앉는다. 체력 회복·저장은 play_mode가 한다
        self.sitting = True
        self.x = seat_x
        self.vx, self.vy = 0.0, 0.0
        self.attack_active = 0
        input.clear_buffers()

    def update_sitting(self):
        # ←·→·Z로 일어난다. Z는 일어나기에만 쓰고 점프하지 않는다. X(각인 화면)는 play_mode가 키 입력에서 받는다
        if input.consume('jump') or input.axis_x() != 0:
            self.sitting = False
        input.clear_buffers()

    def update_safe_spot(self, dt):
        # 바닥에 서 있는 동안 안전 지점을 갱신한다 (6.8)
        if not self.on_ground or self.dead:
            self.ground_time = 0.0
            return
        r = config.SAFE_POINT_RADIUS
        for sx, sy in self.safe_points:
            if abs(self.x - sx) <= r and abs(self.y - sy) <= r:
                self.safe_point = (sx, sy)
        self.ground_time += dt
        if self.ground_time >= config.SAFE_GROUND_TIME:
            self.ground_spot = (self.x, self.y)

    # ---------- 공격 적중 ----------

    def on_attack_hit(self, target=None):
        # combat이 이번 휘두름에서 대상을 맞힐 때마다 부른다. 반동·포고·세 번째 일격 판정은 휘두름당 1번
        # 반환: 이번 휘두름이 세 번째 일격인가
        engravings.on_attack_hit(self, target)
        if self.swing_landed:
            return self.swing_strong
        self.swing_landed = True
        self.swing_strong = self.count_strike()
        if self.attack_dir == 'side':
            # 반동: 바라보는 반대쪽으로 밀린다 (위 공격은 반동 없음)
            self.recoil_timer = config.ATTACK_RECOIL_TIME
            self.recoil_dir = -self.face_dir
        elif self.attack_dir == 'down':
            self.pogo()
        return self.swing_strong

    def count_strike(self):
        # 세 번째 일격 (v2 3연타의 3타). 연속 적중 수를 세고, 3번째면 각인이 있을 때만 True
        if self.since_last_strike <= config.THIRD_STRIKE['interval']:
            self.strike_chain += 1
        else:
            self.strike_chain = 1
        self.since_last_strike = 0.0
        if self.strike_chain < 3:
            return False
        self.strike_chain = 0
        return engravings.third_strike_on()

    def pogo(self):
        # 아래 공격 적중: 튀어 오르고 대시·추가 점프 재충전, 체공 시간 리셋
        self.vy = config.POGO_SPEED
        self.jump_rising = False
        self.on_ground = False
        self.fall_time = 0.0
        self.air_dash_used = False
        self.jumps_left = self.max_jumps - 1

    def attack_damage(self):
        damage = config.PICKAXE_DAMAGE[self.pickaxe_lv - 1] * engravings.damage_mult(self) * self.swing_mult
        if self.swing_strong:
            damage *= config.THIRD_STRIKE['damage_mult']
        return damage

    def attack_knockback(self, target):
        # 부호 있는 px. 옆 공격은 바라보는 방향, 위·아래 공격은 플레이어에서 먼 쪽
        power = config.THIRD_STRIKE['knockback'] if self.swing_strong else config.ENEMY_KNOCKBACK
        if self.attack_dir == 'side':
            return self.face_dir * power
        return power if target.x >= self.x else -power

    def attack_angle(self):
        # 타격 스파크가 퍼지는 방향 (라디안)
        if self.attack_dir == 'up':
            return math.pi / 2
        if self.attack_dir == 'down':
            return -math.pi / 2
        return 0 if self.face_dir > 0 else math.pi

    def get_attack_bb(self):
        # hitbox 유지 시간에만 공격 hitbox를 만든다. 아니면 None. 몸을 따라 움직인다
        if not self.is_attacking():
            return None
        w, h = config.ATTACK_HITBOX[self.attack_dir]
        if self.attack_dir == 'side':
            w *= engravings.attack_reach_mult()   # 「긴 자루」: 닿는 길이만 늘린다
        else:
            h *= engravings.attack_reach_mult()
        if self.attack_dir == 'up':
            l, b = self.x - w / 2, self.y + config.PLAYER_H
        elif self.attack_dir == 'down':
            l, b = self.x - w / 2, self.y - h
        else:
            half_w = config.PLAYER_W / 2
            l = self.x + half_w if self.face_dir > 0 else self.x - half_w - w
            b = self.y + (config.PLAYER_H - h) / 2
        return l, b, l + w, b + h

    # ---------- 갱신 ----------

    def update(self):
        dt = game_framework.frame_time
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)
        self.hit_timer = max(0, self.hit_timer - dt)
        self.hard_land_timer = max(0, self.hard_land_timer - dt)
        self.attack_active = max(0, self.attack_active - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.since_last_strike += dt
        self.dash_strike_timer = max(0, self.dash_strike_timer - dt)
        self.wall_jump_lock = max(0, self.wall_jump_lock - dt)
        self.wet = self.in_water()
        if self.is_hazard_respawning():
            # HazardRespawn: 입력 잠금, 움직이지 않는다. 누름은 버리지만 누름 상태는 계속 받는다
            self.update_hazard_respawn(dt)
            input.update(dt)
            input.clear_buffers()
            return
        if self.sitting:
            self.update_sitting()
            input.update(dt)
            return
        if self.blackout or self.cutscene:
            # Blackout · Cutscene: 입력 잠금, 중력만 받는다
            self.wall_dir = 0
            self.vx = 0.0
            self.update_move_y(dt)
            input.update(dt)
            input.clear_buffers()
            return
        self.update_parry(dt)
        self.update_mend(dt)
        self.handle_actions()

        was_on_ground = self.on_ground
        if self.is_dashing():
            self.update_dash(dt)
        elif self.is_casting():
            self.update_cast(dt)
        elif self.rockfall:
            self.update_rockfall(dt)
        else:
            self.update_move_x(dt)
            self.update_move_y(dt)
        self.update_landing(was_on_ground, dt)
        self.update_wall(dt)
        self.update_safe_spot(dt)
        if self.y + config.PLAYER_H < 0:
            self.hazard_hit()  # 방 아래로 떨어짐 = 구덩이
        # 버퍼·누름 시간은 동작 처리 뒤에 줄인다 (누른 프레임에 버퍼가 깎이지 않게)
        input.update(dt)

    def update_dash(self, dt):
        # 마지막 프레임은 남은 시간만큼만 이동해서 이동 거리를 DASH_DIST에 맞춘다. 중력 무시
        step = min(dt, self.dash_timer)
        self.dash_timer -= step
        self.vx = self.dash_dir * self.dash_dist * self.water_speed_mult / config.DASH_TIME
        self.vy = 0
        self.dig_soil(self.x + self.vx * step)
        self.move_x(self.vx * step)
        if self.dash_timer <= 0:
            engravings.on_dash_end(self)

    def dig_soil(self, x):
        # 굴착 대시 (6.4): 몸을 x에 두면 닿는 무른 흙벽(Lv3부터 단단한 흙벽도)을 파고 지나간다 (막히기 전에 먼저 부순다)
        half_w = config.PLAYER_W / 2
        types = ('soil', 'hard_soil') if self.can('hard_soil') else ('soil',)
        for p in self.platforms:
            if (getattr(p, 'type', None) in types and p.kind == 'solid'
                    and x + half_w >= p.left and x - half_w <= p.right
                    and self.y + config.PLAYER_H > p.bottom and self.y < p.top):
                p.dig()

    def update_cast(self, dt):
        # Cast: 중력 없이 제자리. 끝나면 낙반 낙하 시작
        self.vx, self.vy = 0.0, 0.0
        self.cast_timer = max(0.0, self.cast_timer - dt)
        if self.cast_timer <= 0:
            if self.cast_skill == 'arrow':
                self.fire_arrow()
            else:
                self.start_rockfall()

    def update_rockfall(self, dt):
        # 낙반 낙하 (8.2): 수직으로 fall_speed, 무적. 깨지는 바닥은 착지 순간 부수고 계속 떨어진다 (12.6)
        self.vx = 0.0
        self.vy = -config.SKILLS['rockfall']['fall_speed']
        prev_y = self.y
        new_y = self.y + self.vy * dt
        self.break_floors(prev_y, new_y)
        self.y, self.vy, self.on_ground = terrain.resolve_y(
            self.x, prev_y, new_y, self.vy, config.PLAYER_W, config.PLAYER_H, self.platforms)
        if self.on_ground:
            self.land_rockfall()

    def break_floors(self, prev_y, new_y):
        # 이번 낙하 구간에서 발이 닿는 깨지는 바닥을 부순다
        for p in self.platforms:
            if (getattr(p, 'type', None) == 'floor' and p.kind == 'solid'
                    and terrain.overlaps_x(self.x, config.PLAYER_W, p) and prev_y >= p.top >= new_y):
                p.dig()

    def land_rockfall(self):
        # 착지: 발밑 좌우로 충격파 (판정은 combat이 이번 프레임에 한 번 본다). 강착지 잠금 없음
        self.rockfall = False
        self.fall_time = 0.0
        spec = config.SKILLS['rockfall']
        half = spec['shockwave_w'] / 2
        self.shockwave = (self.x - half, self.y, self.x + half, self.y + spec['shockwave_h'])
        effect.rockfall_land(self.x, self.y, spec['shockwave_w'])

    def take_shockwave(self):
        wave, self.shockwave = self.shockwave, None
        return wave

    def update_move_x(self, dt):
        if self.dead or self.is_parry_stunned() or self.is_hard_landing() or self.is_mending():
            self.vx = 0
        elif self.is_hit():
            # 경직 중에는 조작 없이 맞은 반대쪽으로 밀려난다
            self.vx = self.hit_dir * config.PLAYER_HIT_KNOCKBACK
        elif self.wall_jump_lock > 0:
            # 벽점프 직후: 수평 입력 무시, 벽 반대쪽으로 (6.4)
            self.vx = self.wall_jump_dir * config.WALL_JUMP_SPEED_X
        else:
            # 즉시 가감속, 공중 제어 100%. 공격 중에도 이동한다 (hitbox가 살아 있는 동안만 방향 고정)
            move = input.axis_x()
            self.vx = move * config.PLAYER_SPEED * self.water_speed_mult
            if self.is_parrying() and self.on_ground:
                self.vx = 0  # 지상 패링은 제자리
            if move != 0 and not self.is_attacking() and not self.is_parrying():
                self.face_dir = move
        dx = self.vx * dt
        if self.recoil_timer > 0:
            step = min(dt, self.recoil_timer)
            self.recoil_timer -= step
            dx += self.recoil_dir * config.ATTACK_RECOIL / config.ATTACK_RECOIL_TIME * step
        self.move_x(dx)

    def move_x(self, dx):
        # 지형 충돌은 X 이동 → X 해결 → Y 이동 → Y 해결 순서로 분리
        self.x += dx
        self.x = terrain.resolve_x(self.x, self.y, config.PLAYER_W, config.PLAYER_H, self.platforms)
        half_w = config.PLAYER_W / 2
        self.x = clamp(half_w, self.x, game_world.room_w - half_w)

    def update_move_y(self, dt):
        dy, remaining = 0.0, dt
        if self.jump_rising:
            # 누르고 있는 동안 JUMP_HOLD_MAX까지 vy 유지 (중력 무시).
            # JUMP_HOLD_MIN 이후에 떼면 그 순간 vy *= JUMP_CUT. 그 전에 떼면 MIN이 되는 순간 자른다
            released = not input.pressed('jump')
            cut_at = max(config.JUMP_HOLD_MIN, self.jump_elapsed) if released else None
            hold_end = min(config.JUMP_HOLD_MAX, cut_at) if released else config.JUMP_HOLD_MAX
            hold = clamp(0, hold_end - self.jump_elapsed, remaining)
            dy += self.vy * hold
            remaining -= hold
            self.jump_elapsed += hold
            if released and self.jump_elapsed >= cut_at:
                if self.vy > 0:
                    self.vy *= config.JUMP_CUT
                self.jump_rising = False
        if remaining > 0:
            fall_dy, self.vy = fall_motion(self.vy, remaining, self.wet)
            if self.is_wall_sliding() and self.vy < config.WALL_SLIDE_SPEED:
                # 벽에 매달린 동안은 WALL_SLIDE_SPEED보다 빨리 떨어지지 않는다
                fall_dy = max(fall_dy, config.WALL_SLIDE_SPEED * remaining)
                self.vy = config.WALL_SLIDE_SPEED
            dy += fall_dy
        if self.vy <= 0:
            self.jump_rising = False

        prev_y = self.y
        new_y = self.y + dy
        if dy > 0:
            self.x = terrain.corner_correct(self.x, prev_y, new_y, config.PLAYER_W, config.PLAYER_H,
                                            self.platforms, config.CORNER_CORRECTION)
        self.drop_timer = max(0.0, self.drop_timer - dt)
        ignore = self.drop_platforms if self.drop_timer > 0 else ()
        self.y, self.vy, self.on_ground = terrain.resolve_y(
            self.x, prev_y, new_y, self.vy, config.PLAYER_W, config.PLAYER_H, self.platforms, ignore)
        if self.vy == 0 and dy > 0:
            self.jump_rising = False  # 천장에 머리를 박음

    def update_landing(self, was_on_ground, dt):
        if self.on_ground:
            if not was_on_ground and self.fall_time >= config.HARD_LAND_FALL_TIME and not self.dead:
                # 강착지: 입력 잠금 + 큰 먼지
                self.hard_land_timer = config.HARD_LAND_LOCK
                effect.hard_land(self.x, self.y)
            self.fall_time = 0.0
            self.coyote_timer = config.COYOTE_TIME
            self.air_dash_used = False
            self.jumps_left = self.max_jumps - 1
        else:
            # 코요테 타임은 공중에 있는 동안만 줄인다 (발판을 벗어난 프레임부터)
            self.coyote_timer = max(0, self.coyote_timer - dt)
            if self.vy < 0 and not self.is_dashing():
                self.fall_time += dt

    def update_wall(self, dt):
        # 벽 매달리기 (6.4, 버팀의 룬): 공중에서 벽 쪽 방향키를 누르고 있고 몸 옆이 단단한 벽에 닿아 있으면 WallSlide
        # 매달린 동안 대시·공중 점프 재충전, 체공 시간 리셋 (강착지 없음). 같은 벽에 다시 매달릴 수 있다
        # 가시 덩굴벽(thorn_vine)은 버팀 Lv2(thorn_cling)부터 매달린다 (12.6, T65). 그 전에는 닿으면 환경 피해
        move = input.axis_x()
        walls = self.platforms
        if not self.can('thorn_cling'):
            walls = [p for p in walls if getattr(p, 'hazard_type', None) != 'thorn_vine']
        cling = (move != 0 and not self.on_ground and self.can('wall_cling') and not self.is_dashing()
                 and not self.is_skill_active()
                 and self.wall_jump_lock <= 0 and not self.dead and not self.is_hit() and not self.is_mending()
                 and terrain.body_blocked(self.x + move, self.y + config.PLAYER_H * 0.25, config.PLAYER_W,
                                          config.PLAYER_H * 0.5, walls))
        self.wall_dir = move if cling else 0
        if not cling:
            self.wall_spark_timer = 0.0
            return
        self.air_dash_used = False
        self.jumps_left = self.max_jumps - 1
        self.fall_time = 0.0
        if self.vy < 0:
            # 곡괭이를 벽에 박고 미끄러지며 튀는 불꽃
            self.wall_spark_timer -= dt
            if self.wall_spark_timer <= 0:
                spark = config.WALL_SLIDE_SPARK
                self.wall_spark_timer = spark['interval']
                effect.burst(self.x + self.wall_dir * config.PLAYER_W / 2,
                             self.y + config.PLAYER_H * config.WALL_PICK['y'], spark, spark['color'])

    # ---------- 그리기 ----------

    def is_blink_hidden(self):
        # 피격 무적 중에는 BLINK_INTERVAL마다 숨겼다 보였다 한다
        if self.dead or self.invincible_timer <= 0:
            return False
        return int(self.invincible_timer / config.BLINK_INTERVAL) % 2 == 1

    def slash_rect(self, attack_bb):
        # 옆 공격은 두 모션을 번갈아 위쪽 띠 / 아래쪽 띠로 그린다 (판정은 hitbox 전체)
        l, b, r, t = attack_bb
        if self.attack_dir != 'side':
            return attack_bb
        band = (t - b) * config.SLASH_BAND_RATIO
        return (l, t - band, r, t) if self.swing_alt else (l, b, r, b + band)

    def pickaxe_color(self):
        # 곡괭이 레벨마다 색이 바뀐다 (13.3, T64)
        return config.COLOR_PICKAXE[self.pickaxe_lv - 1]

    def draw(self):
        l, b, r, t = self.get_bb()
        attack_bb = self.get_attack_bb()
        if not self.is_blink_hidden():
            if self.dead:
                color = config.COLOR_PLAYER_DEAD
            elif self.is_skill_active():
                color = (config.COLOR_PLAYER_CAST_ARROW if self.is_casting() and self.cast_skill == 'arrow'
                         else config.COLOR_PLAYER_ROCKFALL)
            elif self.is_dashing():
                color = config.COLOR_PLAYER_DASH
            elif self.is_parry_stunned():
                color = config.COLOR_PLAYER_STUN
            elif self.is_hard_landing():
                color = config.COLOR_PLAYER_HARD_LAND
            else:
                color = config.COLOR_PLAYER
            if self.sitting:
                t = b + config.PLAYER_H * config.SIT_BODY_RATIO
            camera.draw_rect(l, b, r, t, *color, filled=True)
            if self.is_wall_sliding():
                # 벽에 박은 곡괭이
                pick = config.WALL_PICK
                px = self.x + self.wall_dir * config.PLAYER_W / 2
                py = b + config.PLAYER_H * pick['y']
                camera.draw_rect(min(px, px + self.wall_dir * pick['w']), py - pick['h'] / 2,
                                 max(px, px + self.wall_dir * pick['w']), py + pick['h'] / 2,
                                 *self.pickaxe_color(), filled=True)
            if self.is_parrying():
                # 몸 앞쪽에 방패 표시
                sx = r if self.face_dir > 0 else l - config.PARRY_SHIELD_W
                camera.draw_rect(sx, b, sx + config.PARRY_SHIELD_W, t, *config.COLOR_PLAYER_PARRY, filled=True)
            # 바라보는 방향 표시
            eye_x = self.x + self.face_dir * config.PLAYER_W / 4
            eye = config.PLAYER_W / 8
            camera.draw_rect(eye_x - eye / 2, t - eye * 3, eye_x + eye / 2, t - eye * 2, *config.COLOR_TEXT, filled=True)
            if attack_bb:
                camera.draw_rect(*self.slash_rect(attack_bb), *self.pickaxe_color(), filled=True)
        if self.is_mending():
            # 숨 고르기: 몸 둘레 점 고리가 완료에 가까울수록 조여든다
            ring = config.MEND_RING
            progress = 1 - self.mend_timer / self.mend_time
            radius = ring['radius'][0] + (ring['radius'][1] - ring['radius'][0]) * progress
            effect.draw_ring(self.x, self.y + config.PLAYER_H / 2, radius, radius,
                             ring['dots'], ring['size'], config.COLOR_MEND)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)
            if attack_bb:
                camera.draw_rect(*attack_bb, *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        half_w = config.PLAYER_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.PLAYER_H

    def handle_collision(self, group, other):
        pass
