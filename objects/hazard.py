import config
import game_framework
import game_world
from objects import effect, pickup, projectile
from objects.enemy_base import DEAD, IDLE, EnemyBase
from systems import camera, sound


class Hazard:
    # 가시·산성·구덩이 (6.8, 12.6). 몸 hitbox가 닿으면 play_mode가 player.hazard_hit()을 부른다
    # 가시는 아래 공격이 닿으면 포고. 낙석은 아래 Rockfall, 쇠뇌 함정은 BoltTrap
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


class ThornVine(Hazard):
    # 가시 덩굴벽 (12.6, 버팀의 룬 Lv2): 지형(solid)이면서 함정. hazards [x, y, w, h, "thorn_vine"]
    # 버팀 Lv2(thorn_cling) 전에는 닿으면 환경 피해 (play_mode.check_hazards) + 매달리지 못함 (player.update_wall)
    # Lv2부터는 피해 없이 보통 벽처럼 매달리고 벽점프한다. 지형 판정은 left·right·bottom·top (Room.terrain)
    # get_bb는 '닿음' 판정용으로 THORN_VINE touch만큼 넓힌 영역 (단단한 벽이라 몸이 겹칠 수 없으므로)
    KINDS = ('thorn_vine',)
    kind = 'solid'

    def __init__(self, x, y, w, h, hazard_type):
        super().__init__(x, y, w, h, hazard_type)
        self.harmful = True   # notice가 매 프레임 플레이어 버팀 레벨로 정한다

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y

    @property
    def top(self):
        return self.y + self.h

    def notice(self, player):
        self.harmful = not player.can('thorn_cling')

    def is_harmful(self):
        return self.harmful

    def on_pickaxe_hit(self, player):
        return False

    def draw(self):
        spec = config.THORN_VINE
        l, b, r, t = self.left, self.bottom, self.right, self.top
        camera.draw_rect(l, b, r, t, *config.COLOR_THORN_VINE, filled=True)
        # 양옆 면에 엇갈린 가시 (바깥으로 spike px)
        half = spec['spike'] / 2
        y, i = b + spec['step'] / 2, 0
        while y < t:
            x = l - spec['spike'] if i % 2 else r
            camera.draw_rect(x, y - half, x + spec['spike'], y + half, *config.COLOR_THORN_VINE_SPIKE, filled=True)
            y += spec['step'] / 2
            i += 1
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *config.COLOR_DEBUG_ATTACK)

    def get_bb(self):
        m = config.THORN_VINE['touch']
        return self.x - m, self.y - m, self.x + self.w + m, self.y + self.h + m


def fire_bolt(x, y, dir_x, platforms, owner):
    # 쇠뇌 화살 (흰, 패링 가능) 한 발. owner = 쏜 함정·과녁 → 패링 숨 0 (8.4)
    spec = config.TRAP_BOLT
    return projectile.fire(x, y, dir_x, 0, spec['speed'], spec['damage'], True, platforms, spec, owner)


class BoltTrap(Hazard):
    # 쇠뇌 함정 (12.6): 벽면에 박힌 쇠뇌. 붙어 있는 solid의 반대쪽으로 수평 발사
    #   (rect 오른쪽 면이 solid에 붙어 있으면 왼쪽으로, 왼쪽 면이 붙어 있으면 오른쪽으로, 둘 다 아니면 방 가운데 쪽으로)
    # 플레이어가 쏘는 쪽 앞 range 안·높이 band 안이면 interval마다 흰 예고 → 화살. 몸에 닿아도 피해 없음
    # 화살 패링: 반사 해금 전에는 막아 없애기, 해금 후에는 반사 (combat.projectile_hit). 패링 숨 0 (kind 'hazard')
    KINDS = ('bolt_trap',)

    def __init__(self, x, y, w, h, hazard_type, platforms, room_w):
        super().__init__(x, y, w, h, hazard_type)
        self.dir_x = self.facing(platforms, room_w)
        self.platforms = platforms   # 화살이 부딪히는 지형. Room.build가 terrain(닫힌 문·벽 포함)으로 바꾼다
        self.timer = config.TRAP_BOLT['interval']
        self.armed = False    # 플레이어가 사거리 안에 있음 (notice가 매 프레임 정한다)

    def facing(self, platforms, room_w):
        for p in platforms:
            if p.kind != 'solid' or p.bottom >= self.y + self.h or p.top <= self.y:
                continue
            if p.left == self.x + self.w:
                return -1
            if p.right == self.x:
                return 1
        return 1 if self.x + self.w / 2 < room_w / 2 else -1

    def muzzle(self):
        # 화살이 나가는 자리: 쏘는 쪽 면 바로 앞, 높이 가운데
        half = config.TRAP_BOLT['size'] / 2 + 1
        x = self.x + self.w + half if self.dir_x > 0 else self.x - half
        return x, self.y + self.h / 2

    def notice(self, player):
        spec = config.TRAP_BOLT
        mx, my = self.muzzle()
        ahead = (player.x - mx) * self.dir_x
        body_mid = player.y + config.PLAYER_H / 2
        self.armed = (not player.dead and 0 <= ahead <= spec['range'] and abs(body_mid - my) <= spec['band'])

    def is_harmful(self):
        return False

    def on_pickaxe_hit(self, player):
        return False

    def warning(self):
        return self.armed and self.timer <= config.TRAP_BOLT['telegraph']

    def update(self):
        spec = config.TRAP_BOLT
        if not self.armed:
            # 사거리 밖이면 다음 발을 장전해 둔다 (들어오자마자 쏘지 않고 예고부터)
            self.timer = max(self.timer, spec['telegraph'])
            return
        before = self.timer
        self.timer -= game_framework.frame_time
        if before > spec['telegraph'] >= self.timer:
            effect.telegraph(True)
        if self.timer <= 0:
            self.timer += spec['interval']
            fire_bolt(*self.muzzle(), self.dir_x, self.platforms, self)

    def draw(self):
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *config.COLOR_BOLT_TRAP, filled=True)
        # 활: 쏘는 쪽 면에 세로 막대, 예고 중이면 흰색으로 깜빡인다
        bow_w = max(4, self.w / 4)
        color = config.COLOR_BOLT_TRAP_BOW
        if self.warning() and int(self.timer / config.TELEGRAPH_BLINK) % 2 == 0:
            color = config.COLOR_PARRYABLE
        face = r if self.dir_x > 0 else l - bow_w
        camera.draw_rect(face, b - self.h / 4, face + bow_w, t + self.h / 4, *color, filled=True)
        if game_world.show_hitbox:
            camera.draw_rect(l, b, r, t, *config.COLOR_DEBUG_BODY)


class BoltTarget(EnemyBase):
    # 쇠뇌 과녁 (9.5): 반사 해금 직후 반사 연습용. objects ["target", x, y, id], (x, y) = 아래쪽 중심
    # 반사 플래그가 있고 부서지지 않았을 때만 생긴다 (Room.spawn_targets). 플레이어 쪽으로 interval마다 흰 예고 → 화살
    # 반사한 화살에 hits_to_break번 맞으면 부서지며 광석 (영구, broken). 적 목록에 넣어 반사탄 판정을 받는다
    # 곡괭이에는 회색 스파크만, 몸 접촉 피해 없음, 패링 숨 0
    kind = 'statue'

    def __init__(self, room_id, x, y, target_id, player, platforms, state):
        spec = config.BOLT_TARGET
        super().__init__(x, y, dict(spec, hp=1, speed=0, detect_range=0, attack_range=0, attack_cooldown=0),
                         player, platforms)
        self.gid = f'{room_id}:{target_id}'
        self.state_ref = state
        self.hits = 0
        self.timer = spec['interval']

    def update_ai(self):
        spec = config.BOLT_TARGET
        self.vx = 0
        self.face_player()
        if self.player.dead or abs(self.player.x - self.x) > spec['range']:
            self.timer = max(self.timer, spec['telegraph'])
            return
        before = self.timer
        self.timer -= game_framework.frame_time
        if before > spec['telegraph'] >= self.timer:
            effect.telegraph(True)
        if self.timer <= 0:
            self.timer += spec['interval']
            half = self.w / 2 + config.TRAP_BOLT['size'] / 2 + 1
            fire_bolt(self.x + self.face_dir * half, self.y + spec['muzzle_h'], self.face_dir, self.platforms, self)

    def move(self, dt):
        pass   # 제자리에 서 있다

    def deals_contact(self):
        return False

    def take_damage(self, damage, knockback=0):
        # 반사탄만 여기로 온다 (곡괭이는 combat.resolve에서 회색 스파크만)
        self.hits += 1
        self.shake_timer = config.ENEMY_HIT_SHAKE_TIME
        if self.hits >= config.BOLT_TARGET['hits_to_break']:
            self.shatter()

    def shatter(self):
        spec = config.BOLT_TARGET
        self.state_ref.broken.add(self.gid)
        self.hp = 0
        self.set_state(DEAD)
        game_world.remove_object(self)
        effect.wall_broken(self.x, self.y + self.h / 2, self.color)
        pickup.spill(self.x, self.y + self.h / 2, spec['ore'], self.player)

    def warning(self):
        return self.timer <= config.BOLT_TARGET['telegraph'] and self.state == IDLE

    def draw_body(self):
        spec = config.BOLT_TARGET
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *self.color, filled=True)
        # 과녁판: 남은 횟수만큼 동심원 (맞을 때마다 바깥 고리가 깨져 나간다) + 쇠뇌 활 (예고 중 흰색 깜빡임)
        left = spec['hits_to_break'] - self.hits
        cy = b + self.h * spec['ring_y']
        for i in range(left):
            radius = spec['ring_r'] * (left - i) / spec['hits_to_break']
            effect.draw_disc(self.x, cy, radius, spec['ring_colors'][i % 2])
        bow = config.COLOR_BOLT_TRAP_BOW
        if self.warning() and int(self.timer / config.TELEGRAPH_BLINK) % 2 == 0:
            bow = config.COLOR_PARRYABLE
        bow_w, bow_h = spec['bow']
        front = r if self.face_dir > 0 else l - bow_w
        my = b + spec['muzzle_h']
        camera.draw_rect(front, my - bow_h / 2, front + bow_w, my + bow_h / 2, *bow, filled=True)
