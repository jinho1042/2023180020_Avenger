import config
import game_world
from objects import effect
from systems import camera


class Breakable:
    # 곡괭이로 부수는 벽·덩어리 (12.6). 부서지기 전에는 지형으로 플레이어·적·투사체를 막는다
    # kind = 'solid'는 systems/terrain.py가 보는 값이고 기믹 종류는 type. 부서지면 kind = None (지형에서 빠짐)
    # 흙벽(soil·hard_soil)·광맥벽·깨지는 바닥·결정 숨주머니는 해당 룬·곡괭이 작업에서
    KINDS = ('crack', 'ore_chunk')

    def __init__(self, room_id, x, y, w, h, type, obj_id, state):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.type = type
        self.kind = 'solid'
        self.gid = f'{room_id}:{obj_id}'
        self.state = state
        self.max_hits = config.CRACK_WALL_HITS if type == 'crack' else config.ORE_CHUNK_HITS
        # 친 횟수는 방을 나갔다 와도 유지한다 (광석 덩어리를 나갔다 오며 반복해서 캐지 못하게)
        self.hits = state.mined.get(self.gid, 0)

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
        pass

    def on_pickaxe_hit(self, player):
        # 반환: 이번 휘두름이 이 대상에 '맞았는가' (combat이 반동·포고·스파크를 처리)
        if self.kind is None:
            return False
        self.hits += 1
        self.state.mined[self.gid] = self.hits
        cx, cy = self.x + self.w / 2, self.y + self.h / 2
        if self.type == 'ore_chunk':
            # 칠 때마다 광석. 튀어나와 흡수되는 광석은 T38
            player.ore += config.ORE_PER_CHUNK_HIT
            effect.ore_mined(cx, cy)
        if self.hits >= self.max_hits:
            self.kind = None
            self.state.broken.add(self.gid)
            self.state.mined.pop(self.gid, None)
            game_world.remove_object(self)
            effect.wall_broken(cx, cy, self.color())
        return True

    def color(self):
        return config.COLOR_CRACK_WALL if self.type == 'crack' else config.COLOR_ORE_CHUNK

    def draw(self):
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *self.color(), filled=True)
        if self.type == 'crack':
            self.draw_crack()
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
