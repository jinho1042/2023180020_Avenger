import json
import math
import os

from pico2d import *

import config
import game_framework
from modes import play_mode
from objects import effect
from systems import economy, engravings, sound
from ui import font

# 대화 · 석판 · 상점 (2.5, 2.6, 13.3). play_mode 위에 push된다 (월드·숨 정지)
# 대사: data/dialog/<id>.json {name, name_en, pages: [[줄, ...], ...], pages_en, shop}. 한 페이지 최대 3줄 (2.6)
# 상점 상품 이름·설명은 data/items.json
# 글자는 DIALOG_CHARS_PER_SEC로 한 글자씩 나온다. Z·X·↑·Enter·Space: 다 나오기 전이면 끝까지, 다 나왔으면 다음 페이지
# 마지막 페이지 뒤 shop이면 상점 목록 (←→ 선택, X 구매, Z·Esc 닫기). Esc는 언제든 닫는다
# start(id, after): 마지막 페이지를 넘기면 닫고 after()를 부른다 (룬지기 → 룬 획득·강화 목록). Esc로 닫으면 부르지 않는다

DIALOG_PATH = os.path.join(os.path.dirname(__file__), '..', config.DIALOG_DIR)
NEXT_KEYS = (SDLK_z, SDLK_x, SDLK_UP, SDLK_RETURN, SDLK_SPACE)
BUY_KEYS = (SDLK_x, SDLK_RETURN, SDLK_SPACE)
CLOSE_KEYS = (SDLK_ESCAPE, SDLK_z)

dialog = None      # 지금 대화 데이터 (start()가 정한다)
after = None       # 끝까지 읽고 닫으면 부를 함수
page = 0
shown = 0.0        # 지금 페이지에서 나온 글자 수 (소수 = 다음 글자까지 진행)
blink = 0.0
view = 'talk'      # 'talk' | 'shop'
stock = []         # 상점 상품 키 (economy.shop_stock)
selected = 0
notice = ''        # 상점 하단 안내 ('광석이 모자랍니다' 등)


def load_dialog(dialog_id):
    path = os.path.join(DIALOG_PATH, f'{dialog_id}.json')
    if not os.path.exists(path):
        # 대사 파일이 없는 NPC: 이름만 보여 주고 닫는다
        return dict(name=dialog_id, pages=[['...']])
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def start(dialog_id, then=None):
    # play_mode·carver_mode가 push_mode 직전에 부른다
    global dialog, after
    dialog = load_dialog(dialog_id)
    after = then


def init():
    global page, shown, blink, view, selected, notice
    page, shown, blink = 0, 0.0, 0.0
    view, selected, notice = 'talk', 0, ''
    sound.play('cursor')


def finish():
    global dialog, after
    dialog = None
    after = None


def pages():
    return dialog.get('pages_en', dialog['pages']) if not font.has_korean() else dialog['pages']


def name():
    return font.text(dialog.get('name', ''), dialog.get('name_en', dialog.get('name', '')))


def page_len():
    return sum(len(line) for line in pages()[page])


def next_page():
    # 반환: 대화가 끝나 닫았으면 True
    global page, shown, view, stock, selected
    if shown < page_len():
        shown = page_len()   # 다 나오기 전이면 끝까지 보여 준다
    elif page + 1 < len(pages()):
        page, shown = page + 1, 0.0
        sound.play('cursor')
    elif dialog.get('shop'):
        view, stock, selected = 'shop', economy.shop_stock(), 0
        sound.play('select')
    else:
        then = after
        game_framework.pop_mode()
        if then:
            then()
        return True
    return False


def buy():
    global stock, selected, notice
    if not stock:
        return
    key = stock[selected]
    price = config.SHOP[key][0]
    if not economy.buy(key):
        notice = font.text(f'보관 광석이 모자랍니다 (필요 {price})', f'Not enough stored ore (need {price})')
        sound.play('cursor')
        return
    notice = font.text(f'{item_name(key)}을(를) 얻었습니다', f'Got {item_name(key)}')
    sound.play('chest')
    play_mode.save_game()    # 구매하면 저장 (13.6)
    stock = economy.shop_stock()
    selected = min(selected, max(0, len(stock) - 1))


def handle_events():
    global selected, notice
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type != SDL_KEYDOWN:
            continue
        elif view == 'talk':
            if e.key == SDLK_ESCAPE:
                game_framework.pop_mode()
                return
            if e.key in NEXT_KEYS and next_page():
                return
        elif e.key in CLOSE_KEYS:
            game_framework.pop_mode()
            return
        elif e.key in (SDLK_LEFT, SDLK_RIGHT) and stock:
            selected = (selected + (1 if e.key == SDLK_RIGHT else -1)) % len(stock)
            notice = ''
            sound.play('cursor')
        elif e.key in BUY_KEYS:
            buy()


def update():
    global shown, blink
    dt = game_framework.frame_time
    blink += dt
    if view == 'talk':
        shown = min(page_len(), shown + config.DIALOG_CHARS_PER_SEC * dt)


# ---------- 그리기 ----------

def box_rect():
    box = config.DIALOG_BOX
    l = (config.SCREEN_W - box['w']) / 2
    return l, box['bottom'], l + box['w'], box['bottom'] + box['h']


def draw_box(l, b, r, t):
    edge = config.DIALOG_BOX['border']
    draw_rectangle(l - edge, b - edge, r + edge, t + edge, *config.COLOR_DIALOG_BORDER, filled=True)
    draw_rectangle(l, b, r, t, *config.COLOR_DIALOG_BOX, filled=True)


def draw_talk():
    text_font, name_font = font.get(config.FONT_SIZE_TEXT), font.get(config.FONT_SIZE_SMALL)
    l, b, r, t = box_rect()
    draw_box(l, b, r, t)
    if not text_font:
        return
    pad, line_h = config.DIALOG_BOX['pad'], config.DIALOG_BOX['line_h']
    name_font.draw(l + pad, t - pad / 2 - config.FONT_SIZE_SMALL / 2, name(), config.COLOR_DIALOG_NAME)
    # 한 글자씩: 앞 줄부터 shown 글자만큼 잘라 그린다
    left = int(shown)
    y = t - pad - config.FONT_SIZE_SMALL - line_h / 2
    for line in pages()[page]:
        if left <= 0:
            break
        text_font.draw(l + pad, y, line[:left], config.COLOR_TEXT)
        left -= len(line)
        y -= line_h
    if shown >= page_len() and math.fmod(blink, config.DIALOG_NEXT_BLINK * 2) < config.DIALOG_NEXT_BLINK:
        name_font.draw(r - pad - config.FONT_SIZE_SMALL, b + pad, '▼', config.COLOR_DIALOG_NAME)


def item_name(key):
    # 상품 이름·설명은 data/items.json (상품 키 = 각인 id 또는 rare_ore_*)
    return engravings.item_name(key)


def item_desc(key):
    return engravings.item_desc(key)


def draw_shop():
    text_font, small_font = font.get(config.FONT_SIZE_TEXT), font.get(config.FONT_SIZE_SMALL)
    l, b, r, t = box_rect()
    draw_box(l, b, r, t)
    if not text_font:
        return
    pad, line_h = config.DIALOG_BOX['pad'], config.DIALOG_BOX['line_h']
    y = t - pad - config.FONT_SIZE_TEXT / 2
    text_font.draw(l + pad, y, f"{name()} — {font.text('상점', 'Shop')}", config.COLOR_DIALOG_NAME)
    ore = font.text(f'보관 광석 {economy.banked()}   희귀 광석 {economy.rare()}',
                    f'Stored ore {economy.banked()}   Rare ore {economy.rare()}')
    text_font.draw(l + pad, y - line_h, ore, config.COLOR_ORE)
    if notice:
        small_font.draw(l + pad, y - line_h * 2, notice, config.COLOR_TEXT)
    help_text = font.text('←→ 선택   X 구매   Z 닫기', '←→ Select   X Buy   Z Close')
    small_font.draw(l + pad, b + pad, help_text, config.COLOR_TEXT_DIM)
    if not stock:
        text_font.draw(config.SCREEN_W / 2 - config.FONT_SIZE_TEXT * 5, config.SHOP_TOP_Y - config.SHOP_CARD_H / 2,
                       font.text('더 팔 물건이 없어.', 'Nothing left to sell.'), config.COLOR_TEXT)
        return
    draw_cards(text_font, small_font)


def draw_cards(text_font, small_font):
    # SHOP_VISIBLE장씩 가로로. 고른 카드가 보이도록 시작 위치를 옮긴다
    count = min(config.SHOP_VISIBLE, len(stock))
    first = min(max(0, selected - count + 1), len(stock) - count)
    total_w = count * config.CARD_W + (count - 1) * config.CARD_GAP
    left = (config.SCREEN_W - total_w) / 2
    t = config.SHOP_TOP_Y
    b = t - config.SHOP_CARD_H
    pad, edge = config.CARD_PAD, config.CARD_BORDER
    for i in range(count):
        index = first + i
        key = stock[index]
        l = left + i * (config.CARD_W + config.CARD_GAP)
        r = l + config.CARD_W
        border = config.COLOR_CARD_SELECTED if index == selected else config.COLOR_CARD_BORDER
        draw_rectangle(l - edge, b - edge, r + edge, t + edge, *border, filled=True)
        draw_rectangle(l, b, r, t, *config.COLOR_CARD, filled=True)
        y = t - pad - config.FONT_SIZE_TEXT / 2
        text_font.draw(l + pad, y, item_name(key), config.COLOR_TEXT)
        y -= config.CARD_LINE_H
        for line in item_desc(key):
            small_font.draw(l + pad, y, line, config.COLOR_TEXT_DIM)
            y -= config.CARD_LINE_H
        price = config.SHOP[key][0]
        color = config.COLOR_ORE if economy.can_pay(price) else config.COLOR_TEXT_DIM
        text_font.draw(l + pad, b + pad, font.text(f'광석 {price}', f'Ore {price}'), color)
    # 좌우에 더 있으면 화살표
    mid = (t + b) / 2
    if first > 0:
        text_font.draw(left - config.CARD_GAP, mid, '◀', config.COLOR_TEXT_DIM)
    if first + count < len(stock):
        text_font.draw(left + total_w + config.CARD_GAP / 2, mid, '▶', config.COLOR_TEXT_DIM)


def draw():
    play_mode.draw_scene()
    if view == 'shop':
        effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_DIM, config.DIM_ALPHA)
        draw_shop()
    else:
        draw_talk()
    update_canvas()


def pause():
    pass


def resume():
    pass
