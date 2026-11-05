# 화면
SCREEN_W, SCREEN_H = 1280, 720
PX_PER_UNIT = 43           # 1유닛 ≈ 43px (주석의 'u')
MAX_FRAME_TIME = 0.05      # s, 첫 프레임 등 큰 frame_time 제한
DEBUG = True               # F1 hitbox, F3 전체 해금, F4 방 이동, F5 숨 무한, F6 숨 구간 기록, F7 개별 지급. 최종 빌드에서 False

# ===== 범위 (T34, 15.1) =====
SCOPE = 'full'             # 'minimum' | 'target' | 'full'
SEAL_CORES_REQUIRED = 3 if SCOPE == 'full' else 2
R6_GATE_RUNE = 'shadow' if SCOPE == 'full' else 'breakthrough'   # R6 통로를 여는 룬 (목표판은 장막 대신 돌파 구덩이)
SCOPE_REGIONS = dict(      # 범위별로 만드는 구역 (15.1). validate_rooms.py가 구역 검사에 쓴다
    minimum=['mine', 'corridor', 'moss'],
    target=['mine', 'corridor', 'moss', 'crystal', 'temple', 'tomb'],
    full=['mine', 'corridor', 'moss', 'crystal', 'temple', 'nest', 'tomb'],
)

# ===== 키 (T29) =====
# pico2d 상수 이름 문자열. systems/input.py에서 getattr(pico2d, name)으로 변환
KEYS = dict(
    left='SDLK_LEFT', right='SDLK_RIGHT', up='SDLK_UP', down='SDLK_DOWN',
    jump='SDLK_z', attack='SDLK_x', dash='SDLK_c', parry='SDLK_s',
    rune='SDLK_a',           # 짧게: 룬 기술 / 길게: 숨 고르기(회복)
    breakthrough='SDLK_d', map='SDLK_TAB', inventory='SDLK_i', pause='SDLK_ESCAPE',
)
DEBUG_KEYS = dict(hitbox='SDLK_F1', unlock_all='SDLK_F3', warp='SDLK_F4',
                  infinite_breath='SDLK_F5', record_breath='SDLK_F6', give='SDLK_F7')   # F6, F7
RUNE_HOLD_THRESHOLD = 0.25 # s, A를 이보다 오래 누르면 룬 기술 대신 숨 고르기

# ===== 물리 · 이동 (T29) =====
GRAVITY = -2400            # px/s^2 (pico2d는 y가 위로 증가)
MAX_FALL_SPEED = -860      # px/s
PLAYER_SPEED = 357         # px/s, 가속·감속 없음
JUMP_SPEED = 716           # px/s, 누르고 있는 동안 이 속도 유지
JUMP_HOLD_MAX = 0.15       # s → 꾹 누르면 약 210px (5u)
JUMP_HOLD_MIN = 0.06       # s → 톡 치면 약 43px (1u)
JUMP_CUT = 0.0             # 떼는 순간 상승 속도에 곱함 (0 = 즉시 정지, v2는 0.5)
COYOTE_TIME = 0.1
JUMP_BUFFER = 0.1
CORNER_CORRECTION = 8      # px
HARD_LAND_FALL_TIME = 1.1  # s
HARD_LAND_LOCK = 0.25      # s
DASH_DIST = 215            # px
DASH_TIME = 0.25
DASH_COOLDOWN = 0.6
DASH_INVINCIBLE = False    # 일반 대시는 무적 아님
EXIT_UP_BOOST = 900        # px/s, 위쪽 출구로 들어왔을 때 밀어올림

# ===== 곡괭이 공격 (T29) =====
ATTACK_COOLDOWN = 0.41
ATTACK_ACTIVE = 0.1
ATTACK_HITBOX = dict(side=(80, 50), up=(60, 85), down=(60, 85))  # (w, h) px
PICKAXE_DAMAGE = [5, 9, 13, 17, 21]   # 곡괭이 Lv1~5
ATTACK_RECOIL = 60         # px, 옆 공격 적중 시 플레이어가 밀리는 거리
ATTACK_RECOIL_TIME = 0.08  # s, 반동 거리를 이 시간 동안 나눠 민다
POGO_SPEED = 700
ENEMY_KNOCKBACK = 60
INPUT_BUFFER = 0.1         # s, 공격·패링·대시 선입력
THIRD_STRIKE = dict(interval=0.6, damage_mult=2.0, knockback=150, shake=dict(amp=5, time=0.12))  # interval = 적중과 적중 사이 최대 간격

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

# ===== 체력 (T31, 6.7 · 6.8) =====
HP_START = 5               # 칸
HP_MAX = 9                 # 광부 갑옷 Lv2~5에서 1칸씩
INVINCIBLE_ON_HIT = 1.3    # s
CONTACT_DAMAGE = 1         # 적 몸에 닿았을 때 (칸)
HAZARD_DAMAGE = 1          # 가시·산성·구덩이 (칸)
HAZARD_RESPAWN_FADE = 0.4  # s, 환경 피해 후 어두워지는 시간 (밝아지는 시간도 같음)
DAMAGE_CAP = 2             # 플레이어가 한 번에 받는 최대 피해 (칸)
SAFE_GROUND_TIME = 2.0     # s, 방에 safe_points가 없을 때 이만큼 연속으로 서 있던 바닥을 안전 지점으로
SAFE_POINT_RADIUS = 40     # px, safe_points의 이 거리 안에 서면 '밟은' 것
COLOR_FADE = (0, 0, 0)
PLAYER_HIT_STUN = 0.25     # s, 피격 경직 (조작 불가)
PLAYER_HIT_KNOCKBACK = 250 # px/s, 피격 경직 중 밀려나는 속도
BLINK_INTERVAL = 0.08      # s, 피격 무적 깜빡임 주기
# 타격감 (적중했을 때만 적용, 헛스윙은 휘두름음만)
HITSTOP_HIT = 0.03                 # s, 공격 1회당 1번
ENEMY_HIT_SHAKE = 3                # px, 맞은 적 몸 좌우 떨림 폭
ENEMY_HIT_SHAKE_TIME = 0.1         # s
ENEMY_FLINCH_TIME = 0.15           # s, 일반 적 피격 경직 (Idle/Chase에서만)
HIT_SPARK_COUNT = 6                # 세 번째 일격은 HIT_SPARK_MULT_STRONG배
HIT_SPARK_MULT_STRONG = 2
HIT_SPARK_SPEED = 400              # px/s, 최대 속도. 개별 속도는 × (1 - JITTER) ~ 1
HIT_SPARK_SPEED_JITTER = 0.5
HIT_SPARK_SPREAD = 50              # 도, 공격 방향 기준 좌우로 퍼지는 각도
HIT_SPARK_LIFE = 0.15              # s
HIT_SPARK_SIZE = 5                 # px
HIT_SPARK_COLOR = (255, 214, 102)  # 노란 스파크 (흰/빨강은 예고 전용이라 쓰지 않음)
PLAYER_SIZE = (28, 56)     # px, 몸 hitbox
PLAYER_W, PLAYER_H = PLAYER_SIZE
# 강착지 큰 먼지: 발밑에서 좌우로 퍼진다
HARD_LAND_DUST = dict(count=16, speed=(120, 320), life=0.35, size=7, color=(150, 140, 120),
                      spread=30)   # 도, 바닥에서 위로 퍼지는 최대 각도
HARD_LAND_SHAKE = dict(amp=4, time=0.1)
SLASH_BAND_RATIO = 0.6     # 옆 공격 베기 그림: hitbox 높이 중 위/아래 이 비율만 번갈아 칠한다
COLOR_PLAYER = (80, 160, 255)
COLOR_PLAYER_HARD_LAND = (60, 120, 200)  # 강착지 입력 잠금 중 색
COLOR_PLAYER_DASH = (180, 220, 255)  # 대시(무적) 중 색
COLOR_PLAYER_SLASH = (220, 240, 255)  # 공격 판정 중 베기 표시
COLOR_PLAYER_DEAD = (70, 70, 80)
COLOR_PLAYER_PARRY = (120, 255, 255)  # 패링 판정 중 몸 앞 방패 표시
COLOR_PLAYER_STUN = (110, 110, 150)   # 헛입력 경직 중 색
PARRY_SHIELD_W = 10        # px, 패링 방패 표시 두께

# 디버그
COLOR_DEBUG_BODY = (0, 255, 0)
COLOR_DEBUG_ATTACK = (255, 0, 0)
COLOR_DEBUG_EXIT = (255, 255, 0)  # 방 출구

# 지형
COLOR_SOLID = (90, 90, 100)
COLOR_ONEWAY = (150, 130, 90)

# 방 · 문
DOOR_W, DOOR_H = 60, 100   # px
DOOR_FRAME = 6             # px, 문틀 두께
COLOR_DOOR_FRAME = (60, 50, 40)
COLOR_DOOR_LOCKED = (110, 60, 50)
COLOR_DOOR_OPEN = (240, 220, 140)

# [v2] 보물상자 (x, y는 상자 아래쪽 중심, 템플릿의 chest_spot)
CHEST_W, CHEST_H = 52, 38  # px
CHEST_LID_H = 12           # px, 뚜껑 높이 (열리면 뚜껑이 위로 들린다)
CHEST_LID_LIFT = 14        # px
CHEST_BAND = 6             # px, 가운데 잠금쇠 폭
COLOR_CHEST = (170, 110, 50)
COLOR_CHEST_LOCKED = (95, 75, 60)   # 적이 남아 있을 때
COLOR_CHEST_OPENED = (110, 80, 50)
COLOR_CHEST_BAND = (255, 210, 90)
CHEST_PILLAR_TIME = 0.3    # s, 빛 기둥을 보여준 뒤 강화 화면
CHEST_PILLAR_W = 40        # px
CHEST_PILLAR_ALPHA = 200   # 0~255
COLOR_CHEST_PILLAR = (255, 240, 170)

# 패링
PARRY_WINDOW = 0.15        # s
PARRY_COOLDOWN = 0.5       # s, 성공 시 즉시 0으로
PARRY_FAIL_STUN = 0.4      # s
STUN_DAMAGE_BONUS = 1      # 패링 실패 경직 중 피격 시 +칸 (DAMAGE_CAP까지)
HITSTOP_PARRY = 0.08       # s
HITSTOP_KILL = 0.05        # s
ENEMY_STAGGER_TIME = 1.0   # s
STAGGER_DAMAGE_MULT = 1.5  # 비틀거리는 적이 받는 피해 배율
REFLECT_DAMAGE = 15        # 반사 투사체가 적·보스에 주는 피해 (적 체력 단위). × 투사체 reflect_mult × 각인 '거울 결정'
REFLECT_UNLOCK_FLAG = 'reflect'   # 이 플래그가 있어야 반사. 정예 갑각 대장 처치 시 추가
PROJECTILE_SHARD = dict(count=8, speed=(80, 260), life=0.2, size=4)  # 반사 해금 전 패링한 투사체가 튕겨 사라지는 파편. 색은 투사체 색

# ===== 월드 · 진행 (T33, 5.6 · 12.5) =====
START_ROOM = 'TEST_01'     # 새 게임 첫 방. T41에서 'R0_01'
TRANSITION_FADE = 0.25     # s, 방 전환 어두워짐·밝아짐 각각
TRANSITION_LOCK = 0.2      # s, 도착 후 출구를 무시하는 시간
EXIT_SPAWN_INSET = 48      # px, 도착 출구 안쪽으로 이만큼 들어온 자리
REGIONS = dict(            # 구역 이름·대표 색·기본 공기
    # rooms = 12.2 표의 방 수. 다 차기 전에는 구역에 걸린 검사가 경고만 낸다 (12.5 미작성 처리)
    mine=dict(name='광산', color=(120, 85, 55), air=None, rooms=4),       # None = 숨 게이지 없음
    corridor=dict(name='잊힌 회랑', color=(90, 100, 125), air='normal', rooms=12),
    moss=dict(name='이끼 동굴', color=(60, 120, 70), air='normal', rooms=12),
    crystal=dict(name='수정 광맥', color=(130, 90, 200), air='normal', rooms=12),
    temple=dict(name='침수 신전', color=(40, 120, 130), air='normal', rooms=10),
    nest=dict(name='그림자 둥지', color=(40, 50, 90), air='foul', rooms=10),
    tomb=dict(name='왕의 묘실', color=(170, 130, 60), air='thin', rooms=8 if SCOPE == 'full' else 7),
    test=dict(name='테스트', color=(110, 110, 120), air=None, rooms=0),   # data/rooms/test (개발용, 구역 검사 제외)
)
HUB_SHORTCUT_REGIONS = ['moss', 'crystal', 'temple', 'nest']   # R1 허브행 숏컷이 필요한 구역 (R2~R5, 12.5)
SAFE_ZONE_MAX_ROOMS = 4    # 어느 방에서든 가장 가까운 안전지대까지 최대 방 수 (게이트 방 제외)
COLLECTIBLE_COUNTS = dict(  # 임시. 12.7 구역별 수집품 수 (상점·NPC·보스 몫 제외). validate_rooms.py 개수 검사 기준
    full=dict(rare_ore=dict(corridor=3, moss=3, crystal=3, temple=3, nest=3, tomb=1),
              engraving=dict(corridor=1, moss=5, crystal=3, temple=3, nest=2, tomb=0),
              miner=dict(corridor=1, moss=2, crystal=2, temple=1, nest=1, tomb=1),
              map_stone=dict(corridor=1, moss=1, crystal=1, temple=1, nest=1, tomb=1),
              tablet=dict(corridor=3, moss=3, crystal=3, temple=2, nest=2, tomb=2)),
    target=dict(rare_ore=dict(corridor=3, moss=3, crystal=4, temple=5, tomb=1),
                engraving=dict(corridor=1, moss=5, crystal=3, temple=5, tomb=0),
                miner=dict(corridor=1, moss=2, crystal=2, temple=2, tomb=1),
                map_stone=dict(corridor=1, moss=1, crystal=1, temple=1, tomb=1),
                tablet=dict(corridor=3, moss=3, crystal=3, temple=2, tomb=2)),
    minimum=dict(rare_ore=dict(corridor=4, moss=4), engraving=dict(corridor=1, moss=5),
                 miner=dict(corridor=1, moss=2), map_stone=dict(corridor=1, moss=1),
                 tablet=dict(corridor=3, moss=3)),
)
REGION_BG_TINT = 0.2       # 0~1, 배경색을 구역 색 쪽으로 섞는 비율

# ===== 카메라 (T32, 14.2) =====
CAMERA_LERP = 8.0
CAMERA_LOOKAHEAD_X = 120
CAMERA_LOOK_VERTICAL = 180
CAMERA_LOOK_HOLD = 0.5
CAMERA_FALL_LOOKAHEAD = 120
CAMERA_CULL_MARGIN = 100   # px, 화면 밖 이만큼까지는 그린다 (5.3)

# ===== 룬 (T30. 레벨별 효과는 8장) =====
RUNE_MAX_LEVEL = dict(breath=5, burrow=3, brace=3, crystal=3, breakthrough=3, shadow=3)
ABILITY_RUNE = dict(      # 능력 → (룬, 필요 레벨). player.can(능력)이 본다 (6.2, 8.2 표)
    dash=('burrow', 1), rockfall=('burrow', 2), hard_soil=('burrow', 3),
    wall_cling=('brace', 1), thorn_cling=('brace', 2),
    crystal_step=('crystal', 1), crystal_arrow=('crystal', 2),
    breakthrough=('breakthrough', 1), breakthrough_pierce=('breakthrough', 2), air_breakthrough=('breakthrough', 3),
    shadow_dash=('shadow', 1),
)

# 각인 id (8.4 표 순서). T44에서 data/items.json으로 옮긴다. 지금은 F7 지급 메뉴만 쓴다
ENGRAVING_IDS = ['third_strike', 'quick_hands', 'long_handle', 'miners_grit', 'last_stand', 'deep_lung',
                 'parry_breath', 'steady_breath', 'thrifty_breath', 'wind_step', 'long_dash', 'dash_strike',
                 'mirror_crystal', 'counter_wave', 'sharp_counter', 'stone_skin', 'thorn_shell', 'compass',
                 'ore_magnet', 'first_breath', 'breath_echo']

# ===== 디버그 메뉴 (T34, F4 방 이동 · F7 개별 지급) =====
DEBUG_GIVE_FLAGS = ['reflect', 'whetstone', 'met_oram', 'intro_done']   # F7에서 켜고 끄는 플래그 (13.6)
DEBUG_MENU_W = 560         # px
DEBUG_MENU_ROWS = 16       # 한 화면에 보이는 줄 수 (넘치면 스크롤)
DEBUG_MENU_ROW_H = 30      # px
DEBUG_MENU_PAD = 20        # px
COLOR_DEBUG_MENU = (30, 30, 40)
COLOR_DEBUG_MENU_SELECTED = (255, 220, 120)
COLOR_DEBUG_MENU_ON = (130, 220, 120)

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
TELEGRAPH_BLINK = 0.06     # s, 예고 번쩍임 주기
COLOR_ENEMY_WINDUP = (255, 240, 180)   # 공격 모션 중 무기 표시
COLOR_ENEMY_SLASH = (255, 150, 60)     # 공격 판정 중 베기 표시
COLOR_ENEMY_STAGGER = (220, 210, 90)   # 패링당해 비틀거리는 중 색
# 플라잉 몹: 플레이어 머리 위 hover_height에 떠 있다가 급강하. dive_time 동안(착지하면 즉시) 몸 전체가 공격 판정
FLYER = dict(hp=20, speed=150, dive_speed=600, damage=1, telegraph=0.5,
             w=40, h=32, color=(120, 90, 170), detect_range=800, hover_height=220,
             attack_range=60, hover_tolerance=40, ceiling_margin=40,
             windup=0.15, dive_time=0.5, recover=0.6, attack_cooldown=1.2)
# 근거리 병사: 베기 2연타. 2타째는 combo_telegraph만큼 짧게 예고한다
# 방패 돌진(빨간 예고, 패링 불가): shield_rush_chance 확률로 베기 대신 rush_time 동안 rush_speed로 앞으로 돌진
MELEE = dict(hp=40, speed=180, damage=1, telegraph=0.5, shield_rush_chance=0.25,
             w=44, h=68, color=(170, 70, 70), detect_range=700, attack_range=80,
             windup=0.15, active=0.1, recover=0.25, combo_telegraph=0.3, combo_recover=0.6,
             attack_cooldown=0.8, hitbox=(70, 48),
             rush_telegraph=0.6, rush_windup=0.2, rush_time=0.4, rush_speed=650, rush_recover=0.7,
             rush_damage=1, rush_hitbox=(24, 64))
COLOR_SHIELD = (150, 150, 170)
# 원거리 궁수: keep_distance ± distance_tolerance를 유지하고, shoot_range 안이면 플레이어를 조준해 화살을 쏜다
ARCHER = dict(hp=30, keep_distance=400, arrow_speed=500, damage=1, telegraph=0.6,
              w=40, h=64, color=(70, 140, 90), detect_range=1280, speed=140,
              distance_tolerance=60, shoot_range=900,
              windup=0.2, active=0.05, recover=0.4, attack_cooldown=1.0)
COLOR_BOW = (170, 120, 60)
# 투사체 (화살 등). size는 정사각 hitbox 한 변, length는 화살 그림 길이
ARROW = dict(size=14, length=36, color=(240, 230, 200))
COLOR_REFLECTED = (120, 255, 255)  # 반사되어 플레이어 소유가 된 투사체
DISC_STEP = 3              # px, 원형 투사체를 가로 띠로 나눠 그리는 간격

# [v2] 적 - 마법사 루트
# 견습 마법사: 궁수처럼 keep_distance ± distance_tolerance 유지, shoot_range 안이면 조준해 마력탄 1발 (흰색)
APPRENTICE_MAGE = dict(hp=25, speed=120, keep_distance=450, bolt_speed=350,
                       damage=1, telegraph=0.7, cast_cooldown=2.0,
                       w=38, h=60, color=(110, 80, 170), detect_range=1280,
                       distance_tolerance=60, shoot_range=900,
                       windup=0.2, active=0.05, recover=0.5)
# 숙련 마법사: 마력탄 bolt_count발 부채꼴(사이각 bolt_spread도, 흰색) 또는
#   circle_chance 확률로 플레이어 발밑 마법진(빨간색, 패링 불가)
#   blink_trigger_dist 안으로 들어오면 blink_dist만큼 순간 후퇴 (예고 없음, blink_cooldown)
ADEPT_MAGE = dict(hp=45, speed=120, keep_distance=400, bolt_speed=450, bolt_count=3,
                  bolt_spread=15, damage=1, telegraph=0.6, cast_cooldown=2.5,
                  circle_chance=0.35, circle_radius=90, circle_delay=0.8,
                  blink_trigger_dist=150, blink_dist=250, blink_cooldown=4.0,
                  w=42, h=66, color=(80, 50, 140), detect_range=1280,
                  distance_tolerance=60, shoot_range=900,
                  windup=0.25, active=0.05, recover=0.6,
                  circle_telegraph=0.5, circle_windup=0.2, circle_recover=0.6, circle_damage=1)
COLOR_STAFF = (150, 110, 80)
COLOR_STAFF_ORB = (190, 140, 255)
# 마력탄: 화살과 같은 반사 처리, 원형. 반사하면 reflect_mult배 (견습 마법사를 반사탄 한 방에 처치하는 수준)
MAGIC_BOLT = dict(size=18, length=0, color=(190, 140, 255), reflect_mult=3.0, round=True)
# 바닥 마법진 (패링 불가): 빨간 테두리 예고 → delay 후 active 동안 빛 기둥 폭발, 기둥 안에 있으면 피해
# 테두리는 바닥에 눕힌 타원(세로 = 반지름 × ring_flat)을 점 ring_dots개로 그린다
MAGIC_CIRCLE = dict(active=0.12, pillar_h=150, ring_flat=0.3, ring_dots=24, dot=6,
                    warn_alpha=70, pillar_alpha=200, pillar_color=(255, 150, 60))

# [v2] 적 - 쌍검 루트
# 쌍단검 병사: 빠르게 접근해 combo연속 베기 (흰색). 첫 타 예고 telegraph, 이후 각 타는 combo_interval 예고
#   패링해도 연타가 끊기지 않고 다음 타로 이어간다 (연속 패링 연습). 마지막 타를 패링하면 비틀거린다
DUAL_DAGGER = dict(hp=35, speed=260, damage=1, telegraph=0.35,
                   combo=3, combo_interval=0.3,       # combo_interval >= TELEGRAPH_MIN
                   w=40, h=62, color=(60, 130, 150), detect_range=900, attack_range=70,
                   windup=0.08, active=0.08, recover=0.12, last_recover=0.7,
                   attack_cooldown=1.0, hitbox=(64, 44))
# 그림자 암살자: keep_distance ± distance_tolerance를 두고 배회. 공격 쿨타임이 끝나면
#   ① 순간이동 기습 (빨간색): 예고 → fade_time 동안 흐려짐 → 플레이어 등 뒤 offset px에 나타나 appear_windup 후 베기
#      (teleport_cooldown. 등 뒤가 벽·화면 밖이면 앞쪽에 나타난다)
#   ② stab_chance 확률로(또는 기습 쿨타임 중이면) 걸어서 접근해 정면 찌르기 (흰색)
#   흐려지는 동안 몸 알파값은 fade_alpha[0] → fade_alpha[1]
ASSASSIN = dict(hp=30, speed=200, damage=1, telegraph=0.5,
                teleport_cooldown=4.0, fade_time=0.4, stab_chance=0.5,
                w=38, h=64, color=(120, 60, 110), detect_range=1280, attack_range=80,
                keep_distance=320, distance_tolerance=60, attack_cooldown=1.2,
                stab_windup=0.2, stab_active=0.1, stab_recover=0.5, stab_hitbox=(80, 26),
                appear_windup=0.3, slash_active=0.12, slash_recover=0.7, slash_hitbox=(80, 60),
                offset=80, fade_alpha=(220, 0))
COLOR_DAGGER = (200, 210, 225)

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
BOSS_GREATSWORD = dict(hp=400, damage=1, heavy_damage=2,   # 빨간(패링 불가) 패턴 = heavy_damage
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
BOSS_TWINBLADE = dict(hp=600, damage=1, heavy_damage=2,   # 빨간(패링 불가) 패턴 = heavy_damage
                      phase2_hp_ratio=0.5, phase2_speed_mult=1.2,
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
# [v2] 대마법사 (1페이즈): keep_distance ± distance_tolerance를 유지하며 투사체로 압박. 넉백을 받지 않는다
# 패턴 선택: 거리 near_range 이하면 near, 그보다 멀면 far 가중치로 랜덤 (같은 패턴 3연속 금지)
# 순간이동: 플레이어가 blink_trigger_dist 안이면 반대쪽으로 blink_dist (공격 아님, 예고 없음, blink_cooldown)
# 견습 소환: 동시에 최대 summon_max, 쿨타임 summon_cooldown. 보스 좌우 summon_offset px에 나타난다
BOSS_MAGE = dict(hp=500, damage=1,
                 volley_count=5, volley_interval=0.3, bolt_speed=450,
                 orb_speed=250, orb_reflect_mult=3.0,
                 circle_count=3, circle_radius=100, circle_delay=0.8, circle_interval=0.4,
                 blink_trigger_dist=200, blink_dist=400,
                 summon_max=2, summon_cooldown=15.0,
                 w=60, h=110, color=(120, 70, 190), speed=110, detect_range=1280,
                 keep_distance=500, distance_tolerance=80, attack_cooldown=1.0, near_range=350,
                 blink_cooldown=3.0, orb_damage=2, circle_damage=1, summon_offset=120,
                 near=dict(volley=2, orb=1, barrage=3, summon=1),
                 far=dict(volley=3, orb=2, barrage=2, summon=1),
                 # 마력탄 연사 (흰색): Active 동안 volley_interval마다 1발씩, 쏠 때마다 플레이어 조준
                 volley=dict(telegraph=0.6, windup=0.2, recover=0.6),
                 # 대형 마력구 (흰색): 느린 큰 구체 1발
                 orb=dict(telegraph=0.8, windup=0.35, active=0.05, recover=0.8),
                 # 마법진 폭격 (빨간색): Active 동안 circle_interval마다 플레이어 위치에 마법진
                 barrage=dict(telegraph=0.7, windup=0.2, recover=0.8),
                 # 견습 소환 (흰색 번쩍임, 막을 공격 없음)
                 summon=dict(telegraph=0.6, windup=0.3, active=0.05, recover=0.8))
# 대마법사 마력탄은 반사해도 1배, 대형 마력구는 반사하면 orb_reflect_mult배 (반사 강화 배율과 곱해진다)
BOSS_BOLT = dict(size=20, length=0, color=(200, 150, 255), round=True)
MAGE_ORB = dict(size=56, length=0, color=(170, 100, 255), round=True,
                reflect_mult=BOSS_MAGE['orb_reflect_mult'])
COLOR_BOSS_STAFF_ORB = (220, 180, 255)
# 쌍검 기사 검기. 반사하면 reflect_mult배 피해 (반사 강화 배율과 곱해진다)
TWIN_WAVE = dict(size=36, length=48, color=(200, 160, 255), reflect_mult=3.0)
TELEPORT_PUFF = dict(count=10, speed=(100, 300), life=0.3, size=6)  # 색은 보스 몸 색
COLOR_TWINBLADE = (210, 210, 235)

# 진행
UPGRADE_CHOICES = 3
DEATH_DELAY = 1.5          # s, 사망 후 결과 화면으로 넘어가기 전 대기

# 강화 (효과 구현은 systems/upgrades.py)
UPGRADE_PARRY_WINDOW_BONUS = 0.05  # s
UPGRADE_REFLECT_MULT = 2.0
UPGRADE_PARRY_HEAL = 1   # 칸
UPGRADE_MAX_HP_BONUS = 1 # 칸 (HP_MAX까지)
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
HP_CELL = 26               # px, 체력 한 칸 (T31: 바 → 칸). 최대 체력만큼 칸 틀을 그린다
HP_CELL_GAP = 8            # px
HP_BAR_BORDER = 3          # px, HUD 틀 두께 (체력 칸·보스 바·아이콘 공통)
COLOR_HUD_FRAME = (20, 20, 25)
COLOR_HP_BACK = (70, 30, 30)
COLOR_HP_FILL = (220, 60, 60)
COLOR_HP_LOW = (255, 150, 60)   # 체력 1칸일 때
DASH_ICON_RADIUS = 22      # px, 대시 쿨타임 원형 반지름
DASH_ICON_DOTS = 24        # 원을 이루는 점 개수
DASH_ICON_DOT = 6          # px, 점 한 변
COLOR_DASH_READY = (180, 220, 255)
COLOR_DASH_COOL = (70, 80, 100)
COLOR_DASH_FILL = (120, 160, 220)
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
BOSS_NAME = dict(greatsword='대검 기사', mage='대마법사', twinblade='쌍검 기사')

# 결과 화면
COLOR_RESULT_DEAD = (239, 68, 68)
COLOR_RESULT_CLEAR = (255, 220, 120)

# 사운드 (assets/sounds/, 없거나 오디오 장치가 없으면 소리 없이 진행)
# 효과음 파일은 tools/gen_sounds.py로 합성. 볼륨은 0~128
SOUND_DIR = 'assets/sounds'
SOUND_VOLUME = dict(
    parry=110, parry_miss=60, swing=45, hit=100, enemy_hurt=60, kill=80,
    telegraph_white=55, telegraph_red=70, groggy=110, phase2=110,
    dash=55, jump=35, shoot=55, door=70, death=100, cursor=50, select=60, chest=80)
SOUND_MIN_INTERVAL = 0.03  # s, 같은 소리가 한 프레임에 겹쳐 커지는 것 방지
# 배경음 (파일을 넣으면 재생, 없으면 생략). ogg/mp3/wav
MUSIC_FILES = dict(battle='bgm_battle.ogg', boss='bgm_boss.ogg')
MUSIC_VOLUME = 48
