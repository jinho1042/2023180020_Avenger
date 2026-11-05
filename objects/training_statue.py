import config
import game_world
from objects import effect, pickup
from objects.enemy_base import ACTIVE, CHASE, DEAD, IDLE, RECOVER, STAGGER, TELEGRAPH, WINDUP, Attack, EnemyBase
from systems import camera

STATS = config.TRAINING_STATUE


class TrainingStatue(EnemyBase):
    # R1 패링 연습 석상 (9.5): 진행을 막지 않는 선택 요소. objects의 ["statue", x, y, id], (x, y) = 아래쪽 중심
    # 플레이어가 near_range 안에 있으면 interval마다 흰 내려치기 (피해 0). hits_to_break번 패링하면 부서지며 광석 (영구)
    # 적 목록에 넣어 combat의 패링 판정을 그대로 쓴다. 움직이지 않고, 몸 접촉 피해·곡괭이 피해가 없다
    kind = 'statue'   # 패링 숨 0 (8.4)

    def __init__(self, room_id, x, y, statue_id, player, platforms, state):
        super().__init__(x, y, dict(STATS, hp=1, speed=0, detect_range=STATS['near_range'],
                                    attack_range=STATS['near_range'], attack_cooldown=STATS['interval']),
                         player, platforms)
        self.gid = f'{room_id}:{statue_id}'
        self.state_ref = state
        self.parries = 0
        self.strike = Attack('strike', True, STATS['telegraph'], STATS['windup'], STATS['active'],
                             STATS['recover'], 0, STATS['hitbox'])
        self.attack_cooldown = STATS['interval']

    def choose_attacks(self):
        return [self.strike]

    def update_ai(self):
        if self.state in (IDLE, CHASE):
            self.vx = 0
            near = abs(self.player.x - self.x) <= STATS['near_range'] and not self.player.dead
            if near and self.attack_cooldown <= 0:
                self.attack_queue = self.choose_attacks()
                self.start_next_attack()
            return
        if self.state_timer <= 0:
            self.next_phase()

    def move(self, dt):
        pass   # 제자리에 서 있다

    def deals_contact(self):
        return False

    def take_damage(self, damage, knockback=0):
        pass   # 곡괭이에는 회색 스파크만 (combat.resolve)

    def on_parried(self):
        self.parries += 1
        if self.parries >= STATS['hits_to_break']:
            self.shatter()
            return
        # 짧게 멈칫한 뒤 다음 내려치기를 기다린다
        self.attack_queue = []
        self.attack = None
        self.attack_cooldown = STATS['interval']
        self.set_state(STAGGER, STATS['recoil'])

    def shatter(self):
        # 부서짐: 광석 + 영구 기록 (12.6). 적처럼 죽지만 처치 연출 대신 벽 부서짐 파편
        self.state_ref.broken.add(self.gid)
        self.hp = 0
        self.set_state(DEAD)
        game_world.remove_object(self)
        effect.wall_broken(self.x, self.y + self.h / 2, self.color)
        pickup.spill(self.x, self.y + self.h / 2, STATS['ore'], self.player)

    def body_color(self):
        # 회색 사각형, 예고 때만 흰 번쩍임 (14.5)
        if self.state == TELEGRAPH and int(self.state_timer / config.TELEGRAPH_BLINK) % 2 == 0:
            return config.COLOR_PARRYABLE
        return self.color

    def draw_weapon(self, l, b, r, t):
        # 들어 올린 팔 (예고 중 위로, 내려치는 중 앞으로). 패링당한 횟수만큼 금이 간다
        arm = self.w / 4
        front = self.x + self.face_dir * self.w / 2
        if self.state in (TELEGRAPH, WINDUP):
            camera.draw_rect(front - arm / 2, t, front + arm / 2, t + self.h / 3, *self.color, filled=True)
        elif self.state not in (ACTIVE, RECOVER):
            camera.draw_rect(front - arm / 2, b + self.h / 3, front + arm / 2, t - arm, *self.color, filled=True)
        for i in range(self.parries):
            y = t - (i + 1) * self.h / (STATS['hits_to_break'] + 1)
            camera.draw_rect(l + arm / 2, y - 1, r - arm / 2, y + 1, *config.COLOR_STATUE_CRACK, filled=True)
