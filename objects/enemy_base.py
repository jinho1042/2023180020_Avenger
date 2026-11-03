from pico2d import *

import config
import game_framework
import game_world
from objects import effect
from systems import terrain

# 공통 AI 상태: Idle → Chase → Telegraph → Windup → Active → Recover → (Chase)
# 어느 상태든 패링당하면 Stagger → (Chase)
IDLE, CHASE, TELEGRAPH, WINDUP, ACTIVE, RECOVER, STAGGER, DEAD = (
    'Idle', 'Chase', 'Telegraph', 'Windup', 'Active', 'Recover', 'Stagger', 'Dead')


class Attack:
    # 공격 하나를 데이터로 정의한다. hitbox는 (가로, 세로)이고 몸 앞쪽에 붙는다
    def __init__(self, name, parryable, telegraph, windup, active, recover, damage, hitbox):
        self.name = name
        self.parryable = parryable
        self.telegraph = max(telegraph, config.TELEGRAPH_MIN)
        self.windup = windup
        self.active = active
        self.recover = recover
        self.damage = damage
        self.hitbox = hitbox


class EnemyBase:
    is_boss = False  # True면 하단 보스 HUD에 표시

    def __init__(self, x, y, stats, player, platforms):
        # x, y는 발 중심 좌표
        self.x, self.y = x, y
        self.vx, self.vy = 0.0, 0.0
        self.w, self.h = stats['w'], stats['h']
        self.color = stats['color']
        self.hp = stats['hp']
        self.speed = stats['speed']
        self.detect_range = stats['detect_range']
        self.attack_range = stats['attack_range']
        self.attack_cooldown_time = stats['attack_cooldown']
        self.face_dir = -1
        self.on_ground = False
        self.player = player
        self.platforms = platforms

        self.state = IDLE
        self.state_timer = 0.0
        # 이번에 이어서 쓸 공격들(연타면 여러 개)과 현재 공격
        self.attack_queue = []
        self.attack = None
        # 이번 Active 구간에 이미 플레이어를 맞혔는지 (한 번만 피해)
        self.attack_hit = False
        self.attack_cooldown = 0.0
        self.knock_timer = 0.0
        self.knock_vx = 0.0
        self.hurt_timer = 0.0

    def choose_attacks(self):
        # 서브클래스가 이번에 쓸 Attack 목록을 돌려준다
        return []

    def is_alive(self):
        return self.state != DEAD

    def deals_contact_damage(self):
        # 패링당해 비틀거리는 동안은 붙어서 반격할 수 있게 몸 접촉 피해를 주지 않는다
        return self.state not in (STAGGER, DEAD)

    def set_state(self, state, duration=0.0):
        self.state = state
        self.state_timer = duration

    def face_player(self):
        self.face_dir = 1 if self.player.x >= self.x else -1

    def in_attack_range(self):
        return (abs(self.player.x - self.x) <= self.attack_range
                and abs(self.player.y - self.y) < self.h)

    def start_next_attack(self):
        self.attack = self.attack_queue.pop(0)
        self.face_player()
        self.set_state(TELEGRAPH, self.attack.telegraph)
        effect.telegraph(self.attack.parryable)

    def next_phase(self):
        if self.state == TELEGRAPH:
            self.set_state(WINDUP, self.attack.windup)
        elif self.state == WINDUP:
            self.attack_hit = False
            self.set_state(ACTIVE, self.attack.active)
        elif self.state == ACTIVE:
            self.set_state(RECOVER, self.attack.recover)
        elif self.state == RECOVER:
            if self.attack_queue:
                self.start_next_attack()
            else:
                self.attack = None
                self.attack_cooldown = self.attack_cooldown_time
                self.set_state(CHASE)
        elif self.state == STAGGER:
            self.set_state(CHASE)

    def on_parried(self):
        # 남은 연타를 취소하고 비틀거린다. 회복 후 바로 다시 공격하지 않게 쿨타임을 건다
        self.attack_queue = []
        self.attack = None
        self.attack_cooldown = self.attack_cooldown_time
        self.set_state(STAGGER, config.ENEMY_STAGGER_TIME)

    def chase(self):
        if self.player.dead:
            self.vx = 0
            return
        self.face_player()
        if self.in_attack_range() and self.attack_cooldown <= 0:
            self.vx = 0
            self.attack_queue = self.choose_attacks()
            if self.attack_queue:
                self.start_next_attack()
        elif abs(self.player.x - self.x) > self.attack_range:
            self.vx = self.face_dir * self.speed
        else:
            self.vx = 0

    def take_damage(self, damage, knockback=0):
        # knockback은 부호 있는 px (오른쪽이 +)
        if self.state == STAGGER:
            damage *= config.STAGGER_DAMAGE_MULT
        self.hp -= damage
        self.hurt_timer = config.ENEMY_HURT_FLASH
        if knockback:
            self.knock_timer = config.KNOCKBACK_TIME
            self.knock_vx = knockback / config.KNOCKBACK_TIME
        if self.hp <= 0:
            self.die()
        else:
            effect.enemy_hurt(self.x, self.y + self.h / 2)

    def die(self):
        self.hp = 0
        self.set_state(DEAD)
        game_world.remove_object(self)
        effect.enemy_killed(self.x, self.y + self.h / 2, self.color)

    def update(self):
        if not self.is_alive():
            return
        dt = game_framework.frame_time
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.hurt_timer = max(0, self.hurt_timer - dt)
        self.state_timer -= dt
        self.update_ai()
        self.move(dt)

    def update_ai(self):
        if self.state == IDLE:
            self.vx = 0
            if abs(self.player.x - self.x) <= self.detect_range:
                self.set_state(CHASE)
        elif self.state == CHASE:
            self.chase()
        else:
            self.vx = 0
            if self.state_timer <= 0:
                self.next_phase()

    def move_x(self, dt):
        # 넉백은 AI 이동보다 우선한다
        if self.knock_timer > 0:
            # 마지막 프레임은 남은 시간만큼만 밀어서 넉백 거리를 맞춘다
            step = min(dt, self.knock_timer)
            self.knock_timer -= step
            self.x += self.knock_vx * step
        else:
            self.x += self.vx * dt
        self.x = terrain.resolve_x(self.x, self.y, self.w, self.h, self.platforms)
        half_w = self.w / 2
        self.x = clamp(half_w, self.x, config.SCREEN_W - half_w)

    def move(self, dt):
        # 지상 유닛: X 이동 → X 해결 → 중력·Y 이동 → Y 해결
        self.move_x(dt)
        self.vy += config.GRAVITY * dt
        prev_y = self.y
        self.y += self.vy * dt
        self.y, self.vy, self.on_ground = terrain.resolve_y(
            self.x, prev_y, self.y, self.vy, self.w, self.h, self.platforms)

    def get_attack_bb(self):
        # Active 구간에서만 몸 앞쪽에 공격 hitbox를 만든다. 아니면 None (hitbox 없는 공격도 None)
        if self.state != ACTIVE or self.attack.hitbox is None:
            return None
        w, h = self.attack.hitbox
        half_w = self.w / 2
        if self.face_dir > 0:
            l = self.x + half_w
        else:
            l = self.x - half_w - w
        b = self.y + (self.h - h) / 2
        return l, b, l + w, b + h

    def telegraph_color(self):
        return config.COLOR_PARRYABLE if self.attack.parryable else config.COLOR_UNPARRYABLE

    def body_color(self):
        if self.hurt_timer > 0:
            return config.COLOR_ENEMY_HURT
        if self.state == STAGGER:
            return config.COLOR_ENEMY_STAGGER
        if self.state == TELEGRAPH and int(self.state_timer / config.TELEGRAPH_BLINK) % 2 == 0:
            return self.telegraph_color()
        return self.color

    def draw(self):
        l, b, r, t = self.get_bb()
        draw_rectangle(l, b, r, t, *self.body_color(), filled=True)
        # 바라보는 방향 표시
        eye_x = self.x + self.face_dir * self.w / 4
        eye = self.w / 8
        draw_rectangle(eye_x - eye / 2, t - eye * 3, eye_x + eye / 2, t - eye * 2, *config.COLOR_TEXT, filled=True)

        if self.state == TELEGRAPH and not self.attack.parryable:
            # 패링 불가 공격은 머리 위 '!' 표시
            draw_rectangle(self.x - eye / 2, t + eye * 2, self.x + eye / 2, t + eye * 5,
                           *config.COLOR_UNPARRYABLE, filled=True)
            draw_rectangle(self.x - eye / 2, t + eye / 2, self.x + eye / 2, t + eye * 1.5,
                           *config.COLOR_UNPARRYABLE, filled=True)
        self.draw_weapon(l, b, r, t)

        attack_bb = self.get_attack_bb()
        if attack_bb:
            draw_rectangle(*attack_bb, *config.COLOR_ENEMY_SLASH, filled=True)
        if game_world.show_hitbox:
            draw_rectangle(l, b, r, t, *config.COLOR_DEBUG_BODY)
            if attack_bb:
                draw_rectangle(*attack_bb, *config.COLOR_DEBUG_ATTACK)

    def draw_weapon(self, l, b, r, t):
        if self.state == WINDUP:
            # 무기를 들어 올린 모션 (몸 뒤쪽 위)
            eye = self.w / 8
            wx = self.x - self.face_dir * self.w / 2
            draw_rectangle(wx - eye / 2, t, wx + eye / 2, t + self.h / 2, *config.COLOR_ENEMY_WINDUP, filled=True)

    def get_bb(self):
        half_w = self.w / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + self.h

    def handle_collision(self, group, other):
        pass
