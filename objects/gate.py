import math

from pico2d import get_time

import config
import game_framework
import game_world
from objects import effect
from objects.npc import Npc
from systems import camera


class Gate:
    # 닫혀 있는 동안 지형으로 길을 막는 문 (12.6). 열리면 world_state.opened에 남고 다시 만들지 않는다 (5.6)
    # lever_gate: 연결된 레버(objects/switch.py)가 연다. one_way: open_from 쪽에서 곡괭이로 치면 열린다 (숏컷)
    # arena: 보스 아레나 돌문 (11.2). 평소 열려 있고(kind None) 아레나 트리거가 닫는다(close).
    #   플레이어 사망·보스 처치 때 열리며 opened에 남기지 않는다 (방에 들어올 때마다 열린 채로 만든다)
    # shadow_curtain: 그림자 장막 (12.6). 열리지 않고 늘 지형으로 막지만, 플레이어가 그림자 질풍 중이면 지나간다
    #   (objects/player.py move_x가 질풍 중에 장막을 빼고 충돌한다). 적·투사체 판정과 곡괭이에는 벽
    # seal: 봉인문 (T57). 가까이에서 ↑(play_mode.check_seals) → 봉인 핵이 SEAL_CORES_REQUIRED개면 핵을 하나씩 끼우는
    #   연출(플레이어 컷신 = 조작·숨 정지) 뒤 열려 opened에 남는다. 모자라면 몇 개 있는지 알림만
    # kind = 'solid'는 systems/terrain.py가 보는 값이고 문 종류는 type
    KINDS = ('lever_gate', 'one_way', 'arena', 'shadow_curtain', 'seal')

    def __init__(self, room_id, x, y, w, h, type, obj_id, props, state):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.type = type
        self.kind = None if type == 'arena' else 'solid'
        self.gid = f'{room_id}:{obj_id}'
        self.open_from = props.get('open_from')
        self.state = state
        self.prompt = False      # 봉인문: ↑로 상호작용할 수 있으면 문 위에 ↑ 표시 (play_mode가 매 프레임 정함)
        self.inserting = None    # 봉인문: 핵을 끼우는 중이면 지난 시간 (s), 아니면 None
        self.player = None       # 봉인문: 연출 중 멈춰 둔 플레이어

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y

    @property
    def top(self):
        return self.y + self.h

    def update(self):
        if self.inserting is None:
            return
        # 봉인문 연출: 핵을 insert_each마다 하나씩 끼우고, 다 끼운 뒤 open_delay 뒤 열린다
        spec = config.SEAL
        before = self.cores_lit()
        self.inserting += game_framework.frame_time
        if self.cores_lit() > before:
            cx, _ = self.slot_pos(before)
            effect.burst(cx, self.y + self.h / 2, config.DOOR_SPARK, self.core_color(before))
            camera.shake(spec['shake'] / 2, 0.15)
        if self.inserting >= spec['insert_each'] * config.SEAL_CORES_REQUIRED + spec['open_delay']:
            self.inserting = None
            camera.shake(spec['shake'], 0.4)
            self.player.end_cutscene()
            self.open()

    def can_unseal(self, player):
        # 봉인문 테두리에서 SEAL.reach 안, 땅에 서 있고 조작할 수 있을 때 ↑ (play_mode.check_seals)
        if self.type != 'seal' or self.kind is None or self.inserting is not None:
            return False
        if not player.on_ground or player.is_locked():
            return False
        reach = config.SEAL['reach']
        l, b, r, t = player.get_bb()
        return l < self.right + reach and r > self.left - reach and b < self.top + reach and t > self.bottom - reach

    def unseal(self, player):
        # 핵이 다 있으면 끼우는 연출 시작 (True), 모자라면 False
        if len(self.state.cores) < config.SEAL_CORES_REQUIRED:
            return False
        self.inserting = 0.0
        self.player = player
        self.prompt = False
        player.start_cutscene()
        return True

    def cores_lit(self):
        # 지금 빛나는 핵 홈 수 (연출 중이 아니면 0)
        if self.inserting is None:
            return 0
        return min(config.SEAL_CORES_REQUIRED, int(self.inserting / config.SEAL['insert_each']))

    def core_color(self, i):
        # i번째 홈에 끼우는 핵 색 (가진 핵을 BOSS_CORE 순서로)
        order = [c for c in config.BOSS_CORE.values() if c in self.state.cores]
        return config.COLOR_SEAL_CORE.get(order[i] if i < len(order) else None, config.COLOR_SEAL_EDGE)

    def slot_pos(self, i):
        # 핵 홈 i의 중심. 문 가운데 줄에 긴 쪽을 따라 slot_gap 간격
        n = config.SEAL_CORES_REQUIRED
        offset = (i - (n - 1) / 2) * config.SEAL['slot_gap']
        cx, cy = self.x + self.w / 2, self.y + self.h / 2
        return (cx + offset, cy) if self.w >= self.h else (cx, cy + offset)

    def open(self):
        if self.kind is None:
            return
        self.kind = None
        effect.door_opened(self.x + self.w / 2, self.y + self.h / 2)
        if self.type == 'arena':
            return   # 월드에 남겨 두고 다시 닫을 수 있게 한다
        self.state.opened.add(self.gid)
        game_world.remove_object(self)

    def close(self):
        # 아레나 문만 닫힌다 (아레나 트리거)
        if self.kind is not None:
            return
        self.kind = 'solid'
        effect.door_opened(self.x + self.w / 2, self.y + self.h / 2)

    def player_on_open_side(self, player):
        # 몸 중심이 문 중심에서 open_from 쪽에 있는가
        cx, cy = self.x + self.w / 2, self.y + self.h / 2
        side = dict(left=player.x < cx, right=player.x > cx,
                    down=player.y + config.PLAYER_H / 2 < cy, up=player.y + config.PLAYER_H / 2 > cy)
        return side.get(self.open_from, False)

    def on_pickaxe_hit(self, player):
        # 문은 어느 쪽에서 쳐도 단단한 벽처럼 맞는다 (반동·스파크). 한쪽 문은 open_from 쪽에서 치면 열린다
        if self.kind is None:
            return False
        if self.type == 'one_way' and self.player_on_open_side(player):
            self.open()
        return True

    def draw(self):
        if self.kind is None:
            return   # 열린 아레나 문
        if self.type == 'shadow_curtain':
            self.draw_curtain()
            return
        if self.type == 'seal':
            self.draw_seal()
            return
        l, b, r, t = self.get_bb()
        color = config.COLOR_ARENA_GATE if self.type == 'arena' else config.COLOR_GATE
        camera.draw_rect(l, b, r, t, *color, filled=True)
        # 창살: 긴 쪽을 따라 GATE_BAR_GAP 간격
        gap = config.GATE_BAR_GAP
        if self.h >= self.w:
            for x in range(int(l + gap / 2), int(r), gap):
                camera.draw_rect(x - 2, b, x + 2, t, *config.COLOR_GATE_BAR, filled=True)
        else:
            for y in range(int(b + gap / 2), int(t), gap):
                camera.draw_rect(l, y - 2, r, y + 2, *config.COLOR_GATE_BAR, filled=True)
        if self.type == 'one_way':
            self.draw_open_mark()
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def draw_curtain(self):
        # 그림자 장막: 짙은 반투명 막 + 세로로 흔들리는 그림자 실
        spec = config.SHADOW_CURTAIN
        l, b, r, t = self.get_bb()
        effect.draw_alpha_rect(l, b, r, t, config.COLOR_SHADOW_CURTAIN, spec['alpha'])
        half = spec['strand_w'] / 2
        now = get_time() * spec['sway_speed']
        step = spec['strand_gap']
        for i, x in enumerate(range(int(l + step / 2), int(r), step)):
            for y in range(int(b), int(t), step):
                dx = math.sin(now + i + y / 40) * spec['sway']
                sx = min(max(x + dx, l + half), r - half)
                camera.draw_rect(sx - half, y, sx + half, y + step * 0.7, *config.COLOR_SHADOW_STRAND, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def draw_seal(self):
        # 봉인문: 금빛 석판 + 테두리 + 가운데 핵 홈 SEAL_CORES_REQUIRED개 (끼운 핵은 빛남)
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *config.COLOR_SEAL, filled=True)
        camera.draw_rect(l, b, r, t, *config.COLOR_SEAL_EDGE)
        camera.draw_rect(l + 4, b + 4, r - 4, t - 4, *config.COLOR_SEAL_EDGE)
        lit = self.cores_lit()
        for i in range(config.SEAL_CORES_REQUIRED):
            x, y = self.slot_pos(i)
            effect.draw_disc(x, y, config.SEAL['slot_r'], config.COLOR_SEAL_EDGE)
            effect.draw_disc(x, y, config.SEAL['slot_r'] - 4, self.core_color(i) if i < lit else config.COLOR_SEAL_SLOT)
        if self.prompt:
            Npc.draw_prompt(self, self.x + self.w / 2, t + config.SEAL['prompt_h'])
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def draw_open_mark(self):
        # 열리는 쪽 가장자리에 밝은 띠 (어느 쪽에서 치면 열리는지 알려 준다)
        l, b, r, t = self.get_bb()
        band = config.GATE_BAR_GAP / 4
        rect = dict(left=(l, b, l + band, t), right=(r - band, b, r, t),
                    down=(l, b, r, b + band), up=(l, t - band, r, t)).get(self.open_from)
        if rect:
            camera.draw_rect(*rect, *config.COLOR_ONE_WAY_MARK, filled=True)

    def get_bb(self):
        return self.left, self.bottom, self.right, self.top

    def handle_collision(self, group, other):
        pass
