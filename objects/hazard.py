import config
import game_framework
import game_world
from objects import effect
from systems import camera, sound


class Hazard:
    # 가시·산성·구덩이 (6.8, 12.6). 몸 hitbox가 닿으면 play_mode가 player.hazard_hit()을 부른다
    # 가시는 아래 공격이 닿으면 포고. 낙석은 아래 Rockfall, 쇠뇌 함정은 해당 작업에서
    # kind = 'hazard'는 패링 숨 판정용 (8.4, 함정이 쏜 투사체를 패링하면 숨 0). 가시·산성 등 종류는 hazard_type
    KINDS = ('spike', 'acid', 'pit')
    kind = 'hazard'

    def __init__(self, x, y, w, h, hazard_type):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.hazard_type = hazard_type

    def update(self):
        pass

    def notice(self, player):
        # 플레이어 위치를 보고 움직이는 함정만 쓴다 (낙석)
        pass

    def is_harmful(self):
        # 지금 몸에 닿으면 피해를 주는가 (낙석은 떨어지는 동안만)
        return True

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


class Rockfall(Hazard):
    # 낙석 함정 (12.6): 가로 x~x+w 위 y+h에서 돌이 떨어져 바닥 y에 닿는다
    # 대기 → 몸이 가까이 오면 바닥에 빨간 그림자 예고(warn) → 낙석 → 부서짐 → cooldown 뒤 다시 대기
    # 떨어지는 돌에 몸이 닿을 때만 환경 피해. 곡괭이에는 맞지 않는다
    KINDS = ('rockfall',)

    def __init__(self, x, y, w, h, hazard_type):
        super().__init__(x, y, w, h, hazard_type)
        self.phase = 'idle'     # 'idle' | 'warn' | 'fall' | 'cooldown'
        self.timer = 0.0
        self.rock_y = y + h     # 돌 아래쪽

    def notice(self, player):
        # play_mode가 매 프레임 부른다. 대기 중이면 몸 가운데가 가까운지만 본다
        if self.phase == 'idle' and abs(player.x - (self.x + self.w / 2)) <= config.ROCKFALL_TRAP['range']:
            self.phase, self.timer = 'warn', config.ROCKFALL_TRAP['warn']
            effect.telegraph(False)

    def is_harmful(self):
        return self.phase == 'fall'

    def update(self):
        spec = config.ROCKFALL_TRAP
        dt = game_framework.frame_time
        if self.phase == 'fall':
            self.rock_y -= spec['fall_speed'] * dt
            if self.rock_y <= self.y:
                self.land()
            return
        if self.phase in ('warn', 'cooldown'):
            self.timer -= dt
            if self.timer <= 0:
                if self.phase == 'warn':
                    self.phase, self.rock_y = 'fall', self.y + self.h
                else:
                    self.phase = 'idle'

    def land(self):
        spec = config.ROCKFALL_TRAP
        self.phase, self.timer = 'cooldown', spec['cooldown']
        effect.burst(self.x + self.w / 2, self.y, spec['debris'], config.COLOR_ROCK)
        camera.shake(*spec['shake'])
        sound.play('door')

    def on_pickaxe_hit(self, player):
        return False

    def draw(self):
        spec = config.ROCKFALL_TRAP
        l, r = self.x, self.x + self.w
        if self.phase in ('warn', 'fall'):
            # 바닥 그림자는 돌이 다가올수록 진해진다
            k = 1 - self.timer / spec['warn'] if self.phase == 'warn' else 1
            effect.draw_alpha_rect(l, self.y, r, self.y + spec['shadow_h'], config.COLOR_ROCK_SHADOW,
                                   spec['shadow_alpha'] * k)
        if self.phase == 'fall':
            camera.draw_rect(*self.get_bb(), *config.COLOR_ROCK, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, self.y, r, self.y + self.h, *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        # 떨어지는 돌 (떨어지는 중이 아니면 is_harmful()이 False라 판정하지 않는다)
        return self.x, self.rock_y, self.x + self.w, self.rock_y + config.ROCKFALL_TRAP['rock_h']
