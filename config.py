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
ATTACK_COOLDOWN_QUICK = 0.25   # 각인 '빠른 손놀림'
ATTACK_ACTIVE = 0.1
ATTACK_HITBOX = dict(side=(80, 50), up=(60, 85), down=(60, 85))  # (w, h) px
ATTACK_RANGE_LONG = 1.25   # 각인 '긴 자루' (닿는 길이: 옆 공격 w, 위·아래 공격 h)
PICKAXE_DAMAGE = [5, 9, 13, 17, 21]   # 곡괭이 Lv1~5
ATTACK_RECOIL = 60         # px, 옆 공격 적중 시 플레이어가 밀리는 거리
ATTACK_RECOIL_TIME = 0.08  # s, 반동 거리를 이 시간 동안 나눠 민다
POGO_SPEED = 700
ENEMY_KNOCKBACK = 60
CRACK_WALL_HITS = 3
ORE_VEIN_HITS = 5
ORE_VEIN_LEVEL = 3         # 광맥벽은 곡괭이 Lv3 이상
ORE_CHUNK_HITS = 5
ORE_PER_CHUNK_HIT = 2
INPUT_BUFFER = 0.1         # s, 공격·패링·대시 선입력
THIRD_STRIKE = dict(interval=0.6, damage_mult=2.0, knockback=150, shake=dict(amp=5, time=0.12))  # interval = 적중과 적중 사이 최대 간격

# 레이어 (depth)
DEPTH_BG, DEPTH_MAP, DEPTH_ENEMY, DEPTH_PLAYER, DEPTH_EFFECT, DEPTH_UI = range(6)
LAYER_COUNT = 6

# 폰트 (없으면 텍스트 생략)
FONT_PATH = 'C:/Windows/Fonts/malgun.ttf'
FONT_SIZE_TITLE = 72
FONT_SIZE_TEXT = 24
FONT_FALLBACK_PATH = 'C:/Windows/Fonts/arial.ttf'   # FONT_PATH(한글)가 없을 때. 문구는 영어 대체 (ui/font.py)

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

# ===== 숨 (T37, 7.2 · 7.3. # 임시 = T58에서 확정, 그 전에는 바꾸지 않는다. 예외는 0장 14번) =====
# 숨의 단위는 '초': 소모 배율 1.0에서 1초에 1씩 준다
BREATH_CAPACITY = [25, 50, 75, 105, 140, 175]  # 임시. 인덱스 = 숨의 룬 레벨 (0 = 룬 없음)
BREATH_DRAIN = 1.0                              # 임시. 초당 기본 소모
BREATH_DRAIN_MULT = dict(normal=1.0, spore=2.0, water=3.0, foul=1.3, thin=1.5, void=2.5)  # 임시. void = R6 통로
BREATH_REFILL_RATE = 40.0  # 임시. 안전지대 안에서 초당 회복
AIR_VENT_REFILL = 12.0     # 임시. 숨구멍 1회 회복량
AIR_VENT_COOLDOWN = 20.0   # 임시. 같은 숨구멍 재사용 대기
CRYSTAL_POCKET_REFILL = 6.0  # 임시. R3 결정 숨주머니를 깼을 때
BREATH_PER_PARRY = 3.0     # 임시. 각인 '받아친 숨'(parry_breath) 장착 시에만
PARRY_BREATH_PER_ENEMY_MAX = 3   # 일반 적 한 마리에게서 패링 숨을 얻는 최대 횟수 (보스·정예는 제한 없음)
PARRY_BREATH_ENGRAVING_LOCKED = False  # True면 '받아친 숨'을 숨의 룬 1번 홈에서 뺄 수 없음
BREATH_PER_KILL = 0.0      # 임시. 0이면 처치로는 숨을 얻지 않음
BREATH_GROGGY_BURST = 15.0 # 임시. 보스 그로기 때 공기 주머니
HEAL_BREATH_COST = 15.0    # 임시. 숨 고르기 1칸 (완료 시 차감, 그때 모자라면 취소)
HEAL_TIME = 0.9            # s
SKILL_BREATH_COST = 8.0    # 임시. 룬 기술 1회
SUFFOCATE_INTERVAL = 3.0   # 임시. 숨 0일 때 이 간격마다 체력 1칸 (게이트 방 안 제외)
BREATH_GATE_BLACKOUT_FADE = 1.0  # s, 게이트 기절 페이드
BREATH_GATE_LOCKED_TIME = 1.5    # s, 요구 레벨 미달로 게이트 방에 들어가면 이 시간 동안 숨이 0까지 떨어진 뒤 기절
BREATH_LOW_RATIO = 0.25    # 이 비율 아래면 경고 연출
BREATH_EXIT_GRACE = 1.0    # s, 안전지대를 나선 직후 소모 시작까지 유예
BREATH_USE_TARGET = dict(  # 임시. 플레이테스트 목표 (7.6): 처음 하는 플레이어가 쓴 숨 ÷ 그 시점 기본 용량
    gate=(0.6, 0.85),      # 게이트 통로 (요구 레벨로 지날 때). 이 범위면 '빠듯하지만 통과'
    segment=0.8,           # 일반 구간 (안전지대·숨구멍 사이) 상한
)
BREATH_BUDGET_PATH = 'data/breath_budget.json'   # F6 측정 기록 (13.5). 한 번 누를 때마다 JSON 한 줄
# 숨 연출 (14.1 · 14.3 · 14.5). 흰색·빨간색은 쓰지 않는다
BREATH_BAR_PX = 2.5        # px, 숨 1당 게이지 길이 (용량이 늘면 막대도 길어진다)
BREATH_BAR_H = 12          # px
BREATH_BAR_GAP = 12        # px, 체력 칸 아래 간격
BREATH_LOW_BLINK = 0.2     # s, 숨 부족 깜빡임 주기
BREATH_FLOW_GAP = 18       # px, 배율 > 1일 때 게이지 안 흐름 무늬 간격
BREATH_FLOW_SPEED = 30     # px/s, 흐름 무늬 속도 (× 배율)
BREATH_FLASH_TIME = 0.3    # s, 패링 숨을 얻었을 때 게이지 반짝
BREATH_GATE_HATCH = 8      # px, 게이트 방 안일 때 게이지 테두리 빗금 간격
COLOR_BREATH = (120, 200, 240)        # 하늘색
COLOR_BREATH_BACK = (30, 50, 70)
COLOR_BREATH_LOW = (60, 100, 140)     # 숨 부족 깜빡임
COLOR_BREATH_REFILL = (170, 230, 255) # 안전지대 안에서 차오를 때
COLOR_BREATH_FLASH = (220, 245, 255)
COLOR_BREATH_FLOW = (70, 140, 190)
COLOR_BREATH_GATE = (40, 40, 60)      # 게이트 방 빗금
BREATH_VIGNETTE_W = 90     # px, 숨 부족 시 화면 가장자리 어둠 두께 (BREATH_VIGNETTE_LAYERS겹)
BREATH_VIGNETTE_LAYERS = 3
BREATH_VIGNETTE_ALPHA = 200   # 0~255, 숨 0일 때 가장 바깥 겹
SUFFOCATE_FLASH = dict(alpha=150, time=0.3)        # 질식 피해 때 화면 어둡게 깜빡
SAFE_ENTER_FLASH = dict(alpha=40, time=0.4)        # 안전지대 진입 때 화면이 살짝 밝아짐. 색은 COLOR_BREATH_REFILL
MEND_RING = dict(dots=16, size=5, radius=(40, 14))  # 숨 고르기 중 몸 둘레 점 고리 (반지름: 시작 → 완료)
COLOR_MEND = (150, 220, 250)
AIR_VENT_RADIUS = 14       # px, 숨구멍 (x, y는 중심). 닿는 판정은 이 반지름의 정사각형
AIR_VENT_WIND = dict(count=3, rise=40, period=1.2, size=4)  # 숨구멍 위로 오르는 공기 점 (rise px를 period초에)
COLOR_AIR_VENT = (120, 200, 240)
COLOR_AIR_VENT_USED = (60, 90, 110)
BREATH_ZONE_ALPHA = 50     # 0~255, 숨 배율 영역 칠
BREATH_ZONE_DOT_GAP = 40   # px, 포자 지대 점 무늬 간격
BREATH_ZONE_DOT = 4        # px
COLOR_BREATH_ZONE = dict(spore=(220, 200, 80), water=(40, 160, 170), foul=(90, 100, 70),
                         thin=(150, 140, 120), void=(50, 40, 70), normal=(120, 120, 120))
BREATH_GATE_LINE_GAP = 120 # px, 게이트 방 빗금 간격
BREATH_GATE_LINE_W = 6     # px
BREATH_GATE_ALPHA = 140    # 0~255
COLOR_BREATH_GATE_LINE = (15, 15, 25)   # 배경보다 어두운 빗금
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

# 환경 기믹 (T35, 12.6). 크기가 방 JSON에 없는 레버만 여기서 정한다
COLOR_SPIKE = (200, 200, 215)
COLOR_ACID = (120, 200, 60)
SPIKE_W = 16               # px, 가시 한 개의 밑변
SPIKE_STEP = 4             # px, 가시 삼각형을 쌓아 그리는 가로줄 두께
COLOR_CRACK_WALL = (110, 100, 95)
COLOR_CRACK_LINE = (40, 35, 35)
CRACK_WIND = dict(count=6, dist=70, period=1.6, size=3)   # 균열벽(숨은 벽) 바람 단서: 양옆 dist px에서 균열로 빨려 드는 먼지 (7.5)
COLOR_CRACK_WIND = (175, 165, 150)
COLOR_ORE_CHUNK = (95, 85, 80)
COLOR_ORE = (240, 190, 90)
ORE_CHUNK_DOTS = 4         # 광석 덩어리 표면의 광석 점 개수
COLOR_GATE = (110, 60, 50)
COLOR_GATE_BAR = (60, 40, 35)
COLOR_ONE_WAY_MARK = (240, 220, 140)   # 한쪽 문의 열리는 쪽 표시
GATE_BAR_GAP = 16          # px, 문 창살 간격
LEVER_W, LEVER_H = 24, 48  # px, (x, y)는 레버 아래쪽 중심
LEVER_STICK = 36           # px, 손잡이 길이
COLOR_LEVER_BASE = (80, 70, 60)
COLOR_LEVER = (200, 170, 90)
COLOR_LEVER_ON = (130, 220, 120)
# 낙석 함정 (T41, 12.6): 방 JSON [x, y, w, h, "rockfall"] = 가로 x~x+w에 떨어져 바닥 y에 닿는다. 돌은 y+h에서 출발
# 몸 가운데가 영역 가운데에서 가로 range 안에 들어오면 빨간 그림자 warn초 → 낙석 → cooldown초 뒤 다시 대기
ROCKFALL_TRAP = dict(range=420, warn=0.6, fall_speed=1300, rock_h=48, cooldown=2.5,
                     shadow_h=10, shadow_alpha=150, shake=(5, 0.15),
                     debris=dict(count=10, speed=(120, 380), life=0.35, size=6))
COLOR_ROCK = (115, 95, 75)
COLOR_ROCK_SHADOW = (220, 40, 40)   # 빨간 예고 (14.5)

# 안전지대 (T36, 13.1). 흰색·빨간색은 쓰지 않는다. 의자 (x, y)는 아래쪽 중심
COLOR_SAFE_ZONE = (70, 150, 90)       # 초록빛 이끼
SAFE_ZONE_ALPHA = 45       # 0~255, 영역 칠
SAFE_ZONE_MOSS_H = 10      # px, 영역 바닥의 이끼 띠
SEAT_W, SEAT_H = 72, 28    # px
SEAT_BACK_H = 36           # px, 등받이 돌 높이 (몸 판정에는 넣지 않음)
COLOR_SEAT = (95, 110, 95)
COLOR_SEAT_RUNE = (140, 230, 160)     # 의자에 새긴 룬 문양 (앉으면 밝아짐)
COLOR_SEAT_RUNE_OFF = (80, 130, 95)
SIT_PROMPT_GAP = 16        # px, 앉을 수 있을 때 머리 위 ↑ 표시까지
SIT_BODY_RATIO = 0.7       # 앉아 있는 동안 몸을 이 비율 높이로 그린다 (판정은 그대로)

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
START_ROOM = 'R0_01'       # 새 게임 첫 방 (도입부 광산)
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
CARVER_FROM_HUB_MAX = 10.0 # s, R1 허브 안전지대 → 새김터 이동 시간 상한
R1_SEGMENT_MAX = 15.0      # 임시. s, 숨의 룬 전 R1에서 숨 회복 지점 사이 최단 이동 시간 상한 (용량 25 기준)
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

# ===== 도입부 (T41, 2.2) =====
# 광산(R0) 방 + 방 JSON triggers [x, y, w, h, 스크립트 이름, id] (systems/script.py). 처음 한 번만 (flags 'intro_done')
INTRO_WAKE_ZONE = 'R1_01:safe_a'   # 깨어나는 안전지대 = 자동 저장되는 rest_seat (13.6)
INTRO = dict(
    omen_shake=(6, 0.9),            # 이상 징후: 멀리서 울림 (세기 px, 시간 s)
    bats=dict(count=9, speed=(380, 560), w=14, h=8, flap=0.12, spread=260, delay=0.4,    # 반대쪽으로 날아가는 박쥐 떼
              height=(0.45, 0.9), bob=40, bob_speed=8),   # height = 화면 높이 비율, bob = 위아래 흔들림 px/s
    collapse_speed=250,             # px/s, 무너짐이 오른쪽으로 쫓아오는 속도 (PLAYER_SPEED보다 느리게)
    collapse_lead=420,              # px, 붕괴 시작 때 플레이어 뒤로 떨어진 거리
    collapse_shake=(7, 0.2),        # 붕괴 중 매 프레임 다시 거는 흔들림
    collapse_rubble=dict(rate=14, w=(16, 40), speed=(500, 900), life=1.0, spread=120),   # 무너짐 앞 spread px 안에 떨어지는 흙덩이 (개/s)
    fall_shake=(14, 0.6),           # 바닥이 꺼질 때
    black_fade=0.8,                 # s, 추락 끝 암전
    black_hold=1.4,                 # s, 깨어나기 전 검은 화면
    wake_fade=1.2,                  # s, 깨어나며 밝아짐
    hint_time=4.0,                  # s, 안내 문구가 HUD에 떠 있는 시간
    shaft_alpha=26,                 # 깨어나는 방 위 구멍으로 드는 바깥 공기 줄기
)
INTRO_SHAFT_COLORS = [(120, 85, 55), (70, 68, 66), (90, 100, 125)]   # 추락 갱 배경: 흙 → 암반 → 고대 석벽 (위 → 아래)
COLOR_COLLAPSE = (45, 35, 28)
COLOR_BAT_SWARM = (35, 30, 40)
SIGN = dict(y=170, pad=10, line_h=30, post_w=8, narrow=0.55)   # 벽 간판: y = 바닥에서 간판 아래까지, narrow = 영문·기호 글자 폭 비율
COLOR_SIGN = (105, 75, 45)
COLOR_SIGN_TEXT = (240, 220, 170)
INTRO_TEXT = dict(         # 간판(sign)·안내(hint) 트리거 id → (한글, 영어 대체)
    sign_move=('← →  이동     X  곡괭이', '← →  Move     X  Pickaxe'),
    sign_talk=('↑  말 걸기 · 읽기', '↑  Talk · Read'),
    sign_jump=('Z  누르는 만큼 높이 점프', 'Hold Z to jump higher'),
    sign_pogo=('공중에서 ↓ + X  아래 찍기', 'In the air  ↓ + X  Down strike'),
    sign_run=('무너진다! 오른쪽으로 달려라', 'Cave-in! Run right!'),
    hint_safe=('바람이 드는 곳 — 여기서는 숨을 쉴 수 있다', 'Air flows here - you can breathe'),
    hint_breath=('숨이 줄어든다. 안전지대에서 다시 찬다', 'Breath runs out. Safe zones refill it'),
)

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
RUNE_UPGRADE_COST = dict(  # 임시. 레벨 n→n+1 비용 (광석, 희귀 광석). 인덱스 0 = Lv1→2 (8.3)
    breath=[(60, 0), (400, 1), (900, 1), (1600, 2)],   # 첫 강화 150 → 60 (R1에서 확실히 모을 수 있는 양)
    burrow=[(300, 1), (900, 1)],
    brace=[(400, 1), (1000, 1)],
    crystal=[(500, 1), (1200, 2)],
    breakthrough=[(700, 1), (1500, 2)],
    shadow=[(900, 1), (1800, 2)],
)
RUNE_ORDER = ['breath', 'burrow', 'brace', 'crystal', 'breakthrough', 'shadow']   # 강화 목록 순서 (8.2 표)
HINT_FAIL_COUNT = 2        # 숨막이 갱에서 기절한 횟수 → 보름 힌트, 한 번 더 기절하면 지도 물음표 (7.5)

# 룬 획득 연출 (T43, 8.5). rune_get_mode. 흰색·빨간색은 쓰지 않는다
RUNE_GET = dict(
    hitstop=0.1,           # s, 처음 멈춤
    dim=0.3,               # s, 화면이 어두워짐
    absorb=0.8,            # s, 룬 문양이 플레이어에게 흡수
    flash=0.3,             # s, 섬광 (구역색)
    short=0.5,             # s, 강화 때 짧은 연출 (8.3). 문양 흡수 + 섬광을 이 시간에 몰아서
    dim_alpha=170,         # 0~255
    glyph_size=56,         # px, 룬 문양 한 변
    glyph_rise=220,        # px, 문양이 처음 떠 있는 높이 (플레이어 머리 위)
    flash_alpha=150,       # 0~255
)
RUNE_HINT_MAX_RUNES = 3    # 보유 룬이 이 수 이하일 때만 카드에 '룬지기' 안내 줄 (8.3 '처음 3번만')
COLOR_RUNE_GLYPH = (140, 180, 220)
RUNE_CARD = dict(w=560, h=300, pad=28, line_h=34)   # px, 설명 카드
CARVER_CARD = dict(w=300, h=230, gap=24, top=560, visible=3)   # px, 강화 목록 카드 (top = 카드 위쪽 화면 y, visible장씩 ←→로 넘김)
COLOR_MAP_QUESTION = (240, 200, 120)     # 지도 새김터 물음표 (7.5)

ENGRAVE_SLOTS = dict(      # 룬 레벨별 각인 홈 수 (인덱스 = 룬 레벨)
    breath=[0, 2, 2, 3, 3, 4], burrow=[0, 1, 1, 2], brace=[0, 1, 1, 2],   # breath는 '받아친 숨' 몫으로 +1
    crystal=[0, 1, 1, 2], breakthrough=[0, 1, 1, 2], shadow=[0, 1, 1, 2],
)
PICKAXE_ENGRAVE_SLOTS = [1, 1, 2, 2, 3]   # 곡괭이 Lv1~5
ITEMS_PATH = 'data/items.json'   # 각인·수집품 이름·설명·대상 (각인 id 목록 = kind가 engraving인 항목, 8.4 표 순서)

# ===== 각인 효과 수치 (키 = 8.4 표의 id) =====
ENGRAVING = dict(
    miners_grit=1.2,                       # 곡괭이 피해 배율
    last_stand=1.75,                       # 체력 1칸일 때 피해 배율
    deep_lung=1.15,                        # 숨 용량 배율 (7.6 게이트 판정에 포함)
    steady_breath=0.5,                     # 숨 고르기 시간 배율
    thrifty_breath=0.7,                    # 숨 고르기 비용 배율
    wind_step=0.7,                         # 대시 쿨 배율
    long_dash=1.5,                         # 대시 거리 배율
    dash_strike=dict(window=0.5, mult=2.0),
    mirror_crystal=2.0,                    # 반사 피해 배율
    counter_wave=dict(damage=10, speed=700, size=(120, 40)),
    sharp_counter=0.05,                    # 패링 판정 +s
    stone_skin=0.4,                        # 피격 무적 +s
    thorn_shell=dict(damage=15, radius=100),
    first_breath=2.0,                      # 질식 간격 배율
    breath_echo=2.0,                       # '되받은 숨': 패링 숨 배율
)
# third_strike → THIRD_STRIKE, quick_hands → ATTACK_COOLDOWN_QUICK, long_handle → ATTACK_RANGE_LONG,
# ore_magnet → ORE_MAGNET_RADIUS, parry_breath → BREATH_PER_PARRY, compass → 수치 없음
COLOR_COUNTER_WAVE = (150, 230, 255)       # 「반격 파동」 (v2 검기 색)
THORN_STREAK = dict(count=10, length=(60, 100), life=0.2, width=3, color=(190, 170, 120))   # 「가시 갑각」

# 각인 화면 (T44, engrave_mode). 왼쪽 = 곡괭이·룬과 홈, 오른쪽 = 보유 각인. 좌표는 화면 px
ENGRAVE_UI = dict(
    title_y=680, top=620, left_x=40, row_h=62, name_w=160, slot_w=148, slot_h=40, slot_gap=8, slot_pad=6,
    right_x=840, right_w=400, list_row_h=32, list_rows=13, desc_y=150, help_y=30, border=3,
)
COLOR_ENGRAVE_PANEL = (30, 30, 42)
ENGRAVE_DIM_ALPHA = 230     # 0~255, 각인 화면·인벤토리 뒤 화면을 어둡게 (HUD가 비치지 않게)
COLOR_ENGRAVE_SLOT = (55, 55, 70)
COLOR_ENGRAVE_SET = (140, 180, 220)      # 다른 홈에 끼워진 각인 표시
COLOR_ENGRAVE_LOCKED = (110, 110, 125)
# 인벤토리 (T44, inventory_mode, I). 왼쪽 = 룬·장비·수집품, 오른쪽 = 보유 각인
INVENTORY_UI = dict(title_y=680, top=620, left_x=60, right_x=640, set_x=260, line_h=30, list_rows=12, desc_y=150, help_y=30)

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
WALL_DEBRIS = dict(count=20, speed=(100, 380), life=0.5, size=8)    # 벽·덩어리가 부서질 때. 색은 벽 색
ORE_SPARK = dict(count=6, speed=(120, 300), life=0.4, size=5)       # 광석 덩어리를 칠 때. 색은 COLOR_ORE
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
# ===== 적 (T42, 10.2. 피해는 칸 단위, hp는 적 체력 단위, ore = 처치 시 광석) =====
# 앞줄은 4장 값 그대로, 둘째 줄부터는 v2에서 이어받은 행동·그림 값. 색은 구역 색(REGIONS)에 맞춘다
# 갱도 벌레: 바닥을 일정 속도로 기어 다니다 앞이 벽이거나 발판 끝이면 돌아선다. 공격 없음 (접촉만)
CRAWLER = dict(hp=8, speed=60, damage=1, ore=2,
               w=46, h=22, color=(150, 130, 105), detect_range=0, attack_range=0, attack_cooldown=0,
               edge_probe=4)   # px, 발 앞 이만큼 아래에 바닥이 없으면 발판 끝
# 동굴 박쥐 (← v2 플라잉 몹): 플레이어 머리 위 hover_height에 떠 있다가 급강하. dive_time 동안(착지하면 즉시) 몸 전체가 공격 판정
BAT = dict(hp=10, speed=150, dive_speed=600, damage=1, telegraph=0.5, ore=3,
           w=40, h=28, color=(105, 80, 120), detect_range=800, hover_height=220,
           attack_range=60, hover_tolerance=40, ceiling_margin=40,
           windup=0.15, dive_time=0.5, recover=0.6, attack_cooldown=1.2)
# 갑각 전사 (← v2 근거리 병사): 베기 2연타. 2타째는 combo_telegraph만큼 짧게 예고한다
# 방패 돌진(빨간 예고, 패링 불가): shield_rush_chance 확률로 베기 대신 rush_time 동안 rush_speed로 앞으로 돌진
SHELL_WARRIOR = dict(hp=22, speed=180, damage=1, telegraph=0.5, shield_rush_chance=0.25, ore=6,
                     w=44, h=68, color=(95, 115, 140), detect_range=700, attack_range=80,
                     windup=0.15, active=0.1, recover=0.25, combo_telegraph=0.3, combo_recover=0.6,
                     attack_cooldown=0.8, hitbox=(70, 48),
                     rush_telegraph=0.6, rush_windup=0.2, rush_time=0.4, rush_speed=650, rush_recover=0.7,
                     rush_damage=1, rush_hitbox=(24, 64))
COLOR_SHIELD = (150, 150, 170)
# 가시꽃 (← v2 궁수): 제자리 고정. shoot_range 안이면 플레이어를 조준해 가시 (cooldown마다)
THORN_FLOWER = dict(hp=15, thorn_speed=500, damage=1, telegraph=0.6, cooldown=2.0, ore=4,
                    w=40, h=56, color=(70, 140, 90), detect_range=1280, speed=0, shoot_range=900,
                    windup=0.2, active=0.05, recover=0.4)
COLOR_THORN_BUD = (200, 90, 130)
# 투사체 (가시 등). size는 정사각 hitbox 한 변, length는 그림 길이
ARROW = dict(size=14, length=36, color=(240, 230, 200))
COLOR_REFLECTED = (120, 255, 255)  # 반사되어 플레이어 소유가 된 투사체
DISC_STEP = 3              # px, 원형 투사체를 가로 띠로 나눠 그리는 간격
# 포자 버섯·덩굴 매복충 (T47), 독 거머리·유적 골렘 (T53), 정예 (T48·T53)는 해당 작업에서

# 수정 유생 (← v2 견습 마법사): keep_distance ± distance_tolerance 유지, shoot_range 안이면 조준해 수정탄 1발 (흰색)
CRYSTAL_SPRITE = dict(hp=13, speed=120, keep_distance=450, bolt_speed=350,
                      damage=1, telegraph=0.7, cast_cooldown=2.0, ore=4,
                      w=38, h=60, color=(150, 110, 210), detect_range=1280,
                      distance_tolerance=60, shoot_range=900,
                      windup=0.2, active=0.05, recover=0.5)
# 수정 술사 (← v2 숙련 마법사): 수정탄 bolt_count발 부채꼴(사이각 bolt_spread도, 흰색) 또는
#   circle_chance 확률로 플레이어 발밑 결정 장판(빨간색, 패링 불가)
#   blink_trigger_dist 안으로 들어오면 blink_dist만큼 순간 후퇴 (예고 없음, blink_cooldown)
CRYSTAL_SAGE = dict(hp=25, speed=120, keep_distance=400, bolt_speed=450, bolt_count=3,
                    bolt_spread=15, damage=1, telegraph=0.6, cast_cooldown=2.5,
                    circle_chance=0.35, circle_radius=90, circle_delay=0.8,
                    blink_trigger_dist=150, blink_dist=250, blink_cooldown=4.0, ore=8,
                    w=42, h=66, color=(110, 70, 170), detect_range=1280,
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

# 쌍낫 사마귀 (← v2 쌍단검 병사): 빠르게 접근해 combo연속 베기 (흰색). 첫 타 예고 telegraph, 이후 각 타는 combo_interval 예고
#   패링해도 연타가 끊기지 않고 다음 타로 이어간다 (연속 패링 연습). 마지막 타를 패링하면 비틀거린다
SCYTHE_MANTIS = dict(hp=20, speed=260, damage=1, telegraph=0.35,
                     combo=3, combo_interval=0.3, ore=7,      # combo_interval >= TELEGRAPH_MIN
                     w=40, h=62, color=(70, 90, 140), detect_range=900, attack_range=70,
                     windup=0.08, active=0.08, recover=0.12, last_recover=0.7,
                     attack_cooldown=1.0, hitbox=(64, 44))
# 그림자 사냥꾼 (← v2 그림자 암살자): keep_distance ± distance_tolerance를 두고 배회. 공격 쿨타임이 끝나면
#   ① 순간이동 기습 (빨간색): 예고 → fade_time 동안 흐려짐 → 플레이어 등 뒤 offset px에 나타나 appear_windup 후 베기
#      (teleport_cooldown. 등 뒤가 벽·화면 밖이면 앞쪽에 나타난다)
#   ② stab_chance 확률로(또는 기습 쿨타임 중이면) 걸어서 접근해 정면 찌르기 (흰색)
#   흐려지는 동안 몸 알파값은 fade_alpha[0] → fade_alpha[1]
SHADOW_STALKER = dict(hp=18, speed=200, damage=1, telegraph=0.5,
                      teleport_cooldown=4.0, fade_time=0.4, stab_chance=0.5, ore=7,
                      w=38, h=64, color=(60, 55, 100), detect_range=1280, attack_range=80,
                      keep_distance=320, distance_tolerance=60, attack_cooldown=1.2,
                      stab_windup=0.2, stab_active=0.1, stab_recover=0.5, stab_hitbox=(80, 26),
                      appear_windup=0.3, slash_active=0.12, slash_recover=0.7, slash_hitbox=(80, 60),
                      offset=80, fade_alpha=(220, 0))
COLOR_DAGGER = (200, 210, 225)
# 연습 석상 (9.5): 플레이어가 near_range 안에 있으면 interval마다 흰 내려치기 (피해 0, 패링 숨 0)
#   hits_to_break번 패링하면 부서지며 광석 ore (영구). 곡괭이로 치면 회색 스파크만
TRAINING_STATUE = dict(interval=3.0, telegraph=0.5, hits_to_break=3, ore=20,   # 피해 0, 패링 숨 0
                       w=60, h=110, color=(120, 120, 125), near_range=360,
                       windup=0.15, active=0.1, recover=0.5, hitbox=(80, 90), recoil=0.4)
COLOR_STATUE_CRACK = (60, 60, 65)
STATUE_SPARK = dict(count=5, color=(150, 150, 155))   # 곡괭이로 쳤을 때 회색 스파크

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
BOSS_GREATSWORD = dict(hp=400, ore=300, damage=1, heavy_damage=2,   # 빨간(패링 불가) 패턴 = heavy_damage
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
BOSS_TWINBLADE = dict(hp=600, ore=500, damage=1, heavy_damage=2,   # 빨간(패링 불가) 패턴 = heavy_damage
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
BOSS_MAGE = dict(hp=500, ore=350, damage=1,
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

# 세이브 (T36, 13.6)
SAVE_PATH = 'save.json'
SAVE_DEBUG_PATH = 'save_debug.json'   # F3·F7을 쓴 뒤의 저장
SAVE_VERSION = 5

# 진행
DEATH_DELAY = 1.5          # s, 사망 연출 뒤 암전 → 마지막으로 앉은 안전지대에서 부활 (13.2)

# 광석 · 사망 (T38, 13.2)
ORE_PICKUP_RADIUS = 40
ORE_MAGNET_RADIUS = 200    # 각인 '광석 자석'
DEATH_ORE_LOSS = 1.0       # 임시. 사망 시 소지(미보관) 광석 손실 비율
# 바닥 광석 조각: 처치·채굴 시 1~max_value짜리 조각으로 위로 튄다 (10.1). delay 동안은 흡수되지 않아 튀는 게 보인다
# 흡수 범위 안에 들어오면 absorb_speed로 몸에 빨려 들어간다. 바닥에서는 friction(px/s^2)으로 미끄러짐이 멈춘다
ORE_PIECE = dict(max_value=5, speed=(300, 520), spread=0.6, delay=0.35, absorb_speed=900,
                 friction=1500, size=6, size_per_value=1.5)
ORE_COLLECT_SPARK = dict(count=3, speed=(60, 140), life=0.25, size=4)   # 조각이 몸에 닿을 때. 색은 COLOR_ORE
# HUD 광석 줄 (14.1 '보관 840 (+소지 120)'). 보관 연출: 소지 숫자가 보관 쪽으로 미끄러지며 보관 숫자가 올라간다
ORE_HUD_GAP = 6            # px, 숨 게이지와 광석 줄 사이
ORE_BANK_TIME = 0.6        # s, 보관 연출 길이
ORE_BANK_SLIDE = 120       # px, 소지 숫자가 왼쪽으로 미끄러지는 거리
COLOR_ORE_CARRIED = (255, 230, 170)
HUD_FONT_NARROW = 0.55    # 숫자·영문·공백 글자 폭 ÷ 글자 크기 (글자 폭 어림)

# 카드 (룬지기 강화 목록·상점·각인 화면)
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

# 보스 HUD (하단 중앙): 체력 바 + 그 아래 자세 게이지 (POSTURE_MAX칸)
BOSS_BAR_W, BOSS_BAR_H = 640, 18
BOSS_POSTURE_H = 10        # px
BOSS_POSTURE_GAP = 6       # px, 체력 바와 자세 게이지 사이 · 자세 칸 사이
BOSS_NAME_GAP = 16         # px, 체력 바 위 이름 글자 중심까지
COLOR_BOSS_HP = (200, 50, 50)
COLOR_POSTURE_BACK = (50, 50, 60)
COLOR_POSTURE_FILL = (255, 220, 120)
BOSS_NAME = dict(greatsword='대검 기사', mage='대마법사', twinblade='쌍검 기사')

# 알림 문구 (HUD 하단 중앙. '저장했습니다' 등)
HUD_MESSAGE_TIME = 1.5     # s
HUD_MESSAGE_Y = 120        # px, 화면 아래에서

# 타이틀 · 일시정지 메뉴 (T36, 13.7)
MENU_ROW_H = 44            # px
MENU_TOP_Y = 330           # px, 첫 항목의 화면 y
COLOR_MENU_SELECTED = (255, 220, 120)
CONTROLS_TEXT = [          # 조작법 화면 (config.KEYS와 맞춘다)
    '←  →   이동', 'Z   점프 (누르는 만큼 높이)', 'X   곡괭이 (↑·↓와 함께 위·아래 공격)',
    'C   대시', 'S   패링', 'A   룬 기술 / 길게: 숨 고르기', 'D   돌파',
    '↑   앉기 · 말 걸기', 'Tab   지도      I   인벤토리', 'Esc   일시정지',
]

# 대화 · 석판 · 상점 (T39, 2.5, 13.3). 흰색·빨간색은 쓰지 않는다. NPC·석판 (x, y)는 아래쪽 중심
DIALOG_CHARS_PER_SEC = 40
DIALOG_DIR = 'data/dialog'  # <대화 id>.json (NPC id·석판 id와 같은 이름), 상점 상품 이름은 items.json (ITEMS_PATH)
NPC_TALK_RADIUS = 80       # px, NPC·석판 중심과 플레이어 중심의 가로 거리가 이 안이면 ↑로 말 걸기
NPC_W, NPC_H = 40, 72      # px
COLOR_NPC = dict(borum=(150, 120, 80), borum_mine=(150, 120, 80), har=(105, 100, 95), oram=(90, 120, 160))   # NPC id별 몸 색. 없으면 COLOR_NPC_DEFAULT
COLOR_CARVER_STONE = (115, 115, 120)      # 룬지기 오람의 돌이 된 아래 절반
COLOR_NPC_DEFAULT = (120, 120, 100)
COLOR_NPC_LAMP = (255, 220, 120)         # 헬멧 랜턴 (플레이어와 같은 광부 표시)
NPC_LAMP = 8               # px
TABLET_W, TABLET_H = 56, 80
COLOR_TABLET = (100, 100, 110)
COLOR_TABLET_RUNE = (140, 180, 220)
COLOR_TALK_PROMPT = (255, 220, 120)
TALK_PROMPT_SIZE = 14      # px, 머리 위 ↑ 표시
TALK_PROMPT_GAP = 16       # px
DIALOG_BOX = dict(w=1000, h=170, bottom=30, pad=24, line_h=36, border=4)   # 화면 하단 대화 상자
COLOR_DIALOG_BOX = (25, 25, 35)
COLOR_DIALOG_BORDER = (90, 90, 110)
COLOR_DIALOG_NAME = (255, 220, 120)
DIALOG_NEXT_BLINK = 0.5    # s, 페이지 끝 ▼ 깜빡임 주기
SHOP_VISIBLE = 3           # 상점 상품 카드를 한 번에 보이는 수 (←→로 넘김). 카드 모양은 CARD_*
SHOP_CARD_H = 200          # px
SHOP_TOP_Y = 560           # px, 카드 윗변의 화면 y
SHOP = dict(               # 보름 상점: (가격, 판매 조건). 조건 'region_<구역>' = 그 구역 방문, 'miners_<n>' = 실종 광부 n명 구출
    compass=(120, None), ore_magnet=(150, None), deep_lung=(400, 'region_moss'),
    long_handle=(450, 'miners_2'), rare_ore_a=(600, None), rare_ore_b=(1200, 'miners_6'),
)
SHOP_RARE_ORE = 1          # 각인이 아닌 상품(rare_ore_*) 하나에 든 희귀 광석 수
# 대장간 하르 (T62, 13.3). (보관 광석, 희귀 광석). 인덱스 0 = Lv1→2. 목록은 상점과 같은 카드 화면 (data/dialog/har.json의 forge)
FORGE_PICKAXE_COST = [(250, 1), (800, 1), (2000, 1), (4000, 1)]  # 임시. Lv2~5 (강화는 T64)
FORGE_PICKAXE_UNLOCK_FLAG = 'whetstone'  # B3 처치 보상 '수정 숫돌'. 없으면 곡괭이 강화 목록 숨김
FORGE_ARMOR_COST = [(300, 1), (900, 1), (1800, 2), (3000, 2)]    # 임시. 체력 6~9칸 (Lv n = HP_START + n - 1칸)

# 지도 (T40, 13.4). Tab을 누르고 있는 동안. 지금 있는 구역만 그린다. 방 1화면 = MAP_CELL_W × MAP_CELL_H px
MAP_CELL_W, MAP_CELL_H = 96, 54
MAP_ROOM_BORDER = 3        # px, 방 테두리
MAP_EXIT_GAP_MIN = 10      # px, 출구 틈 최소 길이 (출구 길이를 줄인 값이 이보다 짧으면)
MAP_SCROLL_SPEED = 600     # px/s, ←→↑↓ 스크롤
MAP_DIM_ALPHA = 245       # 0~255, 지도 뒤 화면을 어둡게
MAP_FILL_DIM = 0.35        # 방문한 방 안쪽 칠 = 구역 색 × 이 값
MAP_SAFE_RADIUS = 9        # px, 안전지대 (큰 원)
MAP_VENT_RADIUS = 4        # px, 숨구멍 (작은 원)
MAP_DOT_GAP = 10           # px, 숨 소모가 큰 곳의 점 무늬 간격
MAP_DOT = 2                # px
MAP_HATCH_GAP = 10         # px, 숨 게이트 방 빗금 간격
MAP_ICON = 12              # px, 보름 캠프·대장간·새김터 사각 아이콘 한 변
MAP_PLAYER_RADIUS = 6      # px, 현재 위치 (각인 '광부의 나침반' 장착 시)
MAP_PLAYER_BLINK = 0.4     # s
MAP_TOP_PAD = 50           # px, 화면 위 구역 이름 줄
MAP_DISC_STEP = 2          # px, 지도 원을 쌓는 가로 띠 두께
MAP_NPC_ICON = dict(borum='camp', har='forge')   # NPC id → 지도 아이콘 (13.4)
COLOR_MAP_BG = (10, 10, 16)
COLOR_MAP_UNVISITED = (110, 110, 120)  # 지도석으로만 아는 방 (회색 윤곽)
COLOR_MAP_SAFE = (70, 150, 90)         # 안전지대 = COLOR_SAFE_ZONE
COLOR_MAP_VENT = (120, 200, 240)       # 숨구멍 = COLOR_AIR_VENT
COLOR_MAP_HATCH = (150, 150, 190)      # 숨 게이트 빗금·요구 레벨 숫자
COLOR_MAP_ICON = dict(camp=(220, 170, 90), forge=(200, 120, 70), carver=(140, 180, 220),
                      boss=(200, 70, 160), boss_done=(110, 80, 100), shortcut=(130, 220, 120))
COLOR_MAP_PLAYER = (255, 220, 120)

# 결과 화면
COLOR_RESULT_DEAD = (239, 68, 68)
COLOR_RESULT_CLEAR = (255, 220, 120)

# 사운드 (assets/sounds/, 없거나 오디오 장치가 없으면 소리 없이 진행)
# 효과음 파일은 tools/gen_sounds.py로 합성. 볼륨은 0~128
SOUND_DIR = 'assets/sounds'
SOUND_VOLUME = dict(
    parry=110, parry_miss=60, swing=45, hit=100, enemy_hurt=60, kill=80,
    telegraph_white=55, telegraph_red=70, groggy=110, phase2=110,
    dash=55, jump=35, shoot=55, door=70, death=100, cursor=50, select=60, chest=80, ore=40, bank=80)
SOUND_MIN_INTERVAL = 0.03  # s, 같은 소리가 한 프레임에 겹쳐 커지는 것 방지
# 배경음 (파일을 넣으면 재생, 없으면 생략). ogg/mp3/wav
MUSIC_FILES = dict(battle='bgm_battle.ogg', boss='bgm_boss.ogg')
MUSIC_VOLUME = 48
