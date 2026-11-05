import config
from objects import effect
from objects.bosses.boss_base import BossBase
from objects.enemy_base import ACTIVE, RECOVER, STAGGER, WINDUP, Attack
from systems import camera, sound

# 정예 (10.4): 자세 게이지가 있고 한 번 처치하면 다시 나오지 않는다 (world_state.elites_defeated)
# 보스 공통 구조(11.2)에서 아레나 잠금·자세 게이지만 쓴다. 타이틀 카드 없음(늘 짧은 등장), 페이즈 없음,
# 처치 후 아레나가 안전지대가 되지 않는다. 처치 보상은 play_mode.on_elite_defeated
# 방 JSON: objects ["elite", x, y, 종류, id] (x, y = 발 중심)

CAPTAIN = config.ELITE_SHELL_CAPTAIN


class ShellCaptain(BossBase):
    # 갑각 대장 (R2 반격의 시련): 3연베기(흰) · 도약 내려찍기(흰) · 방패 돌진(빨강). 투사체 없음
    # → 반사 없이 패링·곡괭이로 공정하게 이길 수 있다. 처치하면 반사 해금 + 각인 2개
    kind = 'elite'
    boss_key = 'shell_captain'   # HUD 이름 (config.ELITE_NAME)

    def __init__(self, x, y, player, platforms, elite_gid):
        super().__init__(x, y, CAPTAIN, player, platforms)
        self.gid = elite_gid   # 'R2_08:captain' (elites_defeated에 남는다)
        self.left_ground = False
        s, lp, r = CAPTAIN['slash'], CAPTAIN['leap'], CAPTAIN['rush']
        dmg = CAPTAIN['damage']

        def slash(telegraph, recover):
            return Attack('slash3', True, telegraph, s['windup'], s['active'], recover, dmg, s['hitbox'])

        combo = CAPTAIN['combo_telegraph']
        self.patterns = dict(
            slash3=[slash(CAPTAIN['telegraph'], s['recover']), slash(combo, s['recover']),
                    slash(combo, CAPTAIN['last_recover'])],
            # 도약은 착지할 때까지 Active (active 시간은 상한)
            leap=[Attack('leap', True, CAPTAIN['telegraph'], lp['windup'], lp['air_time'] * 2, lp['recover'],
                         dmg, lp['hitbox'])],
            rush=[Attack('rush', False, r['telegraph'], r['windup'], r['active'], r['recover'], dmg,
                         r['hitbox'])])

    # ---------- 등장 ----------

    def wake(self, first):
        super().wake(False)   # 정예는 타이틀 카드 없이 짧은 등장만

    # ---------- 패턴 ----------

    def chase(self):
        self.vx = 0
        if self.player.dead:
            return
        self.face_player()
        dist = abs(self.player.x - self.x)
        near = dist <= CAPTAIN['near_range']
        if self.attack_cooldown <= 0:
            name = self.pick_pattern(CAPTAIN['near'] if near else CAPTAIN['far'])
            if name:
                self.remember_pattern(name)
                self.attack_queue = list(self.patterns[name])
                self.start_next_attack()
                return
        if not near:
            self.vx = self.face_dir * self.speed

    def is_leaping(self):
        return self.state == ACTIVE and self.attack is not None and self.attack.name == 'leap'

    def is_rushing(self):
        return self.state == ACTIVE and self.attack is not None and self.attack.name == 'rush'

    def next_phase(self):
        super().next_phase()
        if self.is_leaping():
            self.take_off()

    def take_off(self):
        # 플레이어 발밑(최대 max_dist)으로 air_time초 포물선. 높이는 air_time으로 정해진다
        lp = CAPTAIN['leap']
        t = lp['air_time']
        dx = max(-lp['max_dist'], min(lp['max_dist'], self.player.x - self.x))
        self.vx = dx / t
        self.vy = -config.GRAVITY * t / 2
        self.left_ground = False
        sound.play('dash')

    def land(self):
        effect.burst(self.x, self.y, CAPTAIN['leap']['dust'], config.COLOR_ROCK)
        camera.shake(*config.ROCKFALL_TRAP['shake'])
        sound.play('door')
        self.vx = 0
        self.set_state(RECOVER, self.attack.recover)

    def update_ai(self):
        # 도약 중에는 vx를 지우지 않는다 (기본 update_ai는 공격 상태에서 vx = 0). 착지는 move가 정한다
        if self.is_leaping():
            if self.state_timer <= 0:
                self.next_phase()
            return
        super().update_ai()

    def move(self, dt):
        if self.is_rushing():
            # 돌진 방향은 예고 때 바라본 방향 그대로
            self.vx = self.face_dir * CAPTAIN['rush']['speed']
        leaping = self.is_leaping()
        super().move(dt)
        if leaping:
            if not self.on_ground:
                self.left_ground = True
            elif self.left_ground:
                self.land()

    def on_parried(self):
        # 공중에서 패링당하면 그대로 떨어지며 비틀거린다 (가로 속도는 멈춤)
        super().on_parried()
        if self.state == STAGGER:
            self.vx = 0

    def get_attack_bb(self):
        if self.is_leaping():
            # 내려오는 동안만 몸 아래쪽 넓은 판정 (올라가는 중에는 없음)
            if self.vy > 0:
                return None
            w, h = self.attack.hitbox
            return self.x - w / 2, self.y - h / 2, self.x + w / 2, self.y + h / 2
        return super().get_attack_bb()

    # ---------- 그리기 ----------

    def draw_weapon(self, l, b, r, t):
        # 투구 장식 + 방패 (돌진 예고·돌진 중에는 몸 앞에 세운다)
        crest = self.w / 6
        camera.draw_rect(self.x - crest / 2, t, self.x + crest / 2, t + crest * 1.5, *config.COLOR_SHIELD, filled=True)
        rushing = self.attack is not None and self.attack.name == 'rush' and self.state != RECOVER
        shield_w, shield_h = CAPTAIN['rush']['hitbox']
        if rushing:
            sb = b + (self.h - shield_h) / 2
            if self.face_dir > 0:
                camera.draw_rect(r, sb, r + shield_w, sb + shield_h, *config.COLOR_SHIELD, filled=True)
            else:
                camera.draw_rect(l - shield_w, sb, l, sb + shield_h, *config.COLOR_SHIELD, filled=True)
            return
        # 평소에는 등 쪽에 작은 방패를 멘다
        back = self.x - self.face_dir * self.w / 2
        sw, sh = shield_w * 0.6, shield_h * 0.6
        sl = back - sw if self.face_dir > 0 else back
        camera.draw_rect(sl, b + self.h * 0.2, sl + sw, b + self.h * 0.2 + sh, *config.COLOR_SHIELD, filled=True)
        if self.state == WINDUP and self.attack is not None and self.attack.name != 'leap':
            super().draw_weapon(l, b, r, t)
