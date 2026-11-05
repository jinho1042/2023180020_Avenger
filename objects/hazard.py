import config
import game_world
from systems import camera


class Hazard:
    # 가시·산성·구덩이 (6.8, 12.6). 몸 hitbox가 닿으면 play_mode가 player.hazard_hit()을 부른다
    # 가시는 아래 공격이 닿으면 포고. 쇠뇌 함정·낙석은 해당 작업에서
    # kind = 'hazard'는 패링 숨 판정용 (8.4, 함정이 쏜 투사체를 패링하면 숨 0). 가시·산성 등 종류는 hazard_type
    KINDS = ('spike', 'acid', 'pit')
    kind = 'hazard'

    def __init__(self, x, y, w, h, hazard_type):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.hazard_type = hazard_type

    def update(self):
        pass

    def on_pickaxe_hit(self, player):
        # 반환: 이번 휘두름이 이 대상에 '맞았는가' (combat이 반동·포고·스파크를 처리)
        return self.hazard_type == 'spike' and player.attack_dir == 'down'

    def draw(self):
        l, b, r, t = self.get_bb()
        if self.hazard_type == 'spike':
            # 밑변 SPIKE_W짜리 삼각형을 가로로 늘어놓는다. 삼각형은 SPIKE_STEP 두께의 가로줄을 쌓아 그린다
            count = max(1, int(self.w // config.SPIKE_W))
            spike_w = self.w / count
            step = config.SPIKE_STEP
            for i in range(count):
                sl = l + i * spike_w
                for row in range(0, int(self.h), step):
                    inset = spike_w / 2 * row / self.h
                    camera.draw_rect(sl + inset, b + row, sl + spike_w - inset, min(t, b + row + step),
                                     *config.COLOR_SPIKE, filled=True)
        elif self.hazard_type == 'acid':
            camera.draw_rect(l, b, r, t, *config.COLOR_ACID, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def handle_collision(self, group, other):
        pass
