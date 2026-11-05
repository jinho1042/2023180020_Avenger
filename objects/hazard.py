import config
import game_world
from systems import camera


class Hazard:
    # 가시·산성·구덩이 (6.8, 12.6). 몸 hitbox가 닿으면 play_mode가 player.hazard_hit()을 부른다
    # 가시는 아래 공격이 닿으면 포고. 쇠뇌 함정·낙석은 해당 작업에서
    KINDS = ('spike', 'acid', 'pit')

    def __init__(self, x, y, w, h, kind):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.kind = kind

    def update(self):
        pass

    def on_pickaxe_hit(self, player):
        # 반환: 이번 휘두름이 이 대상에 '맞았는가' (combat이 반동·포고·스파크를 처리)
        return self.kind == 'spike' and player.attack_dir == 'down'

    def draw(self):
        l, b, r, t = self.get_bb()
        if self.kind == 'spike':
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
        elif self.kind == 'acid':
            camera.draw_rect(l, b, r, t, *config.COLOR_ACID, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def handle_collision(self, group, other):
        pass
