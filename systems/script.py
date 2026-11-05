# 트리거 · 컷신 (2.2 도입부, 11.2 보스 아레나). 엔딩은 T60에서 여기에 더한다
# 방 JSON triggers [x, y, w, h, 스크립트 이름, id] → 트리거 객체. 몸이 처음 닿으면 enter()를 한 번 부른다 (방에 들어올 때마다 다시)
# 도입부 스크립트(omen·collapse·fall·fall_end)는 flags 'intro_done'이 없을 때만 동작한다 (이어하기에서는 재생 안 함)
# sign·hint·fall_backdrop·air_shaft는 방 꾸미기·안내라 늘 동작한다
# 도입부 흐름: R0_01 작업 → R0_02 이상 징후(omen) → R0_03 붕괴(collapse) → 바닥이 꺼짐(fall, 입력 잠금)
#   → R0_04 추락(fall_end에서 암전) → R1_01 깨어남(rest_seat 자동 저장, 숨 게이지 등장) → R1_02 첫 밀폐

import math
import random

from pico2d import get_time

import config
import game_framework
import game_world
from objects import effect
from systems import camera, sound, world
from ui import font, hud

INTRO_FLAG = 'intro_done'
NO_DEATH_REGION = 'mine'   # 광산(R0)에는 사망이 없다 (13.6)
WIDE_CHAR = 0x2FFF         # 이 코드값보다 큰 글자(한글 등)는 글자 크기만큼, 나머지는 SIGN narrow 비율로 폭을 어림한다

player = None
room = None
collapse = None   # 지금 방의 붕괴 트리거 (진행 중이면 낙석에 맞거나 무너짐에 잡혔을 때 장면 처음부터)
scene = None      # 추락 끝 컷신: None | 'black'(암전 → 깨어나는 방으로) | 'wake'(깨어나며 밝아짐)
timer = 0.0
hold = 0.0        # 깨어나는 방에 도착한 뒤 검은 화면 시간


def init():
    global player, room, collapse, scene, timer, hold
    player, room, collapse = None, None, None
    scene, timer, hold = None, 0.0, 0.0


def intro_done():
    return INTRO_FLAG in world.state.flags


def text(trigger_id):
    ko, en = config.INTRO_TEXT.get(trigger_id, (trigger_id, trigger_id))
    return font.text(ko, en)


def enter_room(new_room, new_player):
    # play_mode.enter_room이 다른 객체보다 먼저 부른다 (트리거 그림이 배경 쪽에 오게)
    global player, room, collapse
    player, room, collapse = new_player, new_room, None
    player.min_hp = 1 if room.region == NO_DEATH_REGION else 0
    triggers = [TRIGGERS[t[4]](*t[:4], t[5]) for t in room.triggers if t[4] in TRIGGERS]
    game_world.add_objects(triggers, config.DEPTH_BG)


def on_hazard():
    # 환경 피해 대신 스크립트가 처리하면 True (붕괴 중 낙석 = 장면 처음부터, 피해 없음)
    if collapse and collapse.running:
        collapse.restart()
        return True
    return False


def update(dt):
    # play_mode.update가 방 전환 정지보다 먼저 부른다 (암전 중 방을 옮기는 동안에도 시간이 간다)
    global scene, timer, hold
    if scene == 'black':
        timer += dt
        wake_room, wake_zone = config.INTRO_WAKE_ZONE.split(':')
        if room.id != wake_room:
            if timer >= config.INTRO['black_fade'] and world.phase is None:
                world.warp(wake_room, zone=wake_zone)
        elif world.phase is None:
            hold += dt
            if hold >= config.INTRO['black_hold']:
                wake()
    elif scene == 'wake':
        timer += dt
        if timer >= config.INTRO['wake_fade']:
            scene = None
            player.end_cutscene()
            hud.show_message(text('hint_safe'), config.INTRO['hint_time'])


def start_black():
    global scene, timer, hold
    scene, timer, hold = 'black', 0.0, 0.0
    hud.hide_breath = True


def wake():
    # 5. 깨어남 (2.2): 부활 지점을 깨어나는 안전지대로 정하고 자동 저장 → 숨 게이지가 처음 나타남
    global scene, timer
    from modes import play_mode
    state = world.state
    state.rest_seat = config.INTRO_WAKE_ZONE
    state.safe_zones_found.add(config.INTRO_WAKE_ZONE)
    state.flags.add(INTRO_FLAG)
    play_mode.save_game()
    hud.hide_breath = False
    scene, timer = 'wake', 0.0


def fade_alpha():
    if scene == 'black':
        return 255 * min(1.0, timer / config.INTRO['black_fade'])
    if scene == 'wake':
        return 255 * max(0.0, 1 - timer / config.INTRO['wake_fade'])
    return 0


# ---------- 트리거 ----------

class Trigger:
    intro_only = False

    def __init__(self, x, y, w, h, trigger_id):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.id = trigger_id
        self.fired = False

    def update(self):
        if self.fired or (self.intro_only and intro_done()) or player.dead:
            return
        if game_world.collide(player, self):
            self.fired = True
            self.enter()

    def enter(self):
        pass

    def draw(self):
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *config.COLOR_DEBUG_EXIT)

    def get_bb(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def handle_collision(self, group, other):
        pass


class Sign(Trigger):
    # 벽 간판에 키 안내 (2.2 장면 1·2). 트리거 영역 가운데 위에 나무 간판, 글은 INTRO_TEXT[id]
    def draw(self):
        spec = config.SIGN
        size = config.FONT_SIZE_TEXT
        label = text(self.id)
        width = sum(size if ord(c) > WIDE_CHAR else size * spec['narrow'] for c in label) + spec['pad'] * 2
        cx = self.x + self.w / 2
        b = self.y + spec['y']
        t = b + spec['line_h'] + spec['pad']
        camera.draw_rect(cx - spec['post_w'] / 2, self.y, cx + spec['post_w'] / 2, b, *config.COLOR_SIGN, filled=True)
        camera.draw_rect(cx - width / 2, b, cx + width / 2, t, *config.COLOR_SIGN, filled=True)
        f = font.get(size)
        if f:
            sx, sy = camera.to_screen(cx - width / 2 + spec['pad'], (b + t) / 2)
            f.draw(sx, sy, label, config.COLOR_SIGN_TEXT)
        super().draw()


class Hint(Trigger):
    # 처음 들어온 방에서만 HUD에 안내 문구 (2.2 장면 6 '숨은 줄어든다')
    def enter(self):
        if world.first_visit:
            hud.show_message(text(self.id), config.INTRO['hint_time'])


class Omen(Trigger):
    # 2. 이상 징후: 멀리서 울림 + 박쥐 떼가 반대쪽(왼쪽)으로 날아감
    intro_only = True

    def enter(self):
        camera.shake(*config.INTRO['omen_shake'])
        sound.play('door')
        spec = config.INTRO['bats']
        right = camera.x + config.SCREEN_W
        bats = [Bat(right + random.uniform(0, spec['spread']),
                    camera.y + config.SCREEN_H * random.uniform(*spec['height']),
                    random.uniform(*spec['speed']), i * spec['delay'] / spec['count'])
                for i in range(spec['count'])]
        game_world.add_objects(bats, config.DEPTH_EFFECT)


class Bat:
    # 박쥐 떼 한 마리 (연출만, 판정 없음). 왼쪽으로 날아가 화면을 벗어나면 사라진다
    def __init__(self, x, y, speed, delay):
        self.x, self.y = x, y
        self.speed = speed
        self.delay = delay
        self.phase = random.uniform(0, math.pi * 2)

    def update(self):
        dt = game_framework.frame_time
        if self.delay > 0:
            self.delay -= dt
            return
        self.x -= self.speed * dt
        spec = config.INTRO['bats']
        self.y += math.sin(get_time() * spec['bob_speed'] + self.phase) * spec['bob'] * dt
        if self.x < camera.x - config.SCREEN_W / 2:
            game_world.remove_object(self)

    def draw(self):
        spec = config.INTRO['bats']
        w, h = spec['w'], spec['h']
        up = int((get_time() + self.phase) / spec['flap']) % 2
        camera.draw_rect(self.x - w / 4, self.y - h / 2, self.x + w / 4, self.y + h / 2, *config.COLOR_BAT_SWARM,
                         filled=True)
        wing_y = self.y + (h / 2 if up else -h / 2)
        camera.draw_rect(self.x - w, wing_y - 2, self.x + w, wing_y + 2, *config.COLOR_BAT_SWARM, filled=True)

    def handle_collision(self, group, other):
        pass


class Collapse(Trigger):
    # 3. 붕괴: 왼쪽에서 무너짐이 쫓아온다. 강한 흔들림, 낙석 함정은 가까이 가면 빨간 그림자 예고 후 떨어진다
    # 무너짐에 잡히거나 낙석에 맞으면 장면 처음부터 (피해 없음, 2.2)
    intro_only = True

    def __init__(self, *args):
        super().__init__(*args)
        self.running = False
        self.front = 0.0      # 무너진 곳의 오른쪽 끝 x
        self.rubble = 0.0     # 다음 흙덩이까지 남은 개수 누적

    def enter(self):
        global collapse
        collapse = self
        self.running = True
        self.front = player.x - config.INTRO['collapse_lead']
        sound.play('door')

    def stop(self):
        self.running = False

    def restart(self):
        # 같은 방을 다시 불러온다 (방 객체·낙석·바닥이 처음 상태로, 트리거도 다시)
        if world.phase is None:
            self.running = False
            world.warp(room.id)

    def update(self):
        super().update()
        if not self.running:
            return
        dt = game_framework.frame_time
        spec = config.INTRO
        self.front += spec['collapse_speed'] * dt
        camera.shake(*spec['collapse_shake'])
        self.drop_rubble(dt)
        if player.x - config.PLAYER_W / 2 < self.front:
            self.restart()

    def drop_rubble(self, dt):
        spec = config.INTRO['collapse_rubble']
        self.rubble += spec['rate'] * dt
        while self.rubble >= 1:
            self.rubble -= 1
            x = self.front + random.uniform(0, spec['spread'])
            size = random.uniform(*spec['w'])
            game_world.add_object(effect.Particle(x, room.height, spec['speed'], spec['life'], size, config.COLOR_COLLAPSE,
                                                  -math.pi / 2), config.DEPTH_EFFECT)

    def draw(self):
        if self.running and self.front > 0:
            camera.draw_rect(0, 0, self.front, room.height, *config.COLOR_COLLAPSE, filled=True)
        super().draw()


class Fall(Trigger):
    # 4. 추락 시작: 바닥이 꺼지고 입력을 잠근다. 트리거와 가로로 겹치고 트리거 아래에 있는 발판을 없앤다
    # (트리거는 꺼지는 바닥보다 좁게 둬서 몸이 바닥 위에 온전히 올라왔을 때 닿게 한다)
    intro_only = True

    def enter(self):
        if collapse:
            collapse.stop()
        player.start_cutscene()
        player.vx = 0.0
        gone = [p for p in room.terrain if p in room.platforms and p.x < self.x + self.w and self.x < p.x + p.w
                and p.y + p.h <= self.y]
        for p in gone:
            room.terrain.remove(p)
            game_world.remove_object(p)
            effect.burst(p.x + p.w / 2, p.y + p.h, config.WALL_DEBRIS, config.COLOR_COLLAPSE)
        camera.shake(*config.INTRO['fall_shake'])
        sound.play('door')


class FallEnd(Trigger):
    # 4. 추락 끝: 암전 → 깨어나는 방으로 (update가 이어서 처리)
    intro_only = True

    def enter(self):
        start_black()


class FallBackdrop(Trigger):
    # 추락 갱 배경: 위에서 아래로 흙 → 암반 → 고대 석벽 (트리거 영역을 세로로 나눠 칠한다)
    def draw(self):
        colors = config.INTRO_SHAFT_COLORS
        band = self.h / len(colors)
        for i, color in enumerate(colors):
            t = self.y + self.h - i * band
            camera.draw_rect(self.x, t - band, self.x + self.w, t, *color, filled=True)
        super().draw()


class AirShaft(Trigger):
    # 깨어나는 방 위 무너진 구멍으로 희미하게 드는 바깥 공기 (2.2 장면 5)
    def draw(self):
        effect.draw_alpha_rect(*self.get_bb(), config.COLOR_BREATH_REFILL, config.INTRO['shaft_alpha'])
        super().draw()


class Arena(Trigger):
    # 보스 아레나 (11.2): 몸이 닿으면 출구의 아레나 돌문이 닫히고 보스 등장 (첫 만남이면 타이틀 카드)
    # 플레이어가 죽으면 문이 열린다. 보스가 쓰러지면 문 열림 → play_mode.on_boss_defeated (안전지대·기록·저장)
    # 처치한 아레나는 보스가 없으므로 아무것도 하지 않는다 (문은 열린 채)
    def __init__(self, *args):
        super().__init__(*args)
        self.done = False

    def boss(self):
        from modes import play_mode
        return play_mode.boss

    def update(self):
        boss = self.boss()
        if boss is None or self.done:
            return
        if not self.fired:
            super().update()
        elif not boss.is_alive():
            self.done = True
            self.open_gates()
            from modes import play_mode
            play_mode.on_boss_defeated(boss)
        elif player.dead:
            self.open_gates()

    def enter(self):
        boss = self.boss()
        if not boss.is_dormant():
            return
        for gate in room.arena_gates:
            gate.close()
        met = world.state.bosses_met
        first = boss.boss_key not in met
        met.add(boss.boss_key)
        boss.wake(first)
        print(f"[보스] {boss.boss_key} 등장 ({'첫 만남' if first else '재도전'})")

    def open_gates(self):
        for gate in room.arena_gates:
            gate.open()


TRIGGERS = dict(sign=Sign, hint=Hint, omen=Omen, collapse=Collapse, fall=Fall, fall_end=FallEnd,
                fall_backdrop=FallBackdrop, air_shaft=AirShaft, arena=Arena)
