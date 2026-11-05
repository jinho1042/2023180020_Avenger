import config
import game_framework
import game_world
from objects import effect, pickup
from systems import camera


class Breakable:
    # 곡괭이로 부수는 벽·덩어리 (12.6). 부서지기 전에는 지형으로 플레이어·적·투사체를 막는다
    # kind = 'solid'는 systems/terrain.py가 보는 값이고 기믹 종류는 type. 부서지면 kind = None (지형에서 빠짐)
    # 무른 흙벽(soil)은 곡괭이로는 안 부서지고 굴착 대시로 닿으면 파고 통과한다 (6.4, player.dig_soil)
    # 단단한 흙벽(hard_soil)은 굴착 Lv3 대시로, 깨지는 바닥(floor)은 낙반 착지로만 부서진다 (12.6, T51)
    # 광맥벽·결정 숨주머니는 해당 작업에서
    KINDS = ('crack', 'ore_chunk', 'soil', 'hard_soil', 'floor')
    DIGGABLE = ('soil', 'hard_soil', 'floor')   # 곡괭이로는 안 부서지고 룬 동작(dig)으로만

    def __init__(self, room_id, x, y, w, h, type, obj_id, state):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.type = type
        self.kind = 'solid'
        self.gid = f'{room_id}:{obj_id}'
        self.state = state
        self.max_hits = config.CRACK_WALL_HITS if type == 'crack' else config.ORE_CHUNK_HITS
        # 친 횟수는 방을 나갔다 와도 유지한다 (광석 덩어리를 나갔다 오며 반복해서 캐지 못하게)
        self.hits = state.mined.get(self.gid, 0)
        self.time = 0.0   # 바람 단서 애니메이션

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
        self.time += game_framework.frame_time

    def on_pickaxe_hit(self, player):
        # 반환: 이번 휘두름이 이 대상에 '맞았는가' (combat이 반동·포고·스파크를 처리)
        if self.kind is None:
            return False
        if self.type in self.DIGGABLE:
            return True   # 흙벽·깨지는 바닥은 곡괭이로 부서지지 않는다 (반동·포고만)
        self.hits += 1
        self.state.mined[self.gid] = self.hits
        cx, cy = self.x + self.w / 2, self.y + self.h / 2
        if self.type == 'ore_chunk':
            # 칠 때마다 광석이 튀어나온다
            pickup.spill(cx, cy, config.ORE_PER_CHUNK_HIT, player)
            effect.ore_mined(cx, cy)
        if self.hits >= self.max_hits:
            self.destroy()
        return True

    def dig(self):
        # 굴착 대시로 흙벽을 파고 지나감 / 낙반으로 깨지는 바닥을 부숨 (12.6). 다시 메워지지 않는다 (영구)
        # 레벨 확인(단단한 흙벽 = 굴착 Lv3)은 부르는 쪽(player)이 한다
        if self.kind is not None and self.type in self.DIGGABLE:
            self.destroy()

    def destroy(self):
        self.kind = None
        self.state.broken.add(self.gid)
        self.state.mined.pop(self.gid, None)
        game_world.remove_object(self)
        effect.wall_broken(self.x + self.w / 2, self.y + self.h / 2, self.color())

    def color(self):
        return {'crack': config.COLOR_CRACK_WALL, 'soil': config.COLOR_SOIL, 'hard_soil': config.COLOR_HARD_SOIL,
                'floor': config.COLOR_FRAGILE_FLOOR}.get(self.type, config.COLOR_ORE_CHUNK)

    def draw(self):
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *self.color(), filled=True)
        if self.type == 'crack':
            self.draw_crack()
            self.draw_wind()
        elif self.type == 'soil':
            self.draw_soil(config.SOIL_DOTS, config.COLOR_SOIL_DOT)
        elif self.type == 'hard_soil':
            self.draw_soil(config.HARD_SOIL_DOTS, config.COLOR_HARD_SOIL_DOT)
        elif self.type == 'floor':
            self.draw_floor()
        else:
            self.draw_ore()
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def draw_crack(self):
        # 가운데 세로 균열. 칠수록 갈라진 마디가 늘어난다
        segments = 2 + self.hits * 2
        seg_h = self.h / segments
        cx = self.x + self.w / 2
        for i in range(segments):
            offset = self.w / 6 * (1 if i % 2 else -1)
            sb = self.y + i * seg_h
            camera.draw_rect(cx + offset - 2, sb, cx + offset + 2, sb + seg_h, *config.COLOR_CRACK_LINE, filled=True)

    def draw_wind(self):
        # 바람 단서 (7.5): 벽 양옆의 먼지가 균열로 빨려 들어간다 (뒤에 공기가 있다는 표시)
        if not camera.visible(self.get_bb()):
            return
        wind = config.CRACK_WIND
        half = wind['size'] / 2
        cx = self.x + self.w / 2
        for i in range(wind['count']):
            phase = (self.time / wind['period'] + i / wind['count']) % 1
            side = 1 if i % 2 else -1
            x = cx + side * (self.w / 2 + wind['dist'] * (1 - phase))
            y = self.y + self.h * (i + 1) / (wind['count'] + 1)
            camera.draw_rect(x - half, y - half, x + half, y + half, *config.COLOR_CRACK_WIND, filled=True)

    def draw_soil(self, dots, color):
        # 흙덩이 점을 엇갈린 격자로 (균열벽과 구별되게). 단단한 흙벽은 더 촘촘하고 굵은 점
        half = dots['size'] / 2
        row = 0
        y = self.y + dots['step'] / 2
        while y < self.top:
            x = self.x + dots['step'] / (2 if row % 2 else 4)
            while x < self.right:
                camera.draw_rect(x - half, y - half, x + half, y + half, *color, filled=True)
                x += dots['step']
            y += dots['step']
            row += 1

    def draw_floor(self):
        # 깨지는 바닥: 윗면을 따라 지그재그로 갈라진 금
        step = config.FRAGILE_CRACK_STEP
        x = self.x + step / 2
        i = 0
        while x < self.right:
            dy = self.h / 3 if i % 2 else self.h * 2 / 3
            camera.draw_rect(x - 2, self.y + dy - step / 4, x + 2, self.top, *config.COLOR_FRAGILE_LINE, filled=True)
            x += step
            i += 1

    def draw_ore(self):
        # 남은 횟수만큼 광석 점을 대각선으로 늘어놓는다
        left = self.max_hits - self.hits
        dots = max(1, round(config.ORE_CHUNK_DOTS * left / self.max_hits))
        size = min(self.w, self.h) / 6
        for i in range(dots):
            k = (i + 1) / (config.ORE_CHUNK_DOTS + 1)
            x, y = self.x + self.w * k, self.y + self.h * (1 - k)
            camera.draw_rect(x - size / 2, y - size / 2, x + size / 2, y + size / 2, *config.COLOR_ORE, filled=True)

    def get_bb(self):
        return self.left, self.bottom, self.right, self.top

    def handle_collision(self, group, other):
        pass
