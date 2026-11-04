from pico2d import *

import config
import game_framework
import game_world
from objects import effect, projectile
from objects.chest import Chest
from objects.player import Player
from systems import camera, combat, hitstop, route, sound, upgrades
from systems.room import Room
from ui import hud

player = None
room = None
enemies = []
boss = None      # 현재 방의 보스 (없으면 None), 보스 HUD용
run_state = None  # [v2] 루트 데이터·현재 위치·보스 처치 기록 (systems/route.py). 새 런마다 통째로 새로 만든다
exits = []       # [v2] 지금 방에서 쓰는 문. 전투방은 i번째 문 → 다음 층 i번째 노드
chest = None     # [v2] 지금 방의 보물상자 (없으면 None)
play_time = 0.0  # 결과 화면 통계 (s)
death_timer = 0.0
pending_exit = None  # 강화 선택이 끝나 돌아오면(resume) 이 번호의 문으로 나간다


def load_room(name, door_count):
    # 월드를 비우고 방을 불러온다. 플레이어 객체는 그대로 옮겨 체력 등을 유지한다
    global room, exits, chest
    game_world.clear()
    hitstop.reset()
    camera.reset()
    room = Room(name)
    chest = None
    game_world.add_objects(room.platforms, config.DEPTH_MAP)
    exits = room.doors[:door_count]
    game_world.add_objects(exits, config.DEPTH_MAP)
    player.enter_room(room.platforms, room.player_start)
    game_world.add_object(player, config.DEPTH_PLAYER)
    # 투사체는 생성될 때 b쪽에 스스로 등록한다
    game_world.add_collision_pair(projectile.GROUP_PLAYER, player, None)


def enter_hub():
    # [v2] 안전지대: 적 없음, 루트 문 3개. 보스를 잡은 루트의 문은 잠긴다. 들어올 때 체력 회복
    global enemies, boss
    run_state['route'] = None
    load_room(config.HUB_ROOM, len(config.ROUTE_ORDER))
    for door, name in zip(exits, config.ROUTE_ORDER):
        door.route = name
        if name in run_state['cleared']:
            door.cleared = True
        else:
            door.open()
    enemies = []
    boss = None
    player.hp = min(player.max_hp, player.hp + player.max_hp * config.HUB_HEAL_RATIO)
    sound.stop_music()


def enter_node(name, layer, index):
    # [v2] 루트 name의 layer층 index번째 방으로 들어간다
    global enemies, boss, chest
    run_state.update(route=name, layer=layer, node=index)
    run_state['rooms_entered'] += 1
    node = route.current_node(run_state)
    load_room(node['template'], route.exit_count(run_state))
    # 상자가 있는 방으로 이어지는 문에는 상자 아이콘
    for door, next_node in zip(exits, route.next_nodes(run_state)):
        door.chest = next_node['has_chest']
    if node['has_chest'] and room.chest_spot:
        chest = Chest(*room.chest_spot)
        game_world.add_object(chest, config.DEPTH_MAP)
    enemies = []
    add_enemies(room.spawn_enemies(player, node['enemies']))
    boss = next((e for e in enemies if e.is_boss), None)
    sound.play_music('boss' if boss else 'battle')


def add_enemies(new):
    # 월드에 넣고 반사 투사체에 맞도록 충돌 그룹에 등록한다 ([v2] 보스가 소환한 적도 여기로)
    # [v2] 일반 적에는 현재 루트 난이도 배율을 곱한다. 보스는 보스별 수치를 그대로 쓴다
    if not new:
        return  # 안전지대(route None)에서도 매 프레임 소환 확인으로 불린다
    difficulty = config.ROUTE_DIFFICULTY[run_state['route']]
    for e in new:
        if not e.is_boss:
            e.apply_difficulty(difficulty['hp_mult'], difficulty['dmg_mult'])
    enemies.extend(new)
    game_world.add_objects(new, config.DEPTH_ENEMY)
    for e in new:
        game_world.add_collision_pair(projectile.GROUP_ENEMY, e, None)


def init():
    global player, run_state, play_time, death_timer, pending_exit
    run_state = route.new_run_state()
    play_time = 0.0
    death_timer = 0.0
    pending_exit = None
    hud.init()
    player = Player([], (0, 0))
    enter_hub()


def finish():
    global player, room, enemies, boss, run_state, exits, chest
    game_world.clear()
    hud.finish()
    player = None
    room = None
    enemies = []
    boss = None
    run_state = None
    exits = []
    chest = None


def handle_events():
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            # T20에서 pause_mode로 교체
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key == SDLK_F1:
            game_world.show_hitbox = not game_world.show_hitbox
        else:
            player.handle_event(e)


def update():
    global enemies, play_time, death_timer
    dt = game_framework.frame_time
    if player.dead:
        # 사망 연출을 잠깐 보여준 뒤 결과 화면으로
        death_timer += dt
        if death_timer >= config.DEATH_DELAY:
            end_run(False)
            return
    else:
        play_time += dt
    # 이번 프레임이 히트스톱 중인지 먼저 정하고 타이머를 줄인다 (이벤트는 그대로 받아 선입력에 저장됨)
    stopped = hitstop.is_active()
    hitstop.update(dt)
    camera.update(dt)
    if stopped:
        game_world.update_layer(config.DEPTH_EFFECT)
        return
    # 슬로모션 중에는 월드에 줄어든 frame_time을 전달한다
    game_framework.frame_time = dt * hitstop.time_scale()
    game_world.update()
    add_enemies([s for e in enemies for s in e.pop_summons()])
    combat.resolve(player, enemies)
    game_world.handle_collisions()
    game_framework.frame_time = dt
    enemies = [e for e in enemies if e.is_alive()]
    if run_state['route'] is None:
        update_hub_doors()
        return
    if not enemies and not exits[0].opened:
        route.current_node(run_state)['cleared'] = True
        for door in exits:
            door.open()
            effect.door_opened(door.x, door.y + config.DOOR_H / 2)
        if chest:
            chest.unlock()
    if chest and not player.dead:
        # 상자에 닿으면 열고, 빛 기둥이 끝나면 강화 선택
        if chest.can_open() and game_world.collide(player, chest):
            chest.open()
        if chest.reward_ready:
            chest.take_reward()
            offer_upgrade()
            return
    if exits[0].opened and not player.dead:
        # 두 문에 동시에 닿아도 하나만 처리하고 바로 방을 전환한다
        for i, door in enumerate(exits):
            if game_world.collide(player, door):
                leave_room(i)
                return


def update_hub_doors():
    # 루트 문에 닿으면 그 루트 1층으로 출발. 두 문에 동시에 닿아도 하나만 처리한다
    if player.dead:
        return
    for door in exits:
        if door.opened and game_world.collide(player, door):
            enter_node(door.route, 0, 0)
            return


def leave_room(exit_index):
    # [v2] 보스방 문이면 보스 보상 강화를 먼저 고르고, 돌아오면(resume) 문 너머로
    if route.is_boss_layer(run_state) and config.BOSS_REWARD_UPGRADE:
        offer_upgrade(exit_index)
    else:
        go_through(exit_index)


def offer_upgrade(exit_index=None):
    # 강화 선택 화면을 위에 올린다. exit_index가 있으면 고르고 돌아온 뒤 그 문으로 나간다
    # 남은 강화가 없으면 화면 대신 체력을 회복한다
    global pending_exit
    choices = upgrades.roll_choices(player)
    if not choices:
        player.hp = min(player.max_hp, player.hp + config.UPGRADE_EMPTY_HEAL)
        if exit_index is not None:
            go_through(exit_index)
        return
    from modes import upgrade_mode
    pending_exit = exit_index
    upgrade_mode.set_choices(player, choices)
    game_framework.push_mode(upgrade_mode)


def go_through(exit_index):
    # 전투방 문 → 다음 층의 해당 노드. 보스방 문 → 루트 클리어 기록 후 안전지대 (보스 전부 처치면 클리어)
    if not route.is_boss_layer(run_state):
        enter_node(run_state['route'], run_state['layer'] + 1, exit_index)
        return
    run_state['cleared'].append(run_state['route'])
    if len(run_state['cleared']) == len(config.ROUTE_ORDER):
        end_run(True)
    else:
        enter_hub()


def end_run(cleared):
    from modes import result_mode
    sound.stop_music()
    result_mode.set_result(cleared, run_state['rooms_entered'], route.total_rooms(), player.parry_count, play_time,
                           run_state['cleared'])
    game_framework.change_mode(result_mode)


def background_color():
    # [v2] 루트 안에서는 배경을 루트 색 쪽으로 섞는다
    if run_state['route'] is None:
        return config.COLOR_PLAY_BG
    tint = config.ROUTE_BG_TINT
    return tuple(int(b + (c - b) * tint)
                 for b, c in zip(config.COLOR_PLAY_BG, config.ROUTE_COLOR[run_state['route']]))


def draw_scene():
    # 위에 올라온 모드(강화 선택 등)가 배경으로 쓸 수 있게 update_canvas 없이 그린다
    clear_canvas()
    draw_rectangle(0, 0, config.SCREEN_W, config.SCREEN_H, *background_color(), filled=True)
    camera.begin()
    game_world.render()
    camera.end()
    hud.draw(player, boss if boss and boss.is_alive() else None, run_state)


def draw():
    draw_scene()
    update_canvas()


def pause():
    pass


def resume():
    global pending_exit
    player.clear_input()
    if pending_exit is not None:
        exit_index, pending_exit = pending_exit, None
        go_through(exit_index)
