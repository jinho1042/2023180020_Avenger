# 광석 (13.2): 소지 광석·보관 광석·희귀 광석
# 소지 광석은 저장하지 않으므로 여기 들고 있고, 보관·희귀 광석은 세이브되는 world.state.player에 있다
# 안전지대 영역에 들어가면 소지 광석이 전부 보관되고, 죽으면 소지 광석의 DEATH_ORE_LOSS 비율을 잃는다

import config
from systems import sound, world

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


def update(dt):
    global bank_timer
    bank_timer = max(0, bank_timer - dt)


def bank_progress():
    # 보관 연출 진행도 0 → 1. 연출 중이 아니면 None
    if bank_timer <= 0:
        return None
    return 1 - bank_timer / config.ORE_BANK_TIME
