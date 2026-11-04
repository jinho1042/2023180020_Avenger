from pico2d import *

import config
import game_framework
import game_world
from objects import effect
from systems import sound, terrain, upgrades


class Player:
    def __init__(self, platforms, start):
        # x, y는 발 중심 좌표
        self.x, self.y = start
        self.vx, self.vy = 0.0, 0.0
        self.face_dir = 1
        self.on_ground = False
        self.jump_held = False
        self.jumps_left = 0  # 공중 추가 점프 남은 횟수 (2단 점프 강화)
        # 좌우 동시 입력 처리를 위해 누름 상태를 따로 저장
        self.left_pressed = False
        self.right_pressed = False
        # 대시: dash_timer > 0인 동안 대시 중(무적·중력 무시), 쿨타임은 대시 시작부터 센다
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.dash_dir = 1
        # 공격: attack_step은 현재(또는 직전) 몇 타째인지(0이면 콤보 없음)
        # attack_timer > 0인 동안 공격 중, 끝나면 combo_timer 동안 다음 타 입력 허용
        self.attack_step = 0
        self.attack_timer = 0.0
        self.combo_timer = 0.0
        self.attack_buffer = 0.0
        self.lunge_timer = 0.0  # > 0인 동안 공격 전진 중
        # 이번 공격 판정 구간에 이미 맞힌 적 (한 번 휘두름에 한 번만 피해)
        self.attack_hits = set()
        # 패링: parry_timer > 0인 동안 판정 중. 아무것도 못 막고 끝나면 parry_stun_timer 동안 경직
        # 쿨타임은 패링 시작부터 세고, 성공하면 즉시 0
        self.parry_timer = 0.0
        self.parry_success = False
        self.parry_cooldown = 0.0
        self.parry_stun_timer = 0.0
        self.parry_buffer = 0.0
        self.parry_count = 0  # 결과 화면 통계
        # 피격: hit_timer > 0인 동안 경직(조작 불가, 밀려남), 무적은 invincible_timer로 따로 센다
        self.hp = config.PLAYER_HP
        self.hit_timer = 0.0
        self.hit_dir = 1
        self.invincible_timer = 0.0
        self.dead = False
        # 충돌을 검사할 지형 목록
        self.platforms = platforms
        # 강화로 바뀌는 수치 (systems/upgrades.py). upgrades는 획득 순서대로 강화 키
        self.upgrades = []
        self.max_hp = config.PLAYER_HP
        self.parry_window = config.PARRY_WINDOW
        self.reflect_damage_mult = config.REFLECT_DAMAGE_MULT
        self.invincible_on_hit = config.INVINCIBLE_ON_HIT
        self.attack_mult = 1.0
        self.swing_mult = 1.0  # 이번 한 번 휘두름의 추가 배율 (upgrades.on_attack이 정함)
        self.max_jumps = 1
        self.dash_dist = config.DASH_DIST
        self.dash_cooldown_time = config.DASH_COOLDOWN
        self.dash_strike_ready = False

    def enter_room(self, platforms, start):
        # 다음 방으로 옮길 때 위치·속도·지형만 바꾸고 체력 등 런 상태는 유지한다
        self.x, self.y = start
        self.vx, self.vy = 0.0, 0.0
        self.on_ground = False
        self.dash_timer = 0.0
        self.hit_timer = 0.0
        self.platforms = platforms

    def clear_input(self):
        # 다른 모드가 위에 있는 동안 뗀 키를 놓치므로 누름 상태를 초기화한다
        self.left_pressed = False
        self.right_pressed = False
        self.jump_held = False

    def handle_event(self, e):
        if e.type == SDL_KEYDOWN:
            if e.key == SDLK_LEFT:
                self.left_pressed = True
            elif e.key == SDLK_RIGHT:
                self.right_pressed = True
            elif self.dead:
                return
            elif e.key == SDLK_SPACE:
                self.start_dash()
            elif e.key == SDLK_a:
                if self.is_busy():
                    # 선입력: 현재 동작이 끝나면 실행
                    self.attack_buffer = config.INPUT_BUFFER
                else:
                    self.start_attack()
            elif e.key == SDLK_s:
                # 공격 중이면 캔슬하고 패링, 다른 동작 중이면 선입력
                if self.can_parry():
                    self.start_parry()
                else:
                    self.parry_buffer = config.INPUT_BUFFER
            elif e.key == SDLK_LALT:
                self.jump_held = True
                if self.is_busy():
                    return
                if self.on_ground:
                    self.vy = config.JUMP_SPEED
                    self.on_ground = False
                    sound.play('jump')
                elif self.jumps_left > 0:
                    self.jumps_left -= 1
                    self.vy = config.JUMP_SPEED
                    sound.play('jump')
        elif e.type == SDL_KEYUP:
            if e.key == SDLK_LEFT:
                self.left_pressed = False
            elif e.key == SDLK_RIGHT:
                self.right_pressed = False
            elif e.key == SDLK_LALT:
                self.jump_held = False
                # 가변 점프: 상승 중에 떼면 상승 속도를 깎는다
                if self.vy > 0:
                    self.vy *= config.JUMP_CUT

    def is_dashing(self):
        return self.dash_timer > 0

    def is_invincible(self):
        return self.is_dashing() or self.invincible_timer > 0 or self.dead

    def is_hit(self):
        return self.hit_timer > 0

    def is_parrying(self):
        # 6장의 parry_active
        return self.parry_timer > 0

    def is_parry_stunned(self):
        return self.parry_stun_timer > 0

    def is_busy(self):
        # 새 동작(공격·점프)을 바로 시작할 수 없는 상태
        return (self.is_attacking() or self.is_dashing() or self.is_hit()
                or self.is_parrying() or self.is_parry_stunned())

    def can_parry(self):
        return (self.parry_cooldown <= 0 and not self.is_dashing() and not self.is_hit()
                and not self.is_parrying() and not self.is_parry_stunned())

    def start_parry(self):
        self.parry_timer = self.parry_window
        self.parry_success = False
        self.parry_cooldown = config.PARRY_COOLDOWN
        # 공격 캔슬, 콤보도 끊는다
        self.attack_timer = 0
        self.attack_step = 0
        self.combo_timer = 0
        move = self.right_pressed - self.left_pressed
        if move != 0:
            self.face_dir = move

    def on_parry_success(self, target):
        # 판정 시간은 끝까지 유지해서 동시에 들어온 공격도 막는다
        # 히트스톱·흔들림·섬광은 combat에서
        self.parry_success = True
        self.parry_cooldown = 0
        self.parry_count += 1
        upgrades.on_parry_success(self, target)

    def update_parry(self, dt):
        self.parry_cooldown = max(0, self.parry_cooldown - dt)
        self.parry_buffer = max(0, self.parry_buffer - dt)
        self.parry_stun_timer = max(0, self.parry_stun_timer - dt)
        if self.is_parrying():
            self.parry_timer -= dt
            if self.parry_timer <= 0:
                self.parry_timer = 0
                if not self.parry_success:
                    # 헛입력
                    self.parry_stun_timer = config.PARRY_FAIL_STUN
                    effect.parry_miss(self.x, self.y + config.PLAYER_H / 2)
        if self.parry_buffer > 0 and self.can_parry():
            self.parry_buffer = 0
            self.start_parry()

    def take_hit(self, damage, from_x):
        # 피해를 받았으면 True. 무적이면 무시
        if self.is_invincible():
            return False
        if self.is_parry_stunned():
            damage *= config.STUN_DAMAGE_MULT
        self.parry_timer = 0
        self.parry_stun_timer = 0
        self.hp = max(0, self.hp - damage)
        self.hit_timer = config.PLAYER_HIT_STUN
        self.invincible_timer = self.invincible_on_hit
        self.hit_dir = 1 if self.x >= from_x else -1
        # 공격 중이면 끊는다
        self.attack_timer = 0
        self.attack_step = 0
        self.combo_timer = 0
        if self.hp == 0:
            # 결과 화면 전환은 play_mode가 DEATH_DELAY 뒤에 한다
            self.dead = True
            effect.player_dead()
        return True

    def start_dash(self):
        if (self.is_dashing() or self.dash_cooldown > 0 or self.is_hit()
                or self.is_parrying() or self.is_parry_stunned()):
            return
        # 방향키를 누르고 있으면 그쪽으로, 아니면 바라보는 방향으로
        move = self.right_pressed - self.left_pressed
        self.dash_dir = move if move != 0 else self.face_dir
        self.face_dir = self.dash_dir
        self.dash_timer = config.DASH_TIME
        self.dash_cooldown = self.dash_cooldown_time
        self.vy = 0
        sound.play('dash')
        # 공격 중이면 캔슬하고 콤보도 끊는다
        self.attack_timer = 0
        self.attack_step = 0
        self.combo_timer = 0

    def is_attacking(self):
        return self.attack_timer > 0

    def attack_duration(self, step):
        i = step - 1
        return config.ATTACK_STARTUP[i] + config.ATTACK_ACTIVE[i] + config.ATTACK_RECOVER[i]

    def start_attack(self):
        # 콤보 유지 중이면 다음 타, 3타 뒤에는 다시 1타
        self.attack_step = self.attack_step % 3 + 1 if self.attack_step else 1
        self.attack_timer = self.attack_duration(self.attack_step)
        self.combo_timer = 0
        self.attack_hits.clear()
        upgrades.on_attack(self)
        sound.play('swing')
        # 누르고 있는 방향으로 돌아서 공격
        move = self.right_pressed - self.left_pressed
        if move != 0:
            self.face_dir = move
        # 지상 공격은 선딜 동안 바라보는 방향으로 ATTACK_LUNGE만큼 전진 (공중에서는 전진 없음)
        self.lunge_timer = config.ATTACK_STARTUP[self.attack_step - 1] if self.on_ground else 0

    def update_attack(self, dt):
        self.attack_buffer = max(0, self.attack_buffer - dt)
        if self.is_attacking():
            self.attack_timer -= dt
            if self.attack_timer > 0:
                return
            self.attack_timer = 0
            self.combo_timer = config.COMBO_WINDOW
        elif self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.attack_step = 0
        if self.attack_buffer > 0 and not self.is_busy():
            self.attack_buffer = 0
            self.start_attack()

    def attack_damage(self):
        return config.ATTACK_DAMAGE[self.attack_step - 1] * self.attack_mult * self.swing_mult

    def attack_knockback(self):
        return config.ATTACK3_KNOCKBACK if self.attack_step == 3 else config.ATTACK_KNOCKBACK_LIGHT

    def get_attack_bb(self):
        # 판정 구간에서만 몸 앞쪽에 공격 hitbox를 만든다. 아니면 None
        if not self.is_attacking():
            return None
        i = self.attack_step - 1
        elapsed = self.attack_duration(self.attack_step) - self.attack_timer
        start = config.ATTACK_STARTUP[i]
        if not start <= elapsed < start + config.ATTACK_ACTIVE[i]:
            return None
        w, h = config.ATTACK_HITBOX[i]
        half_w = config.PLAYER_W / 2
        if self.face_dir > 0:
            l = self.x + half_w
        else:
            l = self.x - half_w - w
        b = self.y + (config.PLAYER_H - h) / 2
        return l, b, l + w, b + h

    def update(self):
        dt = game_framework.frame_time
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)
        self.hit_timer = max(0, self.hit_timer - dt)
        self.update_parry(dt)
        self.update_attack(dt)

        if self.dead or self.is_parry_stunned():
            self.vx = 0
            move_dt = dt
        elif self.is_hit():
            # 경직 중에는 조작 없이 맞은 반대쪽으로 밀려난다
            self.vx = self.hit_dir * config.PLAYER_HIT_KNOCKBACK
            move_dt = dt
        elif self.is_dashing():
            # 마지막 프레임은 남은 시간만큼만 이동해서 이동 거리를 DASH_DIST에 맞춘다
            step = min(dt, self.dash_timer)
            self.dash_timer -= step
            self.vx = self.dash_dir * self.dash_dist / config.DASH_TIME
            self.vy = 0
            move_dt = step
            if self.dash_timer <= 0:
                upgrades.on_dash_end(self)
        elif self.is_attacking() and self.lunge_timer > 0:
            # 마지막 프레임은 남은 시간만큼만 이동해서 전진 거리를 ATTACK_LUNGE에 맞춘다
            i = self.attack_step - 1
            step = min(dt, self.lunge_timer)
            self.lunge_timer -= step
            self.vx = self.face_dir * config.ATTACK_LUNGE[i] / config.ATTACK_STARTUP[i]
            move_dt = step
        else:
            move = self.right_pressed - self.left_pressed
            if self.is_attacking() or self.is_parrying():
                # 지상 공격·패링은 제자리, 공중에서는 이동 유지 (방향은 고정)
                self.vx = 0 if self.on_ground else move * config.PLAYER_SPEED
            else:
                self.vx = move * config.PLAYER_SPEED
                if move != 0:
                    self.face_dir = move
            move_dt = dt

        # 지형 충돌은 X 이동 → X 해결 → Y 이동 → Y 해결 순서로 분리
        self.x += self.vx * move_dt
        self.x = terrain.resolve_x(self.x, self.y, config.PLAYER_W, config.PLAYER_H, self.platforms)
        half_w = config.PLAYER_W / 2
        self.x = clamp(half_w, self.x, config.SCREEN_W - half_w)

        if not self.is_dashing():
            self.vy += config.GRAVITY * dt
        prev_y = self.y
        self.y += self.vy * dt
        self.y, self.vy, self.on_ground = terrain.resolve_y(
            self.x, prev_y, self.y, self.vy, config.PLAYER_W, config.PLAYER_H, self.platforms)
        if self.on_ground:
            self.jumps_left = self.max_jumps - 1

    def is_blink_hidden(self):
        # 피격 무적 중에는 BLINK_INTERVAL마다 숨겼다 보였다 한다
        if self.dead or self.invincible_timer <= 0:
            return False
        return int(self.invincible_timer / config.BLINK_INTERVAL) % 2 == 1

    def draw(self):
        l, b, r, t = self.get_bb()
        attack_bb = self.get_attack_bb()
        if not self.is_blink_hidden():
            if self.dead:
                color = config.COLOR_PLAYER_DEAD
            elif self.is_dashing():
                color = config.COLOR_PLAYER_DASH
            elif self.is_parry_stunned():
                color = config.COLOR_PLAYER_STUN
            else:
                color = config.COLOR_PLAYER
            draw_rectangle(l, b, r, t, *color, filled=True)
            if self.is_parrying():
                # 몸 앞쪽에 방패 표시
                sx = r if self.face_dir > 0 else l - config.PARRY_SHIELD_W
                draw_rectangle(sx, b, sx + config.PARRY_SHIELD_W, t, *config.COLOR_PLAYER_PARRY, filled=True)
            # 바라보는 방향 표시
            eye_x = self.x + self.face_dir * config.PLAYER_W / 4
            eye = config.PLAYER_W / 8
            draw_rectangle(eye_x - eye / 2, t - eye * 3, eye_x + eye / 2, t - eye * 2, *config.COLOR_TEXT, filled=True)
            if attack_bb:
                draw_rectangle(*attack_bb, *config.COLOR_PLAYER_SLASH, filled=True)
        if game_world.show_hitbox:
            draw_rectangle(l, b, r, t, *config.COLOR_DEBUG_BODY)
            if attack_bb:
                draw_rectangle(*attack_bb, *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        half_w = config.PLAYER_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.PLAYER_H

    def handle_collision(self, group, other):
        pass
