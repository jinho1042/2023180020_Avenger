import config
import game_world
from systems import camera


class ExitZone:
    # 방 출구 (12.5 exits). 몸 hitbox가 닿으면 play_mode가 world.go_through로 넘긴다
    # side: 출구가 붙은 방 가장자리 'left' | 'right' | 'down' | 'up'. 가는 출구가 'down'이면 도착 출구는 'up'
    def __init__(self, data, room_w, room_h):
        self.id = data['id']
        self.x, self.y, self.w, self.h = data['rect']
        self.to = data['to']
        self.to_exit = data['to_exit']
        cx, cy = self.x + self.w / 2, self.y + self.h / 2
        if self.w <= self.h:
            self.side = 'left' if cx < room_w / 2 else 'right'
        else:
            self.side = 'down' if cy < room_h / 2 else 'up'

    def update(self):
        pass

    def draw(self):
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *config.COLOR_DEBUG_EXIT)

    def get_bb(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def handle_collision(self, group, other):
        pass
