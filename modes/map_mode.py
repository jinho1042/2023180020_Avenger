import math

import pico2d
import pico2d.pico2d as canvas  # open_canvas 이후 renderer가 여기 생긴다
from pico2d import *
from sdl2 import SDL_BLENDMODE_BLEND, SDL_RenderDrawLine, SDL_SetRenderDrawBlendMode, SDL_SetRenderDrawColor

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import breath, engravings, world
from ui import font

# 지도 (13.4). play_mode가 Tab을 누를 때 push하고, Tab을 떼면 pop한다 (월드·숨 정지)
# 지금 있는 구역만 그린다: 방문한 방 + 지도석을 얻었으면 미방문 방(회색 윤곽). 방 = map_cell·size 사각형, 출구 = 테두리 틈
# 숨 정보: 안전지대(큰 원), 숨구멍(작은 원), 숨 소모가 큰 곳(점 무늬), 숨 게이트 방(빗금 + 요구 레벨)
# 아이콘: 보름 캠프·대장간, 새김터(met_oram 뒤, 그 전에는 보름 힌트 뒤 한 번 더 기절하면 물음표), 보스(처치 전·후 색), 연 허브행 숏컷(허브 쪽 화살표),
# 현재 위치('광부의 나침반' 장착 시에만). ←→↑↓로 스크롤

MAP_KEY = getattr(pico2d, config.KEYS['map'])
SCROLL_KEYS = {SDLK_LEFT: (1, 0), SDLK_RIGHT: (-1, 0), SDLK_UP: (0, -1), SDLK_DOWN: (0, 1)}
# 한쪽 문이 열리는 쪽(먼 쪽) → 허브로 가는 방향 화살표
SHORTCUT_ARROW = dict(left='▶', right='◀', up='▼', down='▲')

region = None      # 지금 구역 이름 (REGIONS에 없으면 지도 없음)
rooms = []         # [(Room, 방문 여부)]
origin_x = origin_y = 0.0   # 지도 격자 (0, 0)의 화면 좌표. 스크롤하면 바뀐다
scroll = set()     # 누르고 있는 스크롤 키
blink = 0.0


def init():
    global region, rooms, origin_x, origin_y, blink
    scroll.clear()
    blink = 0.0
    region = world.room_region(play_mode.room.id)
    rooms = world.map_rooms(region) if region in config.REGIONS else []
    # 처음에는 지금 방이 화면 가운데
    here = play_mode.room
    cx = (here.map_cell[0] + here.size[0] / 2) * config.MAP_CELL_W
    cy = (here.map_cell[1] + here.size[1] / 2) * config.MAP_CELL_H
    origin_x, origin_y = config.SCREEN_W / 2 - cx, config.SCREEN_H / 2 - cy


def finish():
    global rooms
    rooms = []
    scroll.clear()


def handle_events():
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYUP and e.key == MAP_KEY:
            game_framework.pop_mode()
            return
        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            game_framework.pop_mode()
            return
        elif e.type == SDL_KEYDOWN and e.key in SCROLL_KEYS:
            scroll.add(e.key)
        elif e.type == SDL_KEYUP and e.key in SCROLL_KEYS:
            scroll.discard(e.key)


def update():
    global origin_x, origin_y, blink
    dt = game_framework.frame_time
    blink += dt
    step = config.MAP_SCROLL_SPEED * dt
    for key in scroll:
        dx, dy = SCROLL_KEYS[key]
        origin_x += dx * step
        origin_y += dy * step


# ---------- 그리기 (화면 좌표) ----------

def room_rect(room):
    l = origin_x + room.map_cell[0] * config.MAP_CELL_W
    b = origin_y + room.map_cell[1] * config.MAP_CELL_H
    return l, b, l + room.size[0] * config.MAP_CELL_W, b + room.size[1] * config.MAP_CELL_H


def to_map(room, x, y):
    # 방 안 월드 좌표 → 지도 화면 좌표
    l, b, _, _ = room_rect(room)
    return l + x * config.MAP_CELL_W / config.SCREEN_W, b + y * config.MAP_CELL_H / config.SCREEN_H


def area_rect(room, x, y, w, h):
    l, b = to_map(room, x, y)
    r, t = to_map(room, x + w, y + h)
    return l, b, r, t


def draw_line(x1, y1, x2, y2, color):
    # pico2d에는 선 그리기가 없어 SDL을 직접 부른다 (effect.draw_alpha_line의 화면 좌표·1px판)
    SDL_SetRenderDrawBlendMode(canvas.renderer, SDL_BLENDMODE_BLEND)
    SDL_SetRenderDrawColor(canvas.renderer, *color, 255)
    top = config.SCREEN_H - 1   # pico2d는 y가 위로, SDL은 아래로 증가
    SDL_RenderDrawLine(canvas.renderer, int(x1), int(top - y1), int(x2), int(top - y2))


def draw_disc(x, y, radius, color):
    # 가로 띠를 쌓아 채운 원 (effect.draw_disc의 화면 좌표판)
    step = config.MAP_DISC_STEP
    rows = max(1, int(radius * 2 / step))
    for i in range(rows):
        dy = -radius + (i + 0.5) * radius * 2 / rows
        half = math.sqrt(max(0, radius * radius - dy * dy))
        draw_rectangle(x - half, y + dy - step / 2, x + half, y + dy + step / 2, *color, filled=True)


def draw_square(x, y, size, color):
    draw_rectangle(x - size / 2, y - size / 2, x + size / 2, y + size / 2, *color, filled=True)


def draw_dots(l, b, r, t, color):
    # 숨 소모가 큰 곳 점 무늬
    gap, half = config.MAP_DOT_GAP, config.MAP_DOT / 2
    y = b + gap / 2
    while y < t:
        x = l + gap / 2
        while x < r:
            draw_rectangle(x - half, y - half, x + half, y + half, *color, filled=True)
            x += gap
        y += gap


def draw_hatch(l, b, r, t, color):
    # 숨 게이트 빗금: x + y = c 인 대각선을 사각형 안으로 자른다
    c = l + b + config.MAP_HATCH_GAP
    while c < r + t:
        x1, x2 = max(l, c - t), min(r, c - b)
        draw_line(x1, c - x1, x2, c - x2, color)
        c += config.MAP_HATCH_GAP


def heavy_air(name):
    return name is not None and config.BREATH_DRAIN_MULT[name] > config.BREATH_DRAIN_MULT['normal']


def draw_room(room, visited):
    l, b, r, t = room_rect(room)
    edge = config.MAP_ROOM_BORDER
    region_color = config.REGIONS[region]['color']
    if visited:
        border, fill = region_color, tuple(int(c * config.MAP_FILL_DIM) for c in region_color)
    else:
        border, fill = config.COLOR_MAP_UNVISITED, config.COLOR_MAP_BG
    draw_rectangle(l, b, r, t, *border, filled=True)
    draw_rectangle(l + edge, b + edge, r - edge, t - edge, *fill, filled=True)
    # 숨 소모가 큰 방은 전체, 아니면 배율 영역·물만 점 무늬
    base = breath.base_air(room)
    if heavy_air(base):
        draw_dots(l + edge, b + edge, r - edge, t - edge, config.COLOR_BREATH_ZONE[base])
    for x, y, w, h, name in [z[:5] for z in room.breath_zones] + [tuple(w[:4]) + ('water',) for w in room.water]:
        if heavy_air(name):
            draw_dots(*area_rect(room, x, y, w, h), config.COLOR_BREATH_ZONE[name])
    for x, y, w, h, _, need_lv in room.breath_gates:
        gl, gb, gr, gt = area_rect(room, x, y, w, h)
        draw_hatch(max(gl, l + edge), max(gb, b + edge), min(gr, r - edge), min(gt, t - edge), config.COLOR_MAP_HATCH)
        draw_need_level((gl + gr) / 2, (gb + gt) / 2, need_lv)
    for exit_zone in room.exits:
        draw_exit_gap(room, exit_zone, fill)


def draw_need_level(x, y, need_lv):
    text_font = font.get(config.FONT_SIZE_TEXT)
    if not text_font:
        return
    label = f'Lv{need_lv}'
    w = len(label) * config.FONT_SIZE_TEXT * config.HUD_FONT_NARROW
    draw_rectangle(x - w / 2 - 4, y - config.FONT_SIZE_TEXT / 2, x + w / 2 + 4, y + config.FONT_SIZE_TEXT / 2,
                   *config.COLOR_MAP_BG, filled=True)
    text_font.draw(x - w / 2, y, label, config.COLOR_MAP_HATCH)


def draw_exit_gap(room, exit_zone, fill):
    # 출구 자리 테두리를 안쪽 색으로 덮어 틈을 낸다
    l, b, r, t = room_rect(room)
    edge = config.MAP_ROOM_BORDER
    el, eb, er, et = area_rect(room, exit_zone.x, exit_zone.y, exit_zone.w, exit_zone.h)
    half = config.MAP_EXIT_GAP_MIN / 2
    if exit_zone.side in ('left', 'right'):
        cy = (eb + et) / 2
        eb, et = min(eb, cy - half), max(et, cy + half)
        x = l if exit_zone.side == 'left' else r - edge
        draw_rectangle(x, max(eb, b + edge), x + edge, min(et, t - edge), *fill, filled=True)
    else:
        cx = (el + er) / 2
        el, er = min(el, cx - half), max(er, cx + half)
        y = b if exit_zone.side == 'down' else t - edge
        draw_rectangle(max(el, l + edge), y, min(er, r - edge), y + edge, *fill, filled=True)


def draw_icons(room):
    state = world.state
    for x, y, w, h, _ in room.safe_zones:
        draw_disc(*to_map(room, x + w / 2, y + h / 2), config.MAP_SAFE_RADIUS, config.COLOR_MAP_SAFE)
    for x, y, _ in room.air_vents:
        draw_disc(*to_map(room, x, y), config.MAP_VENT_RADIUS, config.COLOR_MAP_VENT)
    text_font = font.get(config.FONT_SIZE_SMALL)
    for obj in room.objects:
        icon = None
        if obj[0] == 'npc':
            icon = config.MAP_NPC_ICON.get(obj[3])
        elif obj[0] == 'carver' and 'met_oram' in state.flags:
            icon = 'carver'   # 새김터는 찾은 뒤 영구 표시 (8.3)
        elif obj[0] == 'carver' and state.hint_fail_count > config.HINT_FAIL_COUNT and text_font:
            # 보름 힌트 뒤 한 번 더 기절하면 새김터 자리에 물음표 (7.5)
            mx, my = to_map(room, obj[1], obj[2])
            text_font.draw(mx - config.FONT_SIZE_SMALL / 2, my, '?', config.COLOR_MAP_QUESTION)
        if icon:
            draw_square(*to_map(room, obj[1], obj[2]), config.MAP_ICON, config.COLOR_MAP_ICON[icon])
    if room.boss:
        l, b, r, t = room_rect(room)
        done = room.boss in state.bosses_defeated
        draw_square((l + r) / 2, (b + t) / 2, config.MAP_ICON * 1.5,
                    config.COLOR_MAP_ICON['boss_done' if done else 'boss'])
    for x, y, w, h, kind, gid, attrs in room.gates:
        # 허브행 숏컷은 연 뒤에만 화살표 (13.4)
        if kind == 'one_way' and attrs.get('to_hub') and f'{room.id}:{gid}' in state.opened and text_font:
            mx, my = to_map(room, x + w / 2, y + h / 2)
            arrow = SHORTCUT_ARROW.get(attrs.get('open_from'), '◆')
            text_font.draw(mx - config.FONT_SIZE_SMALL / 2, my, arrow, config.COLOR_MAP_ICON['shortcut'])


def draw_player():
    # 현재 위치는 '광부의 나침반'(compass)을 장착했을 때만 (13.4, 8.4)
    if not engravings.is_set('compass'):
        return
    if math.fmod(blink, config.MAP_PLAYER_BLINK * 2) >= config.MAP_PLAYER_BLINK:
        return
    player = play_mode.player
    draw_disc(*to_map(play_mode.room, player.x, player.y + config.PLAYER_H / 2),
              config.MAP_PLAYER_RADIUS, config.COLOR_MAP_PLAYER)


def small_width(text):
    size = config.FONT_SIZE_SMALL
    return sum(size if ord(c) >= 0x1100 else size * config.HUD_FONT_NARROW for c in text)


def draw_legend():
    small_font = font.get(config.FONT_SIZE_SMALL)
    if not small_font:
        return
    items = [(config.COLOR_MAP_SAFE, font.text('안전지대', 'Safe zone')),
             (config.COLOR_MAP_VENT, font.text('숨구멍', 'Air vent')),
             (config.COLOR_MAP_HATCH, font.text('숨 게이트', 'Breath gate')),
             (config.COLOR_MAP_ICON['camp'], font.text('보름 캠프', 'Camp')),
             (config.COLOR_MAP_ICON['forge'], font.text('대장간', 'Forge')),
             (config.COLOR_MAP_ICON['carver'], font.text('새김터', 'Carver')),
             (config.COLOR_MAP_ICON['boss'], font.text('보스', 'Boss'))]
    x, y = config.HUD_MARGIN, config.HUD_MARGIN + config.FONT_SIZE_SMALL / 2
    for color, label in items:
        draw_square(x + config.MAP_ICON / 2, y, config.MAP_ICON, color)
        x += config.MAP_ICON + config.FONT_SIZE_SMALL / 2
        small_font.draw(x, y, label, config.COLOR_TEXT_DIM)
        x += small_width(label) + config.FONT_SIZE_SMALL
    help_text = font.text('←→↑↓ 이동   Tab 떼면 닫기', '←→↑↓ Scroll   Release Tab to close')
    small_font.draw(config.SCREEN_W - config.HUD_MARGIN - small_width(help_text), y, help_text,
                    config.COLOR_TEXT_DIM)


def draw_title():
    text_font = font.get(config.FONT_SIZE_TEXT)
    if not text_font:
        return
    if region in config.REGIONS:
        title = config.REGIONS[region]['name'] if font.has_korean() else region
    else:
        title = font.text('이곳은 지도에 없습니다', 'No map here')
    text_font.draw(config.HUD_MARGIN, config.SCREEN_H - config.MAP_TOP_PAD / 2, title, config.COLOR_TEXT)


def draw():
    play_mode.draw_scene()
    effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_MAP_BG, config.MAP_DIM_ALPHA)
    for room, visited in rooms:
        draw_room(room, visited)
    for room, _ in rooms:
        draw_icons(room)
    if rooms:
        draw_player()
    draw_title()
    draw_legend()
    update_canvas()


def pause():
    pass


def resume():
    pass
