import json
import os

from pico2d import *

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import camera, sound, world
from ui import font

# 룬 획득·강화 연출 (8.5). play_mode(또는 carver_mode) 위에 push된다 (월드·숨 정지)
# 획득: 히트스톱 → 화면이 어두워짐 → 룬 문양이 플레이어에게 흡수 → 섬광(구역색) → 설명 카드. 강화는 RUNE_GET.short에 몰아서
# 카드: 룬 이름·레벨, 키 아이콘, 그 레벨의 한 줄 설명, 열리는 곳 힌트, (처음 몇 번만) 룬지기 안내. X: 확인
# 문구는 data/dialog/runes.json. 반사 해금(T48, 'reflect' = 갑각 방패 조각 문양)·수정 숫돌(T52)도 이 모드를 쓴다

RUNES_PATH = os.path.join(os.path.dirname(__file__), '..', config.DIALOG_DIR, 'runes.json')
CONFIRM_KEYS = (SDLK_x, SDLK_RETURN, SDLK_SPACE)

rune = None        # 룬 id
level = 1          # 이 연출이 보여 주는 레벨 (획득 = 1, 강화 = 새 레벨)
short = False      # 강화 (짧은 연출)
from_carver = False  # 룬지기에게 받음 (카드의 '룬지기에게 가면' 줄을 빼려고)
then = None        # 확인으로 닫은 뒤 부를 함수 (룬지기 대화 이어가기 등)
timer = 0.0
texts = {}


def start(rune_id, lv, is_short=False, carver=False, after=None):
    # 부른 쪽이 push_mode·change_mode 직전에 부른다. 룬 지급·저장은 부른 쪽 (runes.grant, play_mode.save_game)
    global rune, level, short, from_carver, then
    rune, level, short, from_carver, then = rune_id, lv, is_short, carver, after


def init():
    global timer, texts
    timer = 0.0
    with open(RUNES_PATH, encoding='utf-8') as f:
        texts = json.load(f)
    sound.play('select')


def finish():
    global then
    then = None


def times():
    # (멈춤, 어두워짐, 흡수, 섬광) 구간 길이. 강화는 짧은 연출 하나에 흡수·섬광만
    g = config.RUNE_GET
    if short:
        return 0.0, 0.0, g['short'] * g['absorb'] / (g['absorb'] + g['flash']), g['short'] * g['flash'] / (g['absorb'] + g['flash'])
    return g['hitstop'], g['dim'], g['absorb'], g['flash']


def card_shown():
    return timer >= sum(times())


def handle_events():
    global then
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key in CONFIRM_KEYS and card_shown():
            after = then
            then = None
            sound.play('cursor')
            game_framework.pop_mode()
            if after:
                after()
            return


def update():
    global timer
    before = card_shown()
    timer += game_framework.frame_time
    if card_shown() and not before:
        sound.play('chest')


# ---------- 그리기 ----------

def phase():
    # 반환: (구간 이름, 0~1 진행도)
    t = timer
    for name, length in zip(('stop', 'dim', 'absorb', 'flash'), times()):
        if t < length:
            return name, t / length
        t -= length
    return 'card', 1.0


def region_color():
    region = config.REGIONS.get(play_mode.room.region)
    return region['color'] if region else config.COLOR_RUNE_GLYPH


def draw_glyph(progress):
    # 룬 문양 (월드 좌표): 플레이어 머리 위에서 내려와 몸 가운데로 줄어들며 흡수된다
    g = config.RUNE_GET
    player = play_mode.player
    cx = player.x
    body = player.y + config.PLAYER_H / 2
    cy = body + g['glyph_rise'] * (1 - progress)
    half = g['glyph_size'] / 2 * (1 - progress * 0.8)
    color = config.COLOR_RUNE_GLYPH
    bar = max(2, half / 6)
    if rune == 'reflect':
        draw_shield_shard(cx, cy, half, bar, color)
        return
    if rune == config.FORGE_PICKAXE_UNLOCK_FLAG:
        draw_whetstone(cx, cy, half, bar)
        return
    if rune in config.BOSS_CORE_CARD.values():
        # 봉인 핵 (B4 신전 핵): 룬 빛 원판 + 테두리
        effect.draw_ring(cx, cy, half, half, 16, bar * 1.5, color)
        effect.draw_disc(cx, cy, half * 0.55, config.COLOR_COLOSSUS_CORE)
        return
    effect.draw_ring(cx, cy, half, half, 16, bar * 1.5, color)
    camera.draw_rect(cx - bar / 2, cy - half * 0.7, cx + bar / 2, cy + half * 0.7, *color, filled=True)
    camera.draw_rect(cx - half * 0.5, cy + half * 0.2 - bar / 2, cx + half * 0.5, cy + half * 0.2 + bar / 2, *color, filled=True)
    camera.draw_rect(cx - half * 0.35, cy - half * 0.3 - bar / 2, cx + half * 0.35, cy - half * 0.3 + bar / 2, *color, filled=True)


def draw_shield_shard(cx, cy, half, bar, color):
    # 반사 해금: 갑각 방패 조각 (위가 넓고 아래로 좁아지는 판 + 가운데 금)
    rows = max(1, int(half * 2 / bar))
    for i in range(rows):
        y = cy - half + i * bar
        w = half * (0.35 + 0.65 * i / rows)
        camera.draw_rect(cx - w, y, cx + w, y + bar, *color, filled=True)
    camera.draw_rect(cx - bar / 4, cy - half * 0.6, cx + bar / 4, cy + half * 0.9, *config.COLOR_CARD, filled=True)


def draw_whetstone(cx, cy, half, bar):
    # 수정 숫돌 (11.4 B3): 납작하고 긴 돌 + 비스듬한 결정 결
    camera.draw_rect(cx - half, cy - half * 0.35, cx + half, cy + half * 0.35, *config.COLOR_ARCHSAGE_ARMOR, filled=True)
    steps = 4
    for i in range(steps):
        x = cx - half * 0.6 + half * 1.2 * i / (steps - 1)
        camera.draw_rect(x - bar / 2, cy - half * 0.25 + i * bar / 2, x + bar / 2, cy + half * 0.25 + i * bar / 2,
                         *config.COLOR_RUNE_GLYPH, filled=True)


def rune_text(key, default=''):
    info = texts.get(rune, {})
    return font.text(info.get(key, default), info.get(f'{key}_en', info.get(key, default)))


def card_lines():
    # 그 레벨 설명 (숨의 룬은 {cap} = 그 레벨 기본 숨 용량, 수정 숫돌은 {cores}/{need} = 봉인 핵 수)
    levels = rune_text('levels', [])
    lines = levels[level - 1] if 0 < level <= len(levels) else []
    cap = config.BREATH_CAPACITY[level] if rune == 'breath' else 0
    cores = len(world.state.cores)
    return [line.format(cap=cap, cores=cores, need=config.SEAL_CORES_REQUIRED) for line in lines]


def draw_card():
    c = config.RUNE_CARD
    text_font, small_font = font.get(config.FONT_SIZE_TEXT), font.get(config.FONT_SIZE_SMALL)
    l = (config.SCREEN_W - c['w']) / 2
    b = (config.SCREEN_H - c['h']) / 2
    r, t = l + c['w'], b + c['h']
    edge = config.CARD_BORDER
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *config.COLOR_RUNE_GLYPH, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_CARD, filled=True)
    draw_rectangle(l, t - config.CARD_STRIPE_H, r, t, *region_color(), filled=True)
    if not text_font:
        return
    pad, line_h = c['pad'], c['line_h']
    y = t - config.CARD_STRIPE_H - pad - config.FONT_SIZE_TEXT / 2
    # 룬이 아닌 해금(반사)은 레벨을 쓰지 않는다
    title = rune_text('name', rune) if rune not in config.RUNE_MAX_LEVEL else f"{rune_text('name', rune)}  Lv{level}"
    text_font.draw(l + pad, y, title, config.COLOR_RUNE_GLYPH)
    # 키 아이콘: 오른쪽 위 작은 사각 안에 키 이름
    key = texts.get(rune, {}).get('key', '')
    if key:
        size = config.FONT_SIZE_TEXT + 12
        kl, kb = r - pad - size, y - size / 2
        draw_rectangle(kl, kb, kl + size, kb + size, *config.COLOR_CARD_BORDER, filled=True)
        text_font.draw(kl + size / 2 - config.FONT_SIZE_TEXT * config.HUD_FONT_NARROW / 2 * len(key), y, key,
                       config.COLOR_TEXT)
    y -= line_h * 1.4
    for line in card_lines():
        text_font.draw(l + pad, y, line, config.COLOR_TEXT)
        y -= line_h
    if not short:
        small_font.draw(l + pad, y, rune_text('hint'), config.COLOR_TEXT_DIM)
        y -= line_h
        if not from_carver and len(world.state.player.runes) <= config.RUNE_HINT_MAX_RUNES:
            line = font.text(texts.get('carver_line', ''), texts.get('carver_line_en', ''))
            small_font.draw(l + pad, y, line, config.COLOR_TEXT_DIM)
    small_font.draw(r - pad - config.FONT_SIZE_SMALL * 4, b + pad, font.text('X: 확인', 'X: OK'), config.COLOR_TEXT_DIM)


def draw():
    play_mode.draw_scene()
    g = config.RUNE_GET
    name, progress = phase()
    dim = {'stop': 0.0, 'dim': progress}.get(name, 1.0)
    if short:
        dim = 1.0
    effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, g['dim_alpha'] * dim)
    if name == 'absorb':
        draw_glyph(progress)   # 카메라 오프셋은 draw_scene에서 정해진 그대로
    elif name == 'flash':
        effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, region_color(),
                                      g['flash_alpha'] * (1 - progress))
    elif name == 'card':
        draw_card()
    update_canvas()


def pause():
    pass


def resume():
    pass
