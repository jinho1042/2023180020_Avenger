import config
import game_world
from objects import effect
from systems import camera


class BreathZone:
    # 숨 소모 배율 영역 (7.2): 포자 지대·물·탁한 공기 등. 몸 중심이 들어 있으면 breath가 배율을 본다
    # 방 JSON breath_zones [x, y, w, h, 배율 이름]과 water [x, y, w, h] (자동으로 'water')
    def __init__(self, x, y, w, h, air):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.air = air

    def update(self):
        pass

    def draw(self):
        if not camera.visible(self.get_bb()):
            return
        l, b, r, t = self.get_bb()
        color = config.COLOR_BREATH_ZONE.get(self.air, config.COLOR_BREATH_ZONE['normal'])
        effect.draw_alpha_rect(l, b, r, t, color, config.BREATH_ZONE_ALPHA)
        if self.air == 'spore':
            # 포자 지대: 노란 점 무늬 (14.5)
            gap, dot = config.BREATH_ZONE_DOT_GAP, config.BREATH_ZONE_DOT
            for row, y in enumerate(range(int(b + gap / 2), int(t), gap)):
                offset = gap / 2 if row % 2 else 0
                for x in range(int(l + gap / 4 + offset), int(r), gap):
                    camera.draw_rect(x, y, x + dot, y + dot, *color, filled=True)
        elif self.air == 'water':
            # 물: 윗면에 수면 선 (14.5)
            camera.draw_rect(l, t - config.WATER_SURFACE_H, r, t, *config.COLOR_WATER_SURFACE, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *color)

    def get_bb(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def handle_collision(self, group, other):
        pass


class BreathGate:
    # 숨 게이트 (7.3): 방 전체를 덮는 영역 + 요구 숨의 룬 레벨. 레벨 확인·기절은 systems/breath.py
    # 방 JSON breath_gates [x, y, w, h, 게이트 id, 요구 Lv]. 숨막이 갱은 id 'choke'
    def __init__(self, x, y, w, h, gate_id, need_lv):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.gate_id = gate_id
        self.need_lv = need_lv

    def update(self):
        pass

    def draw(self):
        # 어두운 빗금 (14.5). 화면에 보이는 부분만 그린다. 경계선은 F1에서만
        l, b, r, t = self.get_bb()
        gap = config.BREATH_GATE_LINE_GAP
        view_l, view_b = camera.offset_x, camera.offset_y
        view_r, view_t = view_l + config.SCREEN_W, view_b + config.SCREEN_H
        cl, cb, cr, ct = max(l, view_l), max(b, view_b), min(r, view_r), min(t, view_t)
        if cl >= cr or cb >= ct:
            return
        # y = x - c 인 45도 선들. c를 gap 간격(월드에 고정)으로 잡고 보이는 사각형 안으로 자른다
        start = int((cl - ct) // gap) * gap
        for c in range(start, int(cr - cb) + gap, gap):
            x1, x2 = max(cl, c + cb), min(cr, c + ct)
            if x1 < x2:
                effect.draw_alpha_line(x1, x1 - c, x2, x2 - c, config.COLOR_BREATH_GATE_LINE,
                                       config.BREATH_GATE_ALPHA, config.BREATH_GATE_LINE_W)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_BREATH_GATE)

    def get_bb(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def handle_collision(self, group, other):
        pass
