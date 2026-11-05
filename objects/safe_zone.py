import config
import game_world
from objects import effect
from systems import camera


class SafeZone:
    # 안전지대 (13.1): 공기가 있는 영역 + 그 안의 앉는 자리(objects의 seat, 같은 id). 앉는 자리는 없을 수 있다
    # 들어오기·앉기 처리는 play_mode.check_safe_zones. 숨·광석 보관은 T37·T38
    def __init__(self, room_id, x, y, w, h, zone_id, seat, state):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.gid = f'{room_id}:{zone_id}'
        self.seat = seat      # 앉는 자리 (x, y) = 아래쪽 중심, 없으면 None
        self.state = state
        self.prompt = False   # 앉을 수 있는 자리에 서 있으면 머리 위에 ↑ 표시 (play_mode가 매 프레임 정함)

    def update(self):
        pass

    def can_sit(self, player):
        if self.seat is None or not player.on_ground or player.is_locked() or player.sitting:
            return False
        l, b, r, t = self.seat_bb()
        return l <= player.x <= r and abs(player.y - b) <= config.SAFE_POINT_RADIUS

    def seat_bb(self):
        sx, sy = self.seat
        return sx - config.SEAT_W / 2, sy, sx + config.SEAT_W / 2, sy + config.SEAT_H

    def draw(self):
        l, b, r, t = self.get_bb()
        effect.draw_alpha_rect(l, b, r, t, config.COLOR_SAFE_ZONE, config.SAFE_ZONE_ALPHA)
        camera.draw_rect(l, b, r, b + config.SAFE_ZONE_MOSS_H, *config.COLOR_SAFE_ZONE, filled=True)
        if self.seat:
            self.draw_seat()
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_SAFE_ZONE)

    def draw_seat(self):
        # 돌 의자 + 등받이. 마지막으로 앉은 자리면 룬 문양이 밝다
        l, b, r, t = self.seat_bb()
        back_l = l + config.SEAT_W / 4
        camera.draw_rect(back_l, t, r - config.SEAT_W / 4, t + config.SEAT_BACK_H, *config.COLOR_SEAT, filled=True)
        camera.draw_rect(l, b, r, t, *config.COLOR_SEAT, filled=True)
        rune = config.COLOR_SEAT_RUNE if self.state.rest_seat == self.gid else config.COLOR_SEAT_RUNE_OFF
        cx, cy = self.seat[0], t + config.SEAT_BACK_H / 2
        mark = config.SEAT_BACK_H / 6
        camera.draw_rect(cx - mark, cy - mark * 2, cx + mark, cy + mark * 2, *rune, filled=True)
        camera.draw_rect(cx - mark * 2, cy - mark / 2, cx + mark * 2, cy + mark / 2, *rune, filled=True)
        if self.prompt:
            self.draw_prompt(cx, t + config.SEAT_BACK_H + config.SIT_PROMPT_GAP)

    def draw_prompt(self, cx, y):
        # ↑ 화살표 (가로줄 쌓기 삼각형 + 막대)
        size = config.SEAT_H / 2
        camera.draw_rect(cx - size / 6, y, cx + size / 6, y + size, *config.COLOR_SEAT_RUNE, filled=True)
        for i in range(0, int(size), 3):
            half = size / 2 * (1 - i / size)
            camera.draw_rect(cx - half, y + size + i, cx + half, y + size + i + 3, *config.COLOR_SEAT_RUNE, filled=True)

    def get_bb(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def handle_collision(self, group, other):
        pass
