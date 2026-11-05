import math

from pico2d import clamp

import config
from objects.enemy_base import ACTIVE, TELEGRAPH, WINDUP, Attack, EnemyBase
from systems import camera, terrain

STATS = config.VINE_LURKER
HIDDEN = 'Hidden'
FAR = -1e6   # 숨어 있는 동안 몸 판정을 방 밖 멀리 둔다 (곡괭이·접촉·반사탄 모두 닿지 않음)


class VineLurker(EnemyBase):
    # 덩굴 매복충 (10.2, 10.3): 땅속 또는 천장에 숨어 있다 (hitbox 없음, 흙 무더기·늘어진 덩굴로 위치 힌트)
    # 가로 ambush_dist 안에 오면 빨간 예고 → 튀어나와 물기(패링 불가) → 이후 접근해 할퀴기 (흰 예고)
    # 천장 매복: spawn 자리 바로 아래에 바닥이 없으면. 몸 윗면이 천장에 붙어 있다가 떨어지며 문다
    def __init__(self, x, y, player, platforms):
        super().__init__(x, y, STATS, player, platforms)
        self.bite = Attack('bite', False, STATS['telegraph'], STATS['bite_windup'], STATS['bite_active'],
                           STATS['bite_recover'], STATS['damage'], STATS['bite_hitbox'])
        self.claw = Attack('claw', True, STATS['claw_telegraph'], STATS['claw_windup'], STATS['claw_active'],
                           STATS['claw_recover'], STATS['damage'], STATS['claw_hitbox'])
        probe = STATS['ceiling_probe']
        self.ceiling = not terrain.resolve_y(x, y, y - probe, -1, self.w, self.h, platforms)[2]
        self.hanging = self.ceiling   # 천장에 매달려 중력을 받지 않는 동안
        self.drop_vx = 0.0
        self.state = HIDDEN

    def choose_attacks(self):
        return [self.claw]

    def player_in_ambush(self):
        if self.player.dead or abs(self.player.x - self.x) > STATS['ambush_dist']:
            return False
        if self.ceiling:
            return self.player.y < self.y   # 천장 아래를 지나갈 때
        return abs(self.player.y - self.y) < self.h * 2

    def update_ai(self):
        if self.state != HIDDEN:
            super().update_ai()
            return
        self.vx = 0
        if self.player_in_ambush():
            self.attack_queue = [self.bite]
            self.start_next_attack()

    def next_phase(self):
        if self.dropping() and not self.on_ground:
            return   # 천장에서 떨어지는 물기는 착지할 때까지 판정이 남는다
        super().next_phase()
        if self.state == ACTIVE and self.attack is self.bite:
            if self.ceiling:
                self.hanging = False      # 떨어지며 문다. 떨어지는 동안 플레이어 x에 닿도록 가로 속도를 정한다
                fall = max(self.y - self.player.y, 1)
                fall_time = math.sqrt(2 * fall / -config.GRAVITY)
                lunge = STATS['bite_lunge']
                self.drop_vx = clamp(-lunge, (self.player.x - self.x) / fall_time, lunge)
            else:
                self.vy = STATS['bite_rise']   # 땅에서 솟구치며 문다
                self.on_ground = False

    def dropping(self):
        return self.ceiling and self.state == ACTIVE and self.attack is self.bite

    def move(self, dt):
        if self.state == HIDDEN or self.hanging:
            self.vx = self.vy = 0
            return
        if self.dropping():
            self.vx = self.drop_vx
        elif self.state == ACTIVE and self.attack is self.bite:
            self.vx = self.face_dir * STATS['bite_lunge']   # 플레이어 쪽으로 튀어나간다
        super().move(dt)

    def deals_contact(self):
        return self.state != HIDDEN and super().deals_contact()

    def get_bb(self):
        if self.state == HIDDEN:
            return FAR, FAR, FAR, FAR
        return super().get_bb()

    def get_attack_bb(self):
        # 물기는 몸 중심에 붙은 판정, 할퀴기는 기본(몸 앞쪽)
        if self.state == ACTIVE and self.attack is self.bite:
            w, h = self.bite.hitbox
            cy = self.y + self.h / 2
            return self.x - w / 2, cy - h / 2, self.x + w / 2, cy + h / 2
        return super().get_attack_bb()

    def draw_body(self):
        if self.state == HIDDEN:
            self.draw_hint()
            return
        super().draw_body()
        if self.state in (TELEGRAPH, WINDUP) and self.attack is self.bite:
            # 튀어나오기 직전: 흙 무더기·덩굴이 남아 있다
            self.draw_hint()

    def draw_hint(self):
        # 위치 힌트 (10.3): 땅속이면 흙 무더기, 천장이면 늘어진 덩굴 세 가닥
        if self.ceiling:
            top = self.y + self.h
            for i, k in enumerate((0.25, 0.5, 0.75)):
                x = self.x - self.w / 2 + self.w * k
                length = self.h * (0.6 + 0.3 * (i % 2))
                camera.draw_rect(x - 2, top - length, x + 2, top, *config.COLOR_LURKER_VINE, filled=True)
        else:
            half = self.w / 2
            camera.draw_rect(self.x - half, self.y, self.x + half, self.y + self.h / 5,
                             *config.COLOR_LURKER_MOUND, filled=True)
            camera.draw_rect(self.x - half / 2, self.y + self.h / 5, self.x + half / 2, self.y + self.h / 3,
                             *config.COLOR_LURKER_MOUND, filled=True)

    def draw_weapon(self, l, b, r, t):
        if self.attack is self.claw:
            super().draw_weapon(l, b, r, t)
        # 이빨: 몸 앞쪽 아래 두 개
        tooth = self.w / 8
        fx = self.x + self.face_dir * self.w / 2
        for k in (0.2, 0.45):
            y = b + self.h * k
            camera.draw_rect(fx - tooth / 2, y, fx + tooth / 2, y + tooth, *config.COLOR_TEXT, filled=True)
