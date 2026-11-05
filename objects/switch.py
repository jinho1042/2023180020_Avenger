import config
import game_world
from objects import effect
from systems import camera


class Switch:
    # 레버·수정 스위치 (12.6). 켜지면 같은 방의 연결된 문(gate id)을 연다. 켠 상태는 world_state.switches
    # (x, y)는 아래쪽 중심
    # lever: 곡괭이로 치면 당겨진다
    # crystal: 투사체는 통과시키는 단단한 수정 기둥 (지형이라 몸은 막는다). 반사탄(결정 화살 포함)이 맞으면 켜지고
    #   그 반사탄은 기둥에서 부서진다. 켜진 뒤에는 반사탄도 통과한다. 곡괭이는 반동·스파크만
    KINDS = ('lever', 'crystal')
    passes_projectiles = True   # projectile.py: 투사체가 지형으로 부딪히지 않는다 (레버는 지형이 아니라 상관없음)

    def __init__(self, room_id, x, y, type, obj_id, target, gate, state):
        self.x, self.y = x, y
        self.type = type
        self.kind = 'solid' if type == 'crystal' else None   # systems/terrain.py가 보는 값
        self.gid = f'{room_id}:{obj_id}'
        self.target = target
        self.gate = gate      # 연결된 Gate 객체. 이미 열렸으면 None
        self.state = state

    @property
    def pulled(self):
        return self.gid in self.state.switches

    @property
    def left(self):
        return self.get_bb()[0]

    @property
    def right(self):
        return self.get_bb()[2]

    @property
    def bottom(self):
        return self.y

    @property
    def top(self):
        return self.get_bb()[3]

    def update(self):
        pass

    def turn_on(self):
        # 처음 켤 때만 문을 연다
        if self.pulled:
            return
        self.state.switches.add(self.gid)
        if self.gate:
            self.gate.open()

    def on_pickaxe_hit(self, player):
        # 당긴 뒤에도 맞기는 한다 (반동·스파크). 수정 스위치는 곡괭이로 켜지지 않는다
        if self.type == 'lever':
            self.turn_on()
        return True

    def on_reflected_hit(self, projectile):
        # 반사탄이 닿음 (projectile.py). 꺼진 수정 스위치만 받는다. 반환: 투사체가 여기서 부서지는가
        if self.type != 'crystal' or self.pulled:
            return False
        self.turn_on()
        effect.wall_broken(self.x, self.y + config.CRYSTAL_SWITCH['h'] / 2, config.COLOR_CRYSTAL_SWITCH_ON)
        return True

    def draw(self):
        if self.type == 'crystal':
            self.draw_crystal()
        else:
            self.draw_lever()
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *config.COLOR_DEBUG_BODY)

    def draw_lever(self):
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

    def draw_crystal(self):
        # 수정 기둥: 켜지면 밝게. 비스듬한 결(facets)로 다른 벽과 구별한다
        l, b, r, t = self.get_bb()
        color = config.COLOR_CRYSTAL_SWITCH_ON if self.pulled else config.COLOR_CRYSTAL_SWITCH
        camera.draw_rect(l, b, r, t, *color, filled=True)
        edge = config.COLOR_CRYSTAL_SWITCH_EDGE
        camera.draw_rect(l, b, r, t, *edge)
        facets = config.CRYSTAL_SWITCH['facets']
        seg = (t - b) / facets
        for i in range(facets):
            y = b + seg * (i + 0.5)
            x = l + (r - l) * (0.3 if i % 2 else 0.7)
            camera.draw_rect(x - 2, y - seg / 3, x + 2, y + seg / 3, *edge, filled=True)

    def get_bb(self):
        if self.type == 'crystal':
            spec = config.CRYSTAL_SWITCH
            return self.x - spec['w'] / 2, self.y, self.x + spec['w'] / 2, self.y + spec['h']
        half_w = config.LEVER_W / 2
        return self.x - half_w, self.y, self.x + half_w, self.y + config.LEVER_H

    def handle_collision(self, group, other):
        pass
