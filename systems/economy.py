# 광석 (13.2): 소지 광석·보관 광석·희귀 광석
# 소지 광석은 저장하지 않으므로 여기 들고 있고, 보관·희귀 광석은 세이브되는 world.state.player에 있다
# 안전지대 영역에 들어가면 소지 광석이 전부 보관되고, 죽으면 소지 광석의 DEATH_ORE_LOSS 비율을 잃는다

import config
from systems import engravings, sound, world

carried = 0
bank_timer = 0.0     # 보관 연출 남은 시간 (HUD가 소지 → 보관 숫자 이동을 그린다)
bank_amount = 0      # 이번 보관 연출로 옮긴 양


def init():
    # 새 게임·이어하기·부활 모두 소지 0에서 시작한다 (13.6)
    global carried, bank_timer, bank_amount
    carried, bank_timer, bank_amount = 0, 0.0, 0


def banked():
    return world.state.player.ore_banked


def rare():
    return world.state.player.rare_ore


def add(amount):
    # 광석 조각 흡수 (objects/pickup.py)
    global carried
    carried += amount


def bank():
    # 안전지대 영역 안: 소지 광석을 전부 보관한다. 반환: 옮긴 양
    global carried, bank_timer, bank_amount
    if carried <= 0:
        return 0
    amount = carried
    world.state.player.ore_banked += amount
    carried = 0
    # 연출 중에 또 보관하면 남은 연출에 더해서 이어 간다
    bank_amount = amount + (bank_amount if bank_timer > 0 else 0)
    bank_timer = config.ORE_BANK_TIME
    sound.play('bank')
    return amount


def lose_on_death():
    # 사망 (13.2): 소지 광석의 DEATH_ORE_LOSS 비율을 잃는다 (회수 불가). 보관·희귀 광석은 그대로. 반환: 잃은 양
    global carried
    lost = round(carried * config.DEATH_ORE_LOSS)
    carried -= lost
    world.state.stats['ore_lost'] += lost
    return lost


def can_pay(ore, rare_ore=0):
    # 지불은 보관 광석으로만 (13.2). 가격표는 config (상점·대장간·룬지기)
    p = world.state.player
    return p.ore_banked >= ore and p.rare_ore >= rare_ore


def pay(ore, rare_ore=0):
    # 모자라면 내지 않고 False
    if not can_pay(ore, rare_ore):
        return False
    p = world.state.player
    p.ore_banked -= ore
    p.rare_ore -= rare_ore
    return True


def shop_condition_met(condition):
    # 판매 조건 (config.SHOP). 'region_<구역>' = 그 구역 방 하나라도 방문, 'miners_<n>' = 실종 광부 n명 이상 구출
    if condition is None:
        return True
    state = world.state
    kind, _, value = condition.partition('_')
    if kind == 'region':
        return any(world.room_region(r) == value for r in state.visited)
    if kind == 'miners':
        return len(state.miners_rescued) >= int(value)
    return False


def shop_sold(key):
    # 한 번 산 상품은 다시 팔지 않는다. 각인은 다른 데서 얻었어도 판매 끝
    p = world.state.player
    return f'shop_{key}' in world.state.collected or key in p.engravings_owned


def shop_stock():
    # 지금 목록에 나오는 상품 키 (config.SHOP 순서). 조건을 채우기 전·이미 산 상품은 목록에 없다 (13.3)
    return [key for key, (price, condition) in config.SHOP.items()
            if shop_condition_met(condition) and not shop_sold(key)]


def buy(key):
    # 보관 광석으로 사서 바로 얻는다. 각인은 보유 목록에만 넣는다 (장착은 안전지대 각인 화면, T44)
    # 반환: 샀으면 True. 저장은 부른 쪽 (13.6 '구매' 저장 시점)
    price, condition = config.SHOP[key]
    if key not in shop_stock() or not pay(price):
        return False
    p = world.state.player
    if key in engravings.IDS:
        p.engravings_owned.add(key)
    else:
        p.rare_ore += config.SHOP_RARE_ORE
    world.state.collected.add(f'shop_{key}')
    return True


def update(dt):
    global bank_timer
    bank_timer = max(0, bank_timer - dt)


def bank_progress():
    # 보관 연출 진행도 0 → 1. 연출 중이 아니면 None
    if bank_timer <= 0:
        return None
    return 1 - bank_timer / config.ORE_BANK_TIME
