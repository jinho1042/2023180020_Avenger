import pico2d
from pico2d import *

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import economy, engravings, runes, sound, world
from ui import font

# 인벤토리 (I, 6.1): 룬·장비·수집품과 보유 각인을 본다 (바꾸기는 안전지대 각인 화면). 월드·숨 정지
# ↑↓ 각인 선택 (아래에 설명), I·Z·Esc 닫기

CLOSE_KEYS = (getattr(pico2d, config.KEYS['inventory']), SDLK_ESCAPE, SDLK_z)

owned = []         # 보유 각인 (8.4 표 순서)
pick = 0
list_top = 0


def init():
    global owned, pick, list_top
    have = engravings.player_state().engravings_owned
    owned = [eid for eid in engravings.IDS if eid in have]
    pick, list_top = 0, 0
    sound.play('select')


def finish():
    pass


def handle_events():
    global pick, list_top
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif e.key in CLOSE_KEYS:
            game_framework.pop_mode()
            return
        elif e.key in (SDLK_UP, SDLK_DOWN) and owned:
            pick = (pick + (-1 if e.key == SDLK_UP else 1)) % len(owned)
            rows = config.INVENTORY_UI['list_rows']
            list_top = min(max(list_top, pick - rows + 1), pick)
            sound.play('cursor')


def update():
    pass


# ---------- 그리기 ----------

def status_lines():
    # 왼쪽 줄: (글, 색). 룬은 가진 것만
    state = world.state
    p = state.player
    lines = [(font.text('룬', 'Runes'), config.COLOR_DIALOG_NAME)]
    have_runes = [r for r in config.RUNE_ORDER if runes.rune_lv(state, r) >= 1]
    for r in have_runes:
        lines.append((f'  {engravings.target_name(r)}  Lv{p.runes[r]} / {config.RUNE_MAX_LEVEL[r]}', config.COLOR_RUNE_GLYPH))
    if not have_runes:
        lines.append((font.text('  아직 없다', '  None yet'), config.COLOR_TEXT_DIM))
    if config.REFLECT_UNLOCK_FLAG in state.flags:
        lines.append((font.text('  반사 (반격의 시련)', '  Reflect'), config.COLOR_RUNE_GLYPH))
    lines.append((font.text('장비', 'Gear'), config.COLOR_DIALOG_NAME))
    lines.append((font.text(f'  곡괭이 Lv{p.pickaxe_level}', f'  Pickaxe Lv{p.pickaxe_level}'), config.COLOR_TEXT))
    lines.append((font.text(f'  갑옷 Lv{p.armor_level} (체력 {p.hp_max}칸)', f'  Armor Lv{p.armor_level} ({p.hp_max} HP)'),
                  config.COLOR_TEXT))
    lines.append((font.text('수집품', 'Collection'), config.COLOR_DIALOG_NAME))
    lines.append((font.text(f'  보관 광석 {economy.banked()}', f'  Stored ore {economy.banked()}'), config.COLOR_ORE))
    lines.append((font.text(f'  희귀 광석 {economy.rare()}', f'  Rare ore {economy.rare()}'), config.COLOR_ORE))
    lines.append((font.text(f'  지도석 {len(state.map_stones)}', f'  Map stones {len(state.map_stones)}'), config.COLOR_TEXT))
    lines.append((font.text(f'  봉인 핵 {len(state.cores)}', f'  Seal cores {len(state.cores)}'), config.COLOR_TEXT))
    lines.append((font.text(f'  구한 광부 {len(state.miners_rescued)}', f'  Miners rescued {len(state.miners_rescued)}'),
                  config.COLOR_TEXT))
    return lines


def draw_status(small_font):
    ui = config.INVENTORY_UI
    for k, (line, color) in enumerate(status_lines()):
        small_font.draw(ui['left_x'], ui['top'] - k * ui['line_h'], line, color)


def draw_engravings(text_font, small_font):
    ui = config.INVENTORY_UI
    text_font.draw(ui['right_x'], ui['top'], font.text('각인', 'Engravings'), config.COLOR_DIALOG_NAME)
    if not owned:
        small_font.draw(ui['right_x'], ui['top'] - ui['line_h'], font.text('가진 각인이 없다', 'No engravings'),
                        config.COLOR_TEXT_DIM)
        return
    for k, eid in enumerate(owned[list_top:list_top + ui['list_rows']]):
        y = ui['top'] - (k + 1) * ui['line_h']
        selected = list_top + k == pick
        small_font.draw(ui['right_x'], y, ('▶ ' if selected else '  ') + engravings.item_name(eid),
                        config.COLOR_CARD_SELECTED if selected else config.COLOR_TEXT)
        where = engravings.where(eid)
        label = engravings.target_name(where) if where else font.text('새기지 않음', 'Not set')
        small_font.draw(ui['right_x'] + ui['set_x'], y, label,
                        config.COLOR_ENGRAVE_SET if where else config.COLOR_TEXT_DIM)
    eid = owned[pick]
    for k, line in enumerate(engravings.item_desc(eid)):
        small_font.draw(ui['right_x'], ui['desc_y'] - k * ui['line_h'] + ui['line_h'] * 2, line, config.COLOR_TEXT)


def draw():
    play_mode.draw_scene()
    effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, config.ENGRAVE_DIM_ALPHA)
    text_font, small_font = font.get(config.FONT_SIZE_TEXT), font.get(config.FONT_SIZE_SMALL)
    if text_font:
        ui = config.INVENTORY_UI
        text_font.draw(ui['left_x'], ui['title_y'], font.text('인벤토리', 'Inventory'), config.COLOR_DIALOG_NAME)
        draw_status(small_font)
        draw_engravings(text_font, small_font)
        small_font.draw(ui['left_x'], ui['help_y'], font.text('↑↓ 각인   I 닫기', '↑↓ Engraving   I Close'),
                        config.COLOR_TEXT_DIM)
    update_canvas()


def pause():
    pass


def resume():
    pass
