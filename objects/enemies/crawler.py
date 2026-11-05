import config
import game_world
from objects.enemy_base import CHASE, EnemyBase
from systems import camera, terrain

STATS = config.CRAWLER


class Crawler(EnemyBase):
    # 갱도 벌레 (10.2, 10.3): 바닥을 일정 속도로 기어 다니고 앞이 벽·발판 끝·안전지대 경계면 돌아선다
    # 공격 상태 없음 (몸 접촉 피해만). 플레이어를 쫓지 않는다
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.state = CHASE

    def update_ai(self):
        if self.state != CHASE:
            # 맞아서 움찔하는 동안만 멈춘다
            self.vx = 0
            if self.state_timer <= 0:
                self.next_phase()
            return
        if self.on_ground and (self.wall_ahead() or not self.floor_ahead() or self.zone_blocked):
            self.face_dir = -self.face_dir
        self.vx = self.face_dir * self.speed

    def wall_ahead(self):
        # 몸 앞 1px에 지형이 있는가 (방 가장자리 포함)
        front = self.x + self.face_dir * (self.w / 2 + 1)
        if not (0 < front < game_world.room_w):
            return True
        return terrain.body_blocked(front, self.y, 2, self.h, self.platforms)

    def floor_ahead(self):
        # 앞발 바로 아래에 바닥이 있는가
        front = self.x + self.face_dir * (self.w / 2 + 1)
        probe = STATS['edge_probe']
        return terrain.resolve_y(front, self.y, self.y - probe, -1, 2, self.h, self.platforms)[2]

    def draw_weapon(self, l, b, r, t):
        # 마디 무늬 (몸 위 세로 줄 3개)
        for i in range(1, 4):
            x = l + (r - l) * i / 4
            camera.draw_rect(x - 1, b + 2, x + 1, t - 2, *config.COLOR_STATUE_CRACK, filled=True)
