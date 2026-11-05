import math
import random

import pico2d.pico2d as canvas  # open_canvas 이후 renderer가 여기 생긴다
from pico2d import *
from sdl2 import SDL_BLENDMODE_BLEND, SDL_RenderDrawLine, SDL_SetRenderDrawBlendMode, SDL_SetRenderDrawColor

import config
import game_framework
import game_world
from systems import camera, hitstop, sound


def draw_screen_alpha_rect(l, b, r, t, color, alpha):
    # 화면 좌표 반투명 사각형 (화면 전체 섬광·페이드)
    SDL_SetRenderDrawBlendMode(canvas.renderer, SDL_BLENDMODE_BLEND)
    draw_rectangle(l, b, r, t, *color, int(alpha), filled=True)


def draw_alpha_rect(l, b, r, t, color, alpha):
    # 월드 좌표 반투명 사각형
    draw_screen_alpha_rect(*camera.rect(l, b, r, t), color, alpha)


def draw_alpha_line(x1, y1, x2, y2, color, alpha, width):
    # 월드 좌표 선. pico2d에는 선 그리기가 없어 SDL을 직접 부른다. 굵기는 수직 방향으로 1px씩 겹쳐 그린다
    x1, y1 = camera.to_screen(x1, y1)
    x2, y2 = camera.to_screen(x2, y2)
    SDL_SetRenderDrawBlendMode(canvas.renderer, SDL_BLENDMODE_BLEND)
    SDL_SetRenderDrawColor(canvas.renderer, *color, int(alpha))
    length = math.hypot(x2 - x1, y2 - y1) or 1
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length
    top = config.SCREEN_H - 1  # pico2d는 y가 위로, SDL은 아래로 증가
    for i in range(int(width)):
        o = i - (width - 1) / 2
        SDL_RenderDrawLine(canvas.renderer, int(x1 + nx * o), int(top - (y1 + ny * o)),
                           int(x2 + nx * o), int(top - (y2 + ny * o)))


def draw_disc(x, y, radius, color):
    # 월드 좌표. pico2d에는 원 그리기가 없어 가로 띠를 쌓아 채운 원을 그린다
    step = config.DISC_STEP
    rows = max(1, int(radius * 2 / step))
    for i in range(rows):
        dy = -radius + (i + 0.5) * radius * 2 / rows
        half = math.sqrt(max(0, radius * radius - dy * dy))
        camera.draw_rect(x - half, y + dy - step / 2, x + half, y + dy + step / 2, *color, filled=True)


def draw_ring(x, y, rx, ry, dots, size, color):
    # 점 dots개로 타원 테두리를 그린다 (ry를 작게 주면 바닥에 눕힌 원)
    half = size / 2
    for i in range(dots):
        angle = 2 * math.pi * i / dots
        px, py = x + rx * math.cos(angle), y + ry * math.sin(angle)
        camera.draw_rect(px - half, py - half, px + half, py + half, *color, filled=True)


class ScreenFlash:
    # 화면 전체를 덮었다가 서서히 사라지는 섬광 (화면 좌표, 흔들리지 않는다)
    def __init__(self, color, alpha, time):
        self.color, self.alpha, self.time = color, alpha, time
        self.timer = time

    def update(self):
        self.timer -= game_framework.frame_time
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self):
        if self.timer > 0:
            draw_screen_alpha_rect(-config.SCREEN_W, -config.SCREEN_H, config.SCREEN_W * 2, config.SCREEN_H * 2,
                            self.color, self.alpha * self.timer / self.time)


class BorderFlash(ScreenFlash):
    # 화면 테두리만 물드는 플래시 (플레이어 피격)
    def __init__(self, color, alpha, time, thickness):
        super().__init__(color, alpha, time)
        self.thickness = thickness

    def draw(self):
        if self.timer <= 0:
            return
        alpha = self.alpha * self.timer / self.time
        w, h, d = config.SCREEN_W, config.SCREEN_H, self.thickness
        draw_screen_alpha_rect(-w, -h, w * 2, d, self.color, alpha)
        draw_screen_alpha_rect(-w, h - d, w * 2, h * 2, self.color, alpha)
        draw_screen_alpha_rect(-w, d, d, h - d, self.color, alpha)
        draw_screen_alpha_rect(w - d, d, w * 2, h - d, self.color, alpha)


class ScreenFade:
    # fade초 동안 어두워졌다가 다시 fade초 동안 밝아진다 (환경 피해 → 안전 지점 복귀)
    def __init__(self, fade):
        self.fade = fade
        self.timer = fade * 2

    def update(self):
        self.timer -= game_framework.frame_time
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self):
        if self.timer <= 0:
            return
        alpha = 255 * (1 - abs(self.timer - self.fade) / self.fade)
        draw_screen_alpha_rect(-config.SCREEN_W, -config.SCREEN_H, config.SCREEN_W * 2, config.SCREEN_H * 2,
                        config.COLOR_FADE, max(0, alpha))


def screen_fade(fade):
    game_world.add_object(ScreenFade(fade), config.DEPTH_EFFECT)


class Particle:
    # 사방으로(angle을 주면 그 방향으로) 튀고 중력을 받으며 작아지는 사각형 조각
    def __init__(self, x, y, speed, life, size, color, angle=None):
        if angle is None:
            angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(*speed)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.life = self.timer = life
        self.size = size
        self.color = color

    def update(self):
        dt = game_framework.frame_time
        self.timer -= dt
        if self.timer <= 0:
            game_world.remove_object(self)
            return
        self.vy += config.PARTICLE_GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self):
        if self.timer <= 0:
            return
        half = self.size * self.timer / self.life / 2
        camera.draw_rect(self.x - half, self.y - half, self.x + half, self.y + half, *self.color, filled=True)


class Streak:
    # 중심에서 바깥으로 뻗어 나가며 사라지는 빛줄기 (패링·그로기·처치의 '번쩍' 느낌)
    def __init__(self, x, y, angle, length, life, width, color):
        self.x, self.y = x, y
        self.dx, self.dy = math.cos(angle), math.sin(angle)
        self.length = length
        self.life = self.timer = life
        self.width, self.color = width, color

    def update(self):
        self.timer -= game_framework.frame_time
        if self.timer <= 0:
            game_world.remove_object(self)

    def draw(self):
        if self.timer <= 0:
            return
        k = 1 - self.timer / self.life   # 0 → 1
        inner = self.length * k * k      # 안쪽 끝이 뒤따라 나가며 줄기가 짧아진다
        outer = self.length * math.sqrt(k)
        draw_alpha_line(self.x + self.dx * inner, self.y + self.dy * inner,
                        self.x + self.dx * outer, self.y + self.dy * outer,
                        self.color, 255 * (1 - k), self.width)


def streaks(x, y, spec):
    # 고르게 나눈 각도에 조금씩 흔들림을 줘서 별 모양으로 뻗게 한다
    count = spec['count']
    offset = random.uniform(0, 2 * math.pi)
    game_world.add_objects([Streak(x, y, offset + 2 * math.pi * i / count + random.uniform(-0.2, 0.2),
                                   random.uniform(*spec['length']), spec['life'], spec['width'], spec['color'])
                            for i in range(count)], config.DEPTH_EFFECT)


def burst(x, y, spec, color):
    game_world.add_objects([Particle(x, y, spec['speed'], spec['life'], spec['size'], color)
                            for _ in range(spec['count'])], config.DEPTH_EFFECT)


def parry_success(x, y):
    # (x, y)는 공격과 몸이 맞닿은 지점
    hitstop.start(config.HITSTOP_PARRY)
    camera.shake(config.SHAKE_PARRY, config.SHAKE_PARRY_TIME)
    game_world.add_object(ScreenFlash(config.COLOR_FLASH_PARRY, config.FLASH_PARRY_ALPHA,
                                      config.FLASH_PARRY_TIME), config.DEPTH_EFFECT)
    burst(x, y, config.PARRY_SPARK, config.PARRY_SPARK['color'])
    streaks(x, y, config.PARRY_STREAK)
    sound.play('parry')


def projectile_blocked(x, y, color):
    # 반사 해금 전 패링한 투사체가 튕겨 사라지는 작은 파편
    burst(x, y, config.PROJECTILE_SHARD, color)


def parry_miss(x, y):
    burst(x, y, config.PARRY_MISS_PUFF, config.PARRY_MISS_PUFF['color'])
    sound.play('parry_miss')


def player_hit(x, y):
    camera.shake(config.SHAKE_HIT, config.SHAKE_HIT_TIME)
    game_world.add_object(BorderFlash(config.COLOR_HIT_FLASH, config.HIT_FLASH_ALPHA,
                                      config.HIT_FLASH_TIME, config.HIT_FLASH_BORDER), config.DEPTH_EFFECT)
    burst(x, y, config.HIT_PARTICLE, config.COLOR_HIT_FLASH)
    sound.play('hit')


def player_dead():
    sound.play('death')


def hit_spark(x, y, base, count):
    # 노란 스파크가 공격 방향(base, 라디안)으로 부채꼴로 퍼진다
    spread = math.radians(config.HIT_SPARK_SPREAD)
    speed = (config.HIT_SPARK_SPEED * (1 - config.HIT_SPARK_SPEED_JITTER), config.HIT_SPARK_SPEED)
    game_world.add_objects([Particle(x, y, speed, config.HIT_SPARK_LIFE, config.HIT_SPARK_SIZE,
                                     config.HIT_SPARK_COLOR, base + random.uniform(-spread, spread))
                            for _ in range(count)], config.DEPTH_EFFECT)


def enemy_hurt(x, y, dir_x):
    # 투사체 등 플레이어 근접 공격이 아닌 피해 (히트스톱 없음)
    hit_spark(x, y, 0 if dir_x > 0 else math.pi, config.HIT_SPARK_COUNT)
    sound.play('enemy_hurt')


def attack_hit(x, y, angle, strong, killed):
    # 플레이어 곡괭이 적중. angle은 공격 방향(라디안), strong은 세 번째 일격
    # 여러 적을 맞혀도 히트스톱은 max로 1회분만 걸린다 (처치 히트스톱과도 max)
    hitstop.start(config.HITSTOP_HIT)
    count = config.HIT_SPARK_COUNT
    if strong:
        shake = config.THIRD_STRIKE['shake']
        camera.shake(shake['amp'], shake['time'])
        count *= config.HIT_SPARK_MULT_STRONG
    hit_spark(x, y, angle, count)
    if not killed:
        sound.play('enemy_hurt')  # 처치면 처치음이 따로 난다


def hard_land(x, y):
    # 강착지: 발밑에서 좌우로 큰 먼지 + 작은 흔들림
    spec = config.HARD_LAND_DUST
    spread = math.radians(spec['spread'])

    def angle():
        # 오른쪽(0)이나 왼쪽(pi)에서 위로 spread 이내
        rise = random.uniform(0, spread)
        return rise if random.random() < 0.5 else math.pi - rise

    game_world.add_objects([Particle(x, y, spec['speed'], spec['life'], spec['size'], spec['color'], angle())
                            for _ in range(spec['count'])], config.DEPTH_EFFECT)
    camera.shake(config.HARD_LAND_SHAKE['amp'], config.HARD_LAND_SHAKE['time'])


def enemy_killed(x, y, color):
    hitstop.start(config.HITSTOP_KILL)
    camera.shake(config.SHAKE_KILL, config.SHAKE_KILL_TIME)
    burst(x, y, config.KILL_PARTICLE, color)
    streaks(x, y, config.KILL_STREAK)
    sound.play('kill')


def telegraph(parryable):
    sound.play('telegraph_white' if parryable else 'telegraph_red')


def boss_groggy(x, y):
    hitstop.start_slowmo(config.GROGGY_SLOWMO)
    camera.shake(config.SHAKE_GROGGY, config.SHAKE_GROGGY_TIME)
    game_world.add_object(ScreenFlash(config.COLOR_FLASH_GROGGY, config.FLASH_GROGGY_ALPHA,
                                      config.FLASH_GROGGY_TIME), config.DEPTH_EFFECT)
    streaks(x, y, config.GROGGY_STREAK)
    burst(x, y, config.PARRY_SPARK, config.COLOR_FLASH_GROGGY)
    sound.play('groggy')


def boss_phase2(x, y, color):
    camera.shake(config.SHAKE_PARRY, config.SHAKE_PARRY_TIME)
    game_world.add_object(ScreenFlash(color, config.FLASH_GROGGY_ALPHA, config.FLASH_GROGGY_TIME),
                          config.DEPTH_EFFECT)
    burst(x, y, config.KILL_PARTICLE, color)
    streaks(x, y, dict(config.GROGGY_STREAK, color=color))
    sound.play('phase2')


def door_opened(x, y):
    burst(x, y, config.DOOR_SPARK, config.COLOR_DOOR_OPEN)
    sound.play('door')
