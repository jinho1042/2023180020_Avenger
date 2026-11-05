import pico2d
from pico2d import *

import config
import game_framework
import game_world
from objects import effect, projectile
from objects.player import Player
from systems import breath, camera, combat, economy, hitstop, input, runes, save, script, sound, world
from ui import hud

player = None
room = None
enemies = []
boss = None      # 현재 방의 보스 (없으면 None), 보스 HUD용
play_time = 0.0  # 세이브 play_time·결과 화면 통계 (s)
death_timer = 0.0
respawning = False  # 사망 → 부활 방으로 전환 중. 방에 들어오는 순간 되살린다
ore_lost = 0        # 이번 사망으로 잃은 소지 광석 (부활 후 알림)
load_path = None  # 이어하기면 불러올 세이브 경로, 새 게임이면 None. title_mode가 change_mode 직전에 start()로 정한다
DEBUG_KEY = {getattr(pico2d, name): action for action, name in config.DEBUG_KEYS.items()}
MAP_KEY = getattr(pico2d, config.KEYS['map'])


def enter_room(new_room, arrival):
    # systems/world.py가 방을 바꿀 때 부른다. 월드를 비우고 새 방을 채운다
    # 플레이어 객체는 그대로 옮겨 체력 등을 유지한다. 투사체·이펙트는 game_world.clear()로 정리된다
    global room, enemies, boss
    game_world.clear()
    if respawning:
        revive()
    hitstop.reset()
    camera.reset()
    room = new_room
    game_world.set_room_size(room.width, room.height)
    camera.set_room(room.width, room.height)
    script.enter_room(room, player)   # 트리거 (도입부 등). 배경 쪽에 그려지도록 먼저 넣는다
    game_world.add_objects(room.breath_gate_objects, config.DEPTH_BG)
    game_world.add_objects(room.breath_zone_objects, config.DEPTH_BG)
    game_world.add_objects(room.safe_zone_objects, config.DEPTH_BG)
    game_world.add_objects(room.air_vent_objects, config.DEPTH_MAP)
    game_world.add_objects(room.platforms, config.DEPTH_MAP)
    game_world.add_objects(room.exits, config.DEPTH_MAP)
    game_world.add_objects(room.gimmicks, config.DEPTH_MAP)
    game_world.add_objects(room.npc_objects, config.DEPTH_MAP)
    world.place_player(player, room, arrival)
    game_world.add_object(player, config.DEPTH_PLAYER)
    # 투사체는 생성될 때 b쪽에 스스로 등록한다
    game_world.add_collision_pair(projectile.GROUP_PLAYER, player, None)
    camera.snap(player)  # 방 전환 직후 카메라는 즉시 목표 위치 (14.2)
    # 일반 적은 방에 들어올 때마다 spawns대로 다시 생긴다 (5.6)
    enemies = []
    add_enemies(room.spawn_enemies(player))
    boss = next((e for e in enemies if e.is_boss), None)
    if any(e.kind != 'statue' for e in enemies):   # 연습 석상만 있는 방은 전투 음악 없음
        sound.play_music('boss' if boss else 'battle')
    else:
        sound.stop_music()


def add_enemies(new):
    # 월드에 넣고 반사 투사체에 맞도록 충돌 그룹에 등록한다 ([v2] 보스가 소환한 적도 여기로)
    enemies.extend(new)
    game_world.add_objects(new, config.DEPTH_ENEMY)
    for e in new:
        game_world.add_collision_pair(projectile.GROUP_ENEMY, e, None)


def start(path=None):
    global load_path
    load_path = path


def init():
    global player, play_time, death_timer, respawning
    play_time = 0.0
    death_timer = 0.0
    respawning = False
    hud.init()
    economy.init()
    script.init()
    player = Player([], (0, 0))
    loaded = None
    if load_path:
        loaded, play_time = save.load(load_path)
    world.init(enter_room, loaded)
    state = world.state
    player.world_state = state
    player.max_hp = player.hp = state.player.hp_max
    player.pickaxe_lv = state.player.pickaxe_level
    player.parry_count = state.stats['parries']
    breath.init(state)
    # 이어하기는 항상 마지막으로 앉은 자리에서 (13.6). 앉은 적이 없으면 새 게임 첫 방 (18장)
    if state.rest_seat and state.rest_seat.split(':')[0] in world.room_paths:
        world.load(*world.seat_arrival(state.rest_seat))
    else:
        world.load(config.START_ROOM)


def finish():
    global player, room, enemies, boss
    game_world.clear()
    world.finish()
    hud.finish()
    player = None
    room = None
    enemies = []
    boss = None


def handle_events():
    for e in get_events():
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            # 일시정지. 방 전환 중·사망 연출 중에는 열지 않는다 (페이드 중 저장 금지, 13.6)
            if world.phase is None and not player.dead and not player.cutscene:
                from modes import pause_mode
                game_framework.push_mode(pause_mode)
                return
        elif e.type == SDL_KEYDOWN and e.key == MAP_KEY:
            # 지도는 Tab을 누르고 있는 동안 (13.4). 방 전환·사망·기절 중에는 열지 않는다
            if world.phase is None and not player.dead and not player.blackout and not player.cutscene:
                from modes import map_mode
                game_framework.push_mode(map_mode)
                return
        elif e.type == SDL_KEYDOWN and e.key == SDLK_F1:
            game_world.show_hitbox = not game_world.show_hitbox
        elif config.DEBUG and e.type == SDL_KEYDOWN and DEBUG_KEY.get(e.key) == 'unlock_all':
            runes.unlock_all(world.state)
            print('[DEBUG] F3 전체 해금: 모든 룬 최대 레벨 + 반사')
        elif config.DEBUG and e.type == SDL_KEYDOWN and DEBUG_KEY.get(e.key) == 'infinite_breath':
            on = breath.toggle_infinite()
            hud.show_message(f"숨 무한 {'켬' if on else '끔'}")
            print(f"[DEBUG] F5 숨 무한 {'켬' if on else '끔'}")
        elif config.DEBUG and e.type == SDL_KEYDOWN and DEBUG_KEY.get(e.key) == 'record_breath':
            line = breath.record(room.id)
            hud.show_message('숨 구간 기록' if line else '기록할 구간 없음')
            print(f'[DEBUG] F6 숨 구간 기록: {line}')
        elif config.DEBUG and e.type == SDL_KEYDOWN and DEBUG_KEY.get(e.key) in ('warp', 'give'):
            # F4 방 이동 메뉴 · F7 개별 지급 메뉴. 방 전환 중에는 열지 않는다
            if world.phase is None:
                from modes import debug_warp_mode
                debug_warp_mode.open_menu(DEBUG_KEY[e.key])
                game_framework.push_mode(debug_warp_mode)
                return
        else:
            player.handle_event(e)


def update():
    global enemies, play_time, death_timer
    dt = game_framework.frame_time
    world.update(dt)
    script.update(dt)
    hud.update(dt)
    economy.update(dt)
    if world.frozen():
        return  # 방 전환으로 어두워지는 동안 월드 정지 (누름 상태는 handle_events가 계속 받는다)
    if player.dead:
        # 사망 연출을 잠깐 보여준 뒤 암전 → 마지막으로 앉은 안전지대에서 부활 (13.2)
        death_timer += dt
        if death_timer >= config.DEATH_DELAY and not respawning:
            start_respawn()
    else:
        play_time += dt
    # 이번 프레임이 히트스톱 중인지 먼저 정하고 타이머를 줄인다 (이벤트는 그대로 받아 선입력에 저장됨)
    stopped = hitstop.is_active()
    hitstop.update(dt)
    camera.update(dt, player)
    if stopped:
        game_world.update_layer(config.DEPTH_EFFECT)
        return
    # 슬로모션 중에는 월드에 줄어든 frame_time을 전달한다
    game_framework.frame_time = dt * hitstop.time_scale()
    game_world.update()
    add_enemies([s for e in enemies for s in e.pop_summons()])
    combat.resolve(player, enemies, room.gimmicks)
    game_world.handle_collisions()
    game_framework.frame_time = dt
    enemies = [e for e in enemies if e.is_alive()]
    check_hazards()
    if check_npcs():
        return   # 대화를 열었다 (dialog_mode가 위에 올라와 월드·숨 정지)
    zone = check_safe_zones()
    check_air_vents()
    if world.phase is None and not player.cutscene:
        # 숨은 방 전환 페이드·컷신 중에는 멈춘다 (7.2). 슬로모션이면 월드와 같은 속도로
        breath.update(dt * hitstop.time_scale(), player, room, zone)
    check_exits()


def check_hazards():
    # 가시·산성·구덩이·낙석에 몸이 닿으면 환경 피해 → 안전 지점 (6.8). 포고가 먼저 되도록 공격 판정 뒤에 본다
    # 도입부 붕괴 중에는 피해 없이 장면 처음부터 (script.on_hazard)
    if player.dead or player.is_hazard_respawning() or player.blackout or player.cutscene:
        return
    for hazard in room.hazard_objects:
        hazard.notice(player)
    for hazard in room.hazard_objects:
        if hazard.is_harmful() and game_world.collide(player, hazard):
            if not script.on_hazard():
                player.hazard_hit()
            return


def check_npcs():
    # 말 걸 수 있는 NPC·석판 머리 위에 ↑ 표시, ↑를 누르면 대화 (2.5). 앉는 자리보다 먼저 ↑를 받는다
    # 반환: 대화를 열었으면 True. 방 전환·사망·기절 중에는 열지 않는다
    near = None
    for npc in room.npc_objects:
        npc.prompt = False
        if near is None and world.phase is None and not player.dead and not player.blackout and npc.can_talk(player):
            near = npc
    if near is None:
        return False
    near.prompt = True
    if not input.consume('up'):
        return False
    near.prompt = False
    from modes import dialog_mode
    dialog_mode.start(near.id)
    game_framework.push_mode(dialog_mode)
    return True


def check_safe_zones():
    # 영역에 들어오면 발견 (13.1). 앉는 자리에서 ↑를 누르면 앉는다
    # 반환: 몸이 들어 있는 안전지대 (없으면 None). 숨 회복·기절 복귀 지점 갱신은 breath.update가 한다
    inside = None
    for zone in room.safe_zone_objects:
        zone.prompt = False
        if player.dead or player.blackout or not game_world.collide(player, zone):
            continue
        inside = inside or zone
        world.state.safe_zones_found.add(zone.gid)
        economy.bank()   # 영역 안에 들어오기만 해도 소지 광석 자동 보관 (13.2)
        if zone.can_sit(player):
            zone.prompt = True
            if input.consume('up'):
                sit(zone)
    return inside


def check_air_vents():
    # 쿨다운이 끝난 숨구멍에 몸이 닿으면 숨 회복 (7.2)
    if player.dead or player.blackout:
        return
    for vent in room.air_vent_objects:
        if vent.ready() and game_world.collide(player, vent):
            vent.use()
            breath.touch_air_vent(vent)


def sit(zone):
    # 앉기: 체력 전부 회복 · 부활 지점 갱신 · 자동 저장 (13.1). 적은 따로 재생성하지 않는다
    player.sit(zone.seat[0])
    player.hp = player.max_hp
    world.state.rest_seat = zone.gid
    zone.prompt = False
    sound.play('select')
    save_game()


def save_game():
    # 플레이어 객체에만 있는 값을 상태에 옮긴 뒤 저장한다. 경로는 debug_unlocked로 정해진다 (13.6)
    state = world.state
    state.player.hp_max = player.max_hp
    state.player.pickaxe_level = player.pickaxe_lv
    state.stats['parries'] = player.parry_count
    path = save.write(state, play_time)
    print(f'[저장] {path}')
    hud.show_message('저장했습니다 (디버그)' if state.debug_unlocked else '저장했습니다')


def check_exits():
    # 출구에 몸이 닿으면 그 방으로. 두 출구에 동시에 닿아도 하나만 처리한다
    if player.dead or player.is_hazard_respawning() or player.blackout or not world.can_exit():
        return
    for exit_zone in room.exits:
        if game_world.collide(player, exit_zone):
            world.go_through(exit_zone, player)
            return


def start_respawn():
    # 사망 (13.2): 소지 광석 일부를 잃고 마지막으로 앉은 자리로 (앉은 적이 없으면 새 게임 첫 방)
    # 보관·희귀 광석은 그대로. 게이트 기절(7.3)은 사망이 아니므로 여기를 거치지 않는다
    global respawning, ore_lost
    respawning = True
    ore_lost = economy.lose_on_death()
    world.state.stats['deaths'] += 1
    seat = world.state.rest_seat
    print(f'[사망] 소지 광석 {ore_lost} 잃음 → {seat or config.START_ROOM}')
    if seat and seat.split(':')[0] in world.room_paths:
        room_id, zone_id = seat.split(':')
        world.warp(room_id, seat=zone_id)
    else:
        world.warp(config.START_ROOM)


def revive():
    # 부활 방에 들어오는 순간 (화면이 가장 어두울 때): 체력 전부, 숨 가득
    global respawning, death_timer
    respawning = False
    death_timer = 0.0
    player.revive()
    breath.refill(world.state)
    if ore_lost:
        hud.show_message(f'광석 {ore_lost} 잃음')


def background_color():
    # 배경을 구역 대표 색 쪽으로 섞는다
    region = config.REGIONS.get(room.region)
    if region is None:
        return config.COLOR_PLAY_BG
    tint = config.REGION_BG_TINT
    return tuple(int(b + (c - b) * tint) for b, c in zip(config.COLOR_PLAY_BG, region['color']))


def draw_scene():
    # 위에 올라온 모드가 배경으로 쓸 수 있게 update_canvas 없이 그린다
    clear_canvas()
    draw_rectangle(0, 0, config.SCREEN_W, config.SCREEN_H, *background_color(), filled=True)
    camera.begin()
    game_world.render()
    camera.end()
    hud.draw_breath_vignette()
    alpha = max(world.fade_alpha(), breath.blackout_alpha())
    if alpha > 0:
        effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_FADE, alpha)
    hud.draw(player, boss if boss and boss.is_alive() else None)
    if script.fade_alpha() > 0:
        # 도입부 추락 암전은 HUD까지 덮는다
        effect.draw_screen_alpha_rect(0, 0, config.SCREEN_W, config.SCREEN_H, config.COLOR_FADE, script.fade_alpha())


def draw():
    draw_scene()
    update_canvas()


def pause():
    pass


def resume():
    player.clear_input()
