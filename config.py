# 화면
SCREEN_W, SCREEN_H = 1280, 720
GRAVITY = -2000            # px/s^2 (pico2d는 y가 위로 증가)
MAX_FRAME_TIME = 0.05      # s, 첫 프레임 등 큰 frame_time 제한

# 레이어 (depth)
DEPTH_BG, DEPTH_MAP, DEPTH_ENEMY, DEPTH_PLAYER, DEPTH_EFFECT, DEPTH_UI = range(6)
LAYER_COUNT = 6

# 폰트 (없으면 텍스트 생략)
FONT_PATH = 'C:/Windows/Fonts/malgun.ttf'
FONT_SIZE_TITLE = 72
FONT_SIZE_TEXT = 24

# 색
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (160, 160, 160)
COLOR_PLAY_BG = (30, 30, 40)

# 플레이어
PLAYER_HP = 100
PLAYER_SPEED = 300         # px/s
JUMP_SPEED = 800           # 초기 상승 속도, 최대 높이 약 160px
JUMP_CUT = 0.5             # Alt를 떼면 상승 속도에 곱함 (가변 점프)
INVINCIBLE_ON_HIT = 1.0    # s
DASH_DIST = 200            # px
DASH_TIME = 0.2            # s, 대시 중 무적
DASH_COOLDOWN = 3.0        # s
ATTACK_DAMAGE = [10, 10, 20]
COMBO_WINDOW = 0.5         # s, 다음 타 입력 허용
ATTACK3_KNOCKBACK = 150    # px
INPUT_BUFFER = 0.1         # s, 공격·패링 선입력
PLAYER_HIT_STUN = 0.25     # s, 피격 경직 (조작 불가)
PLAYER_HIT_KNOCKBACK = 250 # px/s, 피격 경직 중 밀려나는 속도
BLINK_INTERVAL = 0.08      # s, 피격 무적 깜빡임 주기
# 공격 단계별 시간 (1타, 2타, 3타): 선딜 → 판정 → 후딜
ATTACK_STARTUP = [0.06, 0.06, 0.10]   # s
ATTACK_ACTIVE = [0.10, 0.10, 0.12]    # s, 공격 hitbox 유지 시간
ATTACK_RECOVER = [0.10, 0.10, 0.18]   # s
ATTACK_HITBOX = [(60, 40), (60, 40), (80, 56)]  # px (가로, 세로), 몸 앞쪽에 붙음
PLAYER_W, PLAYER_H = 40, 64  # px, 몸 hitbox
COLOR_PLAYER = (80, 160, 255)
COLOR_PLAYER_DASH = (180, 220, 255)  # 대시(무적) 중 색
COLOR_PLAYER_SLASH = (220, 240, 255)  # 공격 판정 중 베기 표시
COLOR_PLAYER_DEAD = (70, 70, 80)
COLOR_PLAYER_PARRY = (120, 255, 255)  # 패링 판정 중 몸 앞 방패 표시
COLOR_PLAYER_STUN = (110, 110, 150)   # 헛입력 경직 중 색
PARRY_SHIELD_W = 10        # px, 패링 방패 표시 두께
# 플레이어 스프라이트 (없으면 도형으로 그림)
# 시트는 PLAYER_SPRITE_CELL 크기 칸을 왼→오, 위→아래 순서로 배치한 격자
PLAYER_IMAGE_DIR = 'assets/images/player'
PLAYER_SPRITE_CELL = 512   # px, 원본 시트 한 칸
PLAYER_SPRITE_SIZE = 72    # px, 화면에 그릴 한 칸 크기 (몸 높이가 PLAYER_H 정도)
PLAYER_SPRITE_FOOT = 3     # px, 칸 아래쪽 빈 공간 (발바닥을 y에 맞춤)
# 애니메이션별로 사용할 칸 번호. jump는 [상승, 낙하]
PLAYER_ANIM_FRAMES = {
    'idle': [0, 1, 2, 3],
    'run': [0, 1, 2, 3, 4, 5],
    'jump': [0, 2],
    'attack1': [0, 1, 2, 3],
    'attack2': [0, 1, 2, 3],
    'attack3': [0, 1, 2, 3],
    'parry': [0, 1, 2, 3],
    'parry_stun': [0, 1, 2, 3],
    'dash': [0, 1, 2, 3, 4, 5, 6, 7],
    'hit': [0, 1, 2, 3],
    'dead': [0, 1, 2, 3, 4, 5, 6, 7],
}
PLAYER_ANIM_FPS = {'idle': 6, 'run': 12}  # 반복 애니메이션 속도 (프레임/초)
PLAYER_DEAD_ANIM_TIME = 0.8  # s, 쓰러지는 애니메이션 길이 (끝나면 마지막 칸 유지)

# 디버그
COLOR_DEBUG_BODY = (0, 255, 0)
COLOR_DEBUG_ATTACK = (255, 0, 0)

# 지형
COLOR_SOLID = (90, 90, 100)
COLOR_ONEWAY = (150, 130, 90)

# 방 · 문
# 일반 전투방 템플릿 (data/rooms/ 아래 JSON 이름). 런 시작 시 여기서 중복 없이 RUN_COMBAT_ROOMS개를 뽑는다
ROOM_TEMPLATES = ['flat_01', 'platform_01', 'platform_02', 'canyon_01', 'canyon_02', 'mixed_01']
RUN_COMBAT_ROOMS = 4
DOOR_W, DOOR_H = 60, 100   # px
DOOR_FRAME = 6             # px, 문틀 두께
COLOR_DOOR_FRAME = (60, 50, 40)
COLOR_DOOR_LOCKED = (110, 60, 50)
COLOR_DOOR_OPEN = (240, 220, 140)

# 패링
PARRY_WINDOW = 0.15        # s
PARRY_COOLDOWN = 0.5       # s, 성공 시 즉시 0으로
PARRY_FAIL_STUN = 0.4      # s
STUN_DAMAGE_MULT = 1.5     # 경직 중 받는 피해 배율
HITSTOP_PARRY = 0.08       # s
HITSTOP_KILL = 0.05        # s
ENEMY_STAGGER_TIME = 1.0   # s
STAGGER_DAMAGE_MULT = 1.5  # 비틀거리는 적이 받는 피해 배율
CONTACT_DAMAGE = 5         # 적 몸에 닿았을 때 받는 피해 (비틀거림·그로기 중인 적은 없음)
REFLECT_DAMAGE_MULT = 1.0  # 반사 투사체 피해 배율 (강화로 2.0)

# 연출 (흔들림 세기는 px, 시간은 s)
SHAKE_PARRY, SHAKE_PARRY_TIME = 8, 0.15
SHAKE_HIT, SHAKE_HIT_TIME = 5, 0.12
SHAKE_KILL, SHAKE_KILL_TIME = 3, 0.08
COLOR_FLASH_PARRY = (255, 255, 255)
FLASH_PARRY_ALPHA = 170    # 0~255
FLASH_PARRY_TIME = 0.12    # s
COLOR_HIT_FLASH = (230, 30, 30)
HIT_FLASH_ALPHA = 150      # 0~255, 피격 시 화면 테두리 플래시
HIT_FLASH_TIME = 0.3       # s
HIT_FLASH_BORDER = 28      # px
PARTICLE_GRAVITY = -1200   # px/s^2
# speed는 (최소, 최대) px/s, life는 s, size는 px
PARRY_SPARK = dict(count=14, speed=(250, 600), life=0.25, size=6, color=(255, 250, 200))
KILL_PARTICLE = dict(count=18, speed=(150, 450), life=0.5, size=8)  # 색은 적 몸 색
HIT_PARTICLE = dict(count=10, speed=(150, 350), life=0.3, size=6)   # 색은 COLOR_HIT_FLASH
HURT_SPARK = dict(count=5, speed=(150, 350), life=0.15, size=5, color=(255, 230, 180))
PARRY_MISS_PUFF = dict(count=6, speed=(40, 120), life=0.3, size=6, color=(140, 140, 170))
DOOR_SPARK = dict(count=24, speed=(80, 300), life=0.6, size=6)      # 색은 COLOR_DOOR_OPEN
# 빛줄기: length는 (최소, 최대) 뻗는 길이 px, width는 굵기 px
PARRY_STREAK = dict(count=8, length=(70, 130), life=0.18, width=3, color=(255, 255, 230))
KILL_STREAK = dict(count=6, length=(40, 80), life=0.15, width=2, color=(255, 255, 255))
GROGGY_STREAK = dict(count=14, length=(140, 260), life=0.45, width=4, color=(255, 220, 120))
SHAKE_GROGGY, SHAKE_GROGGY_TIME = 12, 0.3
COLOR_FLASH_GROGGY = (255, 220, 120)
FLASH_GROGGY_ALPHA = 120   # 0~255
FLASH_GROGGY_TIME = 0.3    # s

# 예고
TELEGRAPH_MIN = 0.3        # s, 모든 공격 예고 최소 시간
COLOR_PARRYABLE = (255, 255, 255)
COLOR_UNPARRYABLE = (239, 68, 68)

# 적
KNOCKBACK_TIME = 0.15      # s, 넉백 거리를 이 시간 동안 나눠 밀어낸다
ENEMY_HURT_FLASH = 0.1     # s, 피해를 받았을 때 몸이 밝아지는 시간
TELEGRAPH_BLINK = 0.06     # s, 예고 번쩍임 주기
COLOR_ENEMY_HURT = (255, 200, 120)
COLOR_ENEMY_WINDUP = (255, 240, 180)   # 공격 모션 중 무기 표시
COLOR_ENEMY_SLASH = (255, 150, 60)     # 공격 판정 중 베기 표시
COLOR_ENEMY_STAGGER = (220, 210, 90)   # 패링당해 비틀거리는 중 색
# 플라잉 몹: 플레이어 머리 위 hover_height에 떠 있다가 급강하. dive_time 동안(착지하면 즉시) 몸 전체가 공격 판정
FLYER = dict(hp=20, speed=150, dive_speed=600, damage=10, telegraph=0.5,
             w=40, h=32, color=(120, 90, 170), detect_range=800, hover_height=220,
             attack_range=60, hover_tolerance=40, ceiling_margin=40,
             windup=0.15, dive_time=0.5, recover=0.6, attack_cooldown=1.2)
# 근거리 병사: 베기 2연타. 2타째는 combo_telegraph만큼 짧게 예고한다
# 방패 돌진(빨간 예고, 패링 불가): shield_rush_chance 확률로 베기 대신 rush_time 동안 rush_speed로 앞으로 돌진
MELEE = dict(hp=40, speed=180, damage=12, telegraph=0.5, shield_rush_chance=0.25,
             w=44, h=68, color=(170, 70, 70), detect_range=700, attack_range=80,
             windup=0.15, active=0.1, recover=0.25, combo_telegraph=0.3, combo_recover=0.6,
             attack_cooldown=0.8, hitbox=(70, 48),
             rush_telegraph=0.6, rush_windup=0.2, rush_time=0.4, rush_speed=650, rush_recover=0.7,
             rush_damage=15, rush_hitbox=(24, 64))
COLOR_SHIELD = (150, 150, 170)
# 원거리 궁수: keep_distance ± distance_tolerance를 유지하고, shoot_range 안이면 플레이어를 조준해 화살을 쏜다
ARCHER = dict(hp=30, keep_distance=400, arrow_speed=500, damage=10, telegraph=0.6,
              w=40, h=64, color=(70, 140, 90), detect_range=1280, speed=140,
              distance_tolerance=60, shoot_range=900,
              windup=0.2, active=0.05, recover=0.4, attack_cooldown=1.0)
COLOR_BOW = (170, 120, 60)
# 투사체 (화살 등). size는 정사각 hitbox 한 변, length는 화살 그림 길이
ARROW = dict(size=14, length=36, color=(240, 230, 200))
COLOR_REFLECTED = (120, 255, 255)  # 반사되어 플레이어 소유가 된 투사체

# 보스
POSTURE_MAX = 3            # 패링 성공 횟수로 그로기
GROGGY_TIME = 3.0          # s
GROGGY_SLOWMO = 0.3        # s
SLOWMO_SCALE = 0.3         # 슬로모션 중 월드에 전달하는 frame_time 배율
GROGGY_DAMAGE_MULT = 1.5   # 그로기 중 받는 피해 배율
BOSS_PARRY_RECOIL = 0.5    # s, 보스는 패링당해도 길게 비틀거리지 않고 이만큼만 멈칫한다
COLOR_BOSS_GROGGY = (230, 200, 60)
# 대검 기사: 느리고 묵직. 넉백을 받지 않는다
# 패턴 선택: 거리 near_range 이하면 near 가중치, thrust_range 이하면 far 가중치로 랜덤 (같은 패턴 3연속 금지)
# 가중치가 모두 0이면 걸어서 접근한다
BOSS_GREATSWORD = dict(hp=400, damage=20,
                       w=80, h=120, color=(110, 110, 140), speed=110, detect_range=1280,
                       attack_cooldown=0.9, near_range=200, thrust_range=750,
                       near=dict(slam=3, spin=2, thrust=0), far=dict(slam=0, spin=0, thrust=1),
                       # 내려찍기 (흰색): 정직한 단발
                       slam=dict(telegraph=0.7, windup=0.3, active=0.12, recover=0.8, hitbox=(140, 130)),
                       # 회전 베기 (빨간색): 몸 중심 좌우 광역, 대시로 회피
                       spin=dict(telegraph=0.8, windup=0.25, active=0.45, recover=0.9, hitbox=(360, 90)),
                       # 돌진 찌르기 (흰색): Active 동안 speed로 앞으로 돌진
                       thrust=dict(telegraph=0.6, windup=0.2, active=0.4, recover=0.9, hitbox=(70, 40),
                                   speed=900))
COLOR_GREATSWORD = (200, 200, 220)
# 쌍검 기사: 빠르고 날렵. 넉백을 받지 않는다
# 패턴 선택: 거리 near_range 이하면 near, 그보다 멀면 far 가중치로 랜덤 (같은 패턴 3연속 금지)
# 2페이즈(체력 phase2_hp_ratio 이하): 모든 동작 시간 ÷ phase2_speed_mult (예고는 TELEGRAPH_MIN 이상 유지),
#   이동 속도 × phase2_speed_mult, phase2_near/far 가중치(빨간 예고 비율 증가),
#   feint_chance 확률로 페이크(예고만 하고 공격하지 않은 채 feint_recover 동안 멈춤)
BOSS_TWINBLADE = dict(hp=600, damage=15, phase2_hp_ratio=0.5, phase2_speed_mult=1.2,
                      w=56, h=100, color=(70, 90, 140), color_phase2=(140, 60, 120),
                      speed=220, detect_range=1280, attack_cooldown=0.7, near_range=160,
                      near=dict(combo=3, teleport=1, wave=1), far=dict(combo=0, teleport=2, wave=3),
                      phase2_near=dict(combo=3, teleport=2, wave=1), phase2_far=dict(combo=0, teleport=3, wave=2),
                      feint_chance=0.25, feint_recover=0.5,
                      # 4연속 베기 (흰색): 첫 타만 길게 예고, 이후는 next_telegraph로 짧게 리듬을 탄다
                      # 패링해도 연타가 끊기지 않고 자세만 쌓인다. 마지막 타 뒤에만 last_recover로 길게 쉰다
                      combo=dict(count=4, telegraph=0.5, next_telegraph=0.3, windup=0.1, active=0.1,
                                 recover=0.15, last_recover=0.7, hitbox=(80, 50)),
                      # 순간이동 기습 (빨간색): 예고가 끝나면 플레이어 등 뒤 offset px로 이동해 windup 후 베기
                      teleport=dict(telegraph=0.6, windup=0.35, active=0.12, recover=0.8, hitbox=(90, 60),
                                    offset=90),
                      # 검기 발사 (흰색): 바라보는 방향으로 수평 발사
                      wave=dict(telegraph=0.6, windup=0.2, active=0.05, recover=0.6, speed=550))
# 쌍검 기사 검기. 반사하면 reflect_mult배 피해 (반사 강화 배율과 곱해진다)
TWIN_WAVE = dict(size=36, length=48, color=(200, 160, 255), reflect_mult=3.0)
TELEPORT_PUFF = dict(count=10, speed=(100, 300), life=0.3, size=6)  # 색은 보스 몸 색
COLOR_TWINBLADE = (210, 210, 235)

# 진행
UPGRADE_CHOICES = 3
DEATH_DELAY = 1.2          # s, 사망 후 결과 화면으로 넘어가기 전 대기
# 보스방: (런에서 몇 번째 자리에 끼울지 0부터, 템플릿 이름). 앞에서부터 차례로 끼운다
# 전투1~3 다음에 중간 보스, 전투4 다음에 최종 보스
RUN_BOSS_ROOMS = [(3, 'arena_greatsword'), (5, 'arena_twinblade')]
# n번째 방(보스방 포함, 1부터)을 클리어하고 문에 들어가면 강화 선택: 전투1 후, 중간 보스 후
RUN_UPGRADE_AFTER = [1, 4]

# 강화 (효과 구현은 systems/upgrades.py)
UPGRADE_PARRY_WINDOW_BONUS = 0.05  # s
UPGRADE_REFLECT_MULT = 2.0
UPGRADE_PARRY_HEAL = 5
UPGRADE_MAX_HP_BONUS = 30
UPGRADE_ATTACK_MULT = 1.2
UPGRADE_ATTACK3_MULT = 1.5
UPGRADE_INVINCIBLE_BONUS = 0.3     # s
UPGRADE_MAX_JUMPS = 2
UPGRADE_DASH_DIST_MULT = 1.5
UPGRADE_DASH_COOLDOWN_MULT = 0.7
UPGRADE_DASH_ATTACK_MULT = 2.0
# 패링 성공 시 검기: 플레이어 소유 투사체로 바라보는 방향에 발사
SWORD_WAVE = dict(speed=700, damage=20, size=40, length=40, color=(150, 230, 255))
UPGRADE_CATEGORIES = ['parry', 'stat', 'util']
UPGRADE_CATEGORY_NAME = dict(parry='패링 변형', stat='기초 스탯', util='유틸리티')
COLOR_UPGRADE = dict(parry=(120, 220, 255), stat=(240, 110, 90), util=(130, 220, 120))

# 강화 선택 화면
CARD_W, CARD_H = 300, 260  # px
CARD_GAP = 40              # px
CARD_PAD = 20              # px, 카드 안쪽 여백
CARD_BORDER = 4            # px
CARD_STRIPE_H = 16         # px, 카드 위쪽 카테고리 색 띠
CARD_LINE_H = 30           # px, 설명 줄 간격
FONT_SIZE_SMALL = 18
DIM_ALPHA = 170            # 0~255, 강화 선택 중 뒤 화면을 어둡게
COLOR_DIM = (0, 0, 0)
COLOR_CARD = (40, 40, 52)
COLOR_CARD_BORDER = (80, 80, 95)
COLOR_CARD_SELECTED = (255, 220, 120)

# HUD (가장자리에만 배치, 좌표는 화면 가장자리로부터 px)
HUD_MARGIN = 20
HP_BAR_W, HP_BAR_H = 300, 22
HP_BAR_BORDER = 3
COLOR_HUD_FRAME = (20, 20, 25)
COLOR_HP_BACK = (70, 30, 30)
COLOR_HP_FILL = (220, 60, 60)
COLOR_HP_LOW = (255, 150, 60)
HP_LOW_RATIO = 0.3         # 이 비율 이하면 체력 바 색이 바뀐다
DASH_ICON_RADIUS = 22      # px, 대시 쿨타임 원형 반지름
DASH_ICON_DOTS = 24        # 원을 이루는 점 개수
DASH_ICON_DOT = 6          # px, 점 한 변
COLOR_DASH_READY = (180, 220, 255)
COLOR_DASH_COOL = (70, 80, 100)
COLOR_DASH_FILL = (120, 160, 220)
HUD_HP_TEXT_W = 60         # px, 체력 숫자 자리 (그 오른쪽부터 강화 아이콘)
UPGRADE_ICON = 36          # px, 강화 아이콘 한 변
UPGRADE_ICON_GAP = 6       # px
UPGRADE_ICON_PAD = 4       # px, 아이콘 안 글자 여백
FONT_SIZE_ICON = 14

# 보스 HUD (하단 중앙): 체력 바 + 그 아래 자세 게이지 (POSTURE_MAX칸)
BOSS_BAR_W, BOSS_BAR_H = 640, 18
BOSS_POSTURE_H = 10        # px
BOSS_POSTURE_GAP = 6       # px, 체력 바와 자세 게이지 사이 · 자세 칸 사이
BOSS_NAME_GAP = 16         # px, 체력 바 위 이름 글자 중심까지
COLOR_BOSS_HP = (200, 50, 50)
COLOR_POSTURE_BACK = (50, 50, 60)
COLOR_POSTURE_FILL = (255, 220, 120)
BOSS_NAME = dict(greatsword='대검 기사', twinblade='쌍검 기사')

# 결과 화면
COLOR_RESULT_DEAD = (239, 68, 68)
COLOR_RESULT_CLEAR = (255, 220, 120)

# 사운드 (assets/sounds/, 없거나 오디오 장치가 없으면 소리 없이 진행)
# 효과음 파일은 tools/gen_sounds.py로 합성. 볼륨은 0~128
SOUND_DIR = 'assets/sounds'
SOUND_VOLUME = dict(
    parry=110, parry_miss=60, swing=45, hit=100, enemy_hurt=60, kill=80,
    telegraph_white=55, telegraph_red=70, groggy=110, phase2=110,
    dash=55, jump=35, shoot=55, door=70, death=100, cursor=50, select=60)
SOUND_MIN_INTERVAL = 0.03  # s, 같은 소리가 한 프레임에 겹쳐 커지는 것 방지
# 배경음 (파일을 넣으면 재생, 없으면 생략). ogg/mp3/wav
MUSIC_FILES = dict(battle='bgm_battle.ogg', boss='bgm_boss.ogg')
MUSIC_VOLUME = 48
