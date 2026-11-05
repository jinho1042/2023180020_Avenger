import math

import config
from objects import spore_cloud
from objects.enemy_base import ACTIVE, CHASE, IDLE, TELEGRAPH, WINDUP, Attack, EnemyBase
from systems import camera

STATS = config.SPORE_SHROOM


class SporeShroom(EnemyBase):
    # 포자 버섯 (10.2, 10.3): 제자리에 고정. 플레이어가 trigger_dist 안에 오면 부풀어(빨간 예고, 패링 불가)
    # 자기 자리에 포자 구름(objects/spore_cloud.py)을 남긴다. 죽을 때도 구름. 원거리·포고로 처리하도록 유도
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.puff = Attack('puff', False, STATS['telegraph'], STATS['windup'], 0,
                           STATS['recover'], STATS['damage'], None)

    def choose_attacks(self):
        return [self.puff]

    def player_near(self):
        # 몸 중심끼리의 거리
        dx = self.player.x - self.x
        dy = (self.player.y + config.PLAYER_H / 2) - (self.y + self.h / 2)
        return math.hypot(dx, dy) <= STATS['trigger_dist']

    def update_ai(self):
        self.vx = 0
        if self.state in (IDLE, CHASE):
            if self.state == IDLE:
                self.set_state(CHASE)
            if not self.player.dead and self.player_near() and self.attack_cooldown <= 0:
                self.attack_queue = self.choose_attacks()
                self.start_next_attack()
        elif self.state_timer <= 0:
            self.next_phase()

    def next_phase(self):
        super().next_phase()
        if self.state == ACTIVE:
            self.release_cloud()

    def release_cloud(self):
        spore_cloud.spawn(self.x, self.y, STATS['cloud_radius'], STATS['cloud_time'], STATS['damage'], self.player)

    def die(self):
        self.release_cloud()   # 죽을 때도 구름 (10.2)
        super().die()

    def draw_body(self):
        # 자루 + 갓. 예고 중에는 갓이 부풀고(swell) 빨갛게 깜빡인다
        l, b, r, t = self.get_bb()
        stem = self.w / 4
        camera.draw_rect(self.x - stem, b, self.x + stem, b + self.h / 2, *self.color, filled=True)
        k = 0.0
        if self.state == TELEGRAPH:
            k = 1 - self.state_timer / self.puff.telegraph
        elif self.state == WINDUP:
            k = 1.0
        half = self.w / 2 * (1 + STATS['swell'] * k)
        cap_b = b + self.h / 2
        cap_t = t + self.h / 2 * STATS['swell'] * k
        cap_color = self.body_color() if self.state in (TELEGRAPH, WINDUP) else config.COLOR_SHROOM_CAP
        if cap_color == self.color:
            cap_color = config.COLOR_SHROOM_CAP
        camera.draw_rect(self.x - half, cap_b, self.x + half, cap_t, *cap_color, filled=True)
        if self.state == TELEGRAPH:
            # 패링 불가 공격은 머리 위 '!' (enemy_base와 같은 모양)
            eye = self.w / 8
            camera.draw_rect(self.x - eye / 2, cap_t + eye * 2, self.x + eye / 2, cap_t + eye * 5,
                             *config.COLOR_UNPARRYABLE, filled=True)
            camera.draw_rect(self.x - eye / 2, cap_t + eye / 2, self.x + eye / 2, cap_t + eye * 1.5,
                             *config.COLOR_UNPARRYABLE, filled=True)
