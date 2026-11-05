import config
import game_framework
import game_world
from objects import effect
from systems import camera


class AirVent:
    # 숨구멍 (7.2): 벽 틈에서 바람이 새는 곳. 몸이 닿으면 AIR_VENT_REFILL, AIR_VENT_COOLDOWN 뒤 재사용
    # 방 JSON air_vents [x, y, id], (x, y)는 중심. 닿기 처리는 play_mode.check_air_vents
    # 쿨다운은 저장하지 않는다 (방에 다시 들어오면 새로 생긴다)
    def __init__(self, room_id, x, y, vent_id):
        self.x, self.y = x, y
        self.gid = f'{room_id}:{vent_id}'
        self.cooldown = 0.0
        self.time = 0.0       # 공기 점 애니메이션

    def ready(self):
        return self.cooldown <= 0

    def use(self):
        self.cooldown = config.AIR_VENT_COOLDOWN

    def update(self):
        dt = game_framework.frame_time
        self.cooldown = max(0, self.cooldown - dt)
        self.time += dt

    def draw(self):
        if not camera.visible(self.get_bb()):
            return
        color = config.COLOR_AIR_VENT if self.ready() else config.COLOR_AIR_VENT_USED
        effect.draw_disc(self.x, self.y, config.AIR_VENT_RADIUS, color)
        if self.ready():
            # 위로 오르는 작은 공기 점 (14.5)
            wind = config.AIR_VENT_WIND
            half = wind['size'] / 2
            for i in range(wind['count']):
                phase = (self.time / wind['period'] + i / wind['count']) % 1
                y = self.y + config.AIR_VENT_RADIUS + phase * wind['rise']
                camera.draw_rect(self.x - half, y - half, self.x + half, y + half, *color, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *color)

    def get_bb(self):
        r = config.AIR_VENT_RADIUS
        return self.x - r, self.y - r, self.x + r, self.y + r

    def handle_collision(self, group, other):
        pass
