import random

import config
import game_framework
import game_world
from objects import effect, magic_circle, pickup, projectile
from objects.enemy_base import CHASE, DEAD, STAGGER, EnemyBase
from systems import camera, sound

# 보스 공통 구조 (11.2)
# 상태: Dormant → Intro → Fight(phase n) → PhaseTransition → Groggy → Dying → Dead
#   Fight = enemy_base의 Chase/Telegraph/Windup/Active/Recover/Stagger (패턴 하나 = 이어서 쓸 Attack 목록)
#   Dormant: 아레나 트리거(systems/script.py Arena)를 기다린다. 무적, 움직이지 않음
#   Intro: 첫 만남은 BOSS_INTRO_CARD_TIME(타이틀 카드), 재도전은 BOSS_INTRO_SHORT. 플레이어 입력 잠금·숨 정지
#   PhaseTransition: phase_hp 아래로 내려가면 무적 + 포효 + 외형·패턴표 교체(on_phase) + 적 투사체 제거
#   Groggy: 자세(posture)가 POSTURE_MAX에 닿으면. 공기 주머니가 터져 숨 회복, 끝나면 자세 0 + 잠깐 무적
#   Dying: 슬로모션·섬광·투사체·소환물 제거 → BOSS_DEATH_FALL 뒤 쓰러짐(광석) → Dead
# 처치 뒤 아레나 문·안전지대·저장은 script.Arena → play_mode.on_boss_defeated
DORMANT, INTRO, PHASE_TRANSITION, GROGGY, DYING = 'Dormant', 'Intro', 'PhaseTransition', 'Groggy', 'Dying'
NO_FIGHT = (DORMANT, INTRO, PHASE_TRANSITION, DYING)   # 무적이고 몸에 닿아도 피해 없음


def boss_damage(stats, parryable):
    # 칸 단위 피해 (T31): 흰(패링 가능) 패턴은 damage, 빨간(패링 불가) 강공격은 heavy_damage
    return stats['damage'] if parryable else stats['heavy_damage']


def clear_hostile_projectiles():
    # 화면의 적 투사체·마법진 제거 (페이즈 전환·처치, 11.2). 반사탄은 남긴다
    for layer in game_world.world:
        for o in layer:
            if isinstance(o, projectile.Projectile) and not o.reflected:
                o.destroy()
            elif isinstance(o, magic_circle.MagicCircle):
                game_world.remove_object(o)


class BossBase(EnemyBase):
    is_boss = True
    kind = 'boss'
    boss_key = None   # config.BOSS_NAME 키 = 방 JSON boss 값 (bosses_met·bosses_defeated에 남는다)

    def __init__(self, x, y, stats, player, platforms):
        # 공격 사거리는 패턴마다 다르므로 attack_range는 쓰지 않는다. 패턴 사이 대기는 BOSS_IDLE_GAP
        super().__init__(x, y, dict(stats, attack_range=stats['near_range'], attack_cooldown=0),
                         player, platforms)
        self.max_hp = self.hp
        self.posture = 0
        self.history = []      # 최근 사용한 패턴 이름 (BOSS_MAX_REPEAT개까지)
        self.cooldowns = {}    # 패턴 이름 → 남은 쿨다운 (s)
        self.phase = 1
        self.phase_hp = list(stats.get('phase_hp', []))   # 체력 비율. 이 아래로 내려가면 다음 페이즈
        self.summons = []      # 소환한 적 (처치 시 함께 제거)
        self.new_summons = []  # 아직 play_mode가 가져가지 않은 소환
        self.rise_timer = 0.0  # 그로기에서 일어난 뒤 무적
        self.intro_time = 0.0
        self.first_meet = False
        self.set_state(DORMANT)

    # ---------- 등장 ----------

    def wake(self, first):
        # 아레나 트리거에 들어옴 (script.Arena). first = 첫 만남(bosses_met에 없었음)이면 타이틀 카드
        self.first_meet = first
        self.intro_time = config.BOSS_INTRO_CARD_TIME if first else config.BOSS_INTRO_SHORT
        self.face_player()
        self.set_state(INTRO, self.intro_time)
        self.player.start_cutscene()
        effect.boss_roar(self.x, self.y + self.h / 2, self.color)
        sound.play_music('boss')

    def is_dormant(self):
        return self.state == DORMANT

    def card_alpha(self):
        # 타이틀 카드 불투명도 0~1 (첫 만남 등장 중에만). 처음·끝 BOSS_CARD.fade 동안 서서히
        if self.state != INTRO or not self.first_meet:
            return 0.0
        elapsed = self.intro_time - self.state_timer
        fade = config.BOSS_CARD['fade']
        return max(0.0, min(1.0, elapsed / fade, self.state_timer / fade))

    def show_hud(self):
        # 보스 이름 + 자세 게이지는 싸우는 동안만 (14.1)
        return self.state not in (DORMANT, INTRO, DYING, DEAD)

    # ---------- 상태 진행 ----------

    def update(self):
        dt = game_framework.frame_time
        self.rise_timer = max(0, self.rise_timer - dt)
        for name in self.cooldowns:
            self.cooldowns[name] = max(0, self.cooldowns[name] - dt)
        super().update()

    def idle_gap(self):
        return random.uniform(*config.BOSS_IDLE_GAP)

    def to_fight(self):
        self.attack_queue = []
        self.attack = None
        self.attack_cooldown = self.idle_gap()
        self.set_state(CHASE)

    def next_phase(self):
        if self.state == DORMANT:
            return
        if self.state == INTRO:
            self.player.end_cutscene()
            self.to_fight()
        elif self.state == PHASE_TRANSITION:
            self.to_fight()
        elif self.state == GROGGY:
            self.posture = 0
            self.rise_timer = config.GROGGY_RISE_INVULN
            self.to_fight()
        elif self.state == DYING:
            self.fall()
        else:
            prev = self.state
            super().next_phase()
            if self.state == CHASE and prev != CHASE:
                self.attack_cooldown = self.idle_gap()   # 패턴 사이 BOSS_IDLE_GAP (11.2)

    # ---------- 패턴 선택 ----------

    def repeat_limited(self, name):
        recent = self.history[-config.BOSS_MAX_REPEAT:]
        return len(recent) == config.BOSS_MAX_REPEAT and all(n == name for n in recent)

    def pick_pattern(self, weights):
        # 가중치(거리 조건은 서브클래스가 고른 표) 중 쿨다운·연속 BOSS_MAX_REPEAT회를 뺀 것에서 고른다 (원칙 13)
        names = [n for n, w in weights.items()
                 if w > 0 and self.cooldowns.get(n, 0) <= 0 and not self.repeat_limited(n)]
        if not names:
            return None
        return random.choices(names, [weights[n] for n in names])[0]

    def remember_pattern(self, name, cooldown=0):
        self.history = (self.history + [name])[-config.BOSS_MAX_REPEAT:]
        if cooldown > 0:
            self.cooldowns[name] = cooldown

    def cancel_attack(self):
        self.attack_queue = []
        self.attack = None
        self.attack_cooldown = self.idle_gap()

    # ---------- 페이즈 · 외형 ----------

    def damage_stage(self):
        # 체력 66%·33% 아래에서 0 → 1 → 2 (원칙 12). 균열 선 + 색 한 단계 어둡게
        ratio = self.hp / self.max_hp
        return sum(1 for s in config.BOSS_DAMAGE_STAGE_HP if ratio < s)

    def check_phase(self):
        i = self.phase - 1
        if i >= len(self.phase_hp) or self.hp > self.max_hp * self.phase_hp[i]:
            return
        self.phase += 1
        self.cancel_attack()
        self.vx = 0
        self.set_state(PHASE_TRANSITION, config.PHASE_TRANSITION_TIME)
        clear_hostile_projectiles()
        self.on_phase(self.phase)
        effect.boss_phase2(self.x, self.y + self.h / 2, self.color)
        print(f'[보스] {self.boss_key} 페이즈 {self.phase}')

    def on_phase(self, phase):
        # 서브클래스: 외형 변경 + 패턴표 교체 (원칙 6)
        pass

    # ---------- 피격 · 자세 ----------

    def invulnerable(self):
        return self.state in NO_FIGHT or self.rise_timer > 0

    def take_damage(self, damage, knockback=0):
        # 경직·넉백 없음. 떨림·스파크만 (11.2)
        if self.invulnerable():
            return
        if self.state == GROGGY:
            damage *= config.GROGGY_DAMAGE_MULT
        super().take_damage(damage)
        if self.state != DYING:
            self.check_phase()

    def add_posture(self, amount):
        # 패링 +POSTURE_PARRY, 곡괭이 +POSTURE_PER_HIT, 룬 기술 +POSTURE_PER_SKILL, 반사탄 +POSTURE_REFLECT (9.4)
        # POSTURE_MAX에 닿으면 그로기에 들어가고 True. 그로기·무적 중에는 쌓지 않는다
        if self.state == GROGGY or self.invulnerable():
            return False
        self.posture = min(config.POSTURE_MAX, self.posture + amount)
        if self.posture < config.POSTURE_MAX:
            return False
        self.cancel_attack()
        self.vx = 0
        self.set_state(GROGGY, config.GROGGY_TIME)
        cx, cy = self.x, self.y + self.h / 2
        effect.boss_groggy(cx, cy)
        effect.air_burst(cx, cy)
        from systems import breath   # 순환 import 방지 (world → room → bosses → breath → world)
        breath.add(config.BREATH_GROGGY_BURST)   # 공기 주머니가 터짐 (7.2 표, 9.4)
        return True

    def on_parried(self):
        if not self.add_posture(config.POSTURE_PARRY):
            self.recoil()

    def recoil(self):
        # 보스는 길게 비틀거리지 않고 잠깐만 멈칫한다
        self.cancel_attack()
        self.set_state(STAGGER, config.BOSS_PARRY_RECOIL)

    def deals_contact(self):
        # 등장·페이즈 전환·처치 중, 그로기 중에는 접촉 피해 없음
        return self.state not in NO_FIGHT and self.state != GROGGY and super().deals_contact()

    # ---------- 소환물 ----------

    def pop_summons(self):
        new, self.new_summons = self.new_summons, []
        return new

    def alive_summons(self):
        return [s for s in self.summons if s.is_alive()]

    # ---------- 처치 ----------

    def die(self):
        # 체력 0: 슬로모션·섬광 + 투사체·소환물 제거 → BOSS_DEATH_FALL 뒤 쓰러짐 (11.2)
        self.hp = 0
        self.cancel_attack()
        self.vx = 0
        self.set_state(DYING, config.BOSS_DEATH_FALL)
        clear_hostile_projectiles()
        for s in self.alive_summons():
            s.die()
        effect.boss_dying()
        print(f'[보스] {self.boss_key} 처치')

    def fall(self):
        # 쓰러짐: 광석 드롭 + 품고 있던 공기가 풀림. 문·안전지대·저장은 script.Arena가 이어서 한다
        self.set_state(DEAD)
        game_world.remove_object(self)
        cx, cy = self.x, self.y + self.h / 2
        effect.enemy_killed(cx, cy, self.color)
        effect.air_burst(cx, cy)
        pickup.spill(cx, cy, self.ore, self.player)

    # ---------- 그리기 ----------

    def body_color(self):
        if self.state == GROGGY:
            return config.COLOR_BOSS_GROGGY
        color = super().body_color()
        if color != self.color:
            return color   # 예고 번쩍임·멈칫 색은 그대로
        k = config.BOSS_STAGE_DARKEN ** self.damage_stage()
        return tuple(int(c * k) for c in color)

    def draw_body(self):
        if self.state == GROGGY:
            self.draw_groggy()
            return
        super().draw_body()
        self.draw_cracks()

    def draw_groggy(self):
        # 쓰러진 몸(낮게) + 깜빡이는 약점 (11.2)
        l, b, r, t = self.get_bb()
        top = b + self.h * config.GROGGY_SQUASH
        camera.draw_rect(l, b, r, top, *self.body_color(), filled=True)
        self.draw_weapon(l, b, r, top)
        weak = config.BOSS_WEAK_POINT
        if int(self.state_timer / weak['blink']) % 2 == 0:
            effect.draw_disc(self.x, top, weak['radius'], weak['color'])

    def draw_cracks(self):
        # 외형 단계 1: 왼쪽 위에서 가운데로, 단계 2: 오른쪽 아래에서 하나 더
        stage = self.damage_stage()
        if stage <= 0:
            return
        l, b, r, t = self.get_bb()
        w, h = r - l, t - b
        lines = [[(l + w * 0.2, t), (l + w * 0.5, b + h * 0.6), (l + w * 0.35, b + h * 0.35)],
                 [(r, b + h * 0.3), (l + w * 0.6, b + h * 0.45), (l + w * 0.7, b + h * 0.8)]]
        for points in lines[:stage]:
            self.draw_crack(points)

    def draw_crack(self, points):
        crack = config.BOSS_CRACK
        half = crack['width'] / 2
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / crack['step']))
            for i in range(steps + 1):
                x = x0 + (x1 - x0) * i / steps
                y = y0 + (y1 - y0) * i / steps
                camera.draw_rect(x - half, y - half, x + half, y + half, *crack['color'], filled=True)
