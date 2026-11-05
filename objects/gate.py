import config
import game_world
from objects import effect
from systems import camera


class Gate:
    # 닫혀 있는 동안 지형으로 길을 막는 문 (12.6). 열리면 world_state.opened에 남고 다시 만들지 않는다 (5.6)
    # lever_gate: 연결된 레버(objects/switch.py)가 연다. one_way: open_from 쪽에서 곡괭이로 치면 열린다 (숏컷)
    # kind = 'solid'는 systems/terrain.py가 보는 값이고 문 종류는 type. 그림자 장막·봉인문·아레나 문은 해당 작업에서
    KINDS = ('lever_gate', 'one_way')

    def __init__(self, room_id, x, y, w, h, type, obj_id, props, state):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.type = type
        self.kind = 'solid'
        self.gid = f'{room_id}:{obj_id}'
        self.open_from = props.get('open_from')
        self.state = state

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

    def open(self):
        if self.kind is None:
            return
        self.kind = None
        self.state.opened.add(self.gid)
        game_world.remove_object(self)
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
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *config.COLOR_GATE, filled=True)
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
