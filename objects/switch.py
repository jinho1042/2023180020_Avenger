import config
import game_world
from systems import camera


class Switch:
    # 레버 (12.6). 곡괭이로 치면 당겨지고 같은 방의 연결된 문(gate id)을 연다. 당긴 상태는 world_state.switches
    # (x, y)는 레버 아래쪽 중심. 수정 스위치(반사 투사체·결정 화살)는 해당 작업에서
    KINDS = ('lever',)

    def __init__(self, room_id, x, y, type, obj_id, target, gate, state):
        self.x, self.y = x, y
        self.type = type
        self.gid = f'{room_id}:{obj_id}'
        self.target = target
        self.gate = gate      # 연결된 Gate 객체. 이미 열렸으면 None
        self.state = state

    @property
    def pulled(self):
        return self.gid in self.state.switches

    def update(self):
        pass

    def on_pickaxe_hit(self, player):
        # 당긴 뒤에도 맞기는 한다 (반동·스파크). 문은 처음 당길 때만 연다
        if not self.pulled:
            self.state.switches.add(self.gid)
            if self.gate:
                self.gate.open()
        return True

    def draw(self):
        l, b, r, t = self.get_bb()
        base_h = config.LEVER_H / 4
        camera.draw_rect(l, b, r, b + base_h, *config.COLOR_LEVER_BASE, filled=True)
        # 손잡이: 당기기 전에는 왼쪽, 당긴 뒤에는 오른쪽으로 기울어진 막대 (가로줄 쌓기)
        color = config.COLOR_LEVER_ON if self.pulled else config.COLOR_LEVER
        lean = 1 if self.pulled else -1
        stick = config.LEVER_STICK
        for i in range(0, stick, 4):
            x = self.x + lean * i / 2
            y = b + base_h + i
            camera.draw_rect(x - 3, y, x + 3, y + 4, *color, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)

    def get_bb(self):
        half_w = config.LEVER_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.LEVER_H

    def handle_collision(self, group, other):
        pass
