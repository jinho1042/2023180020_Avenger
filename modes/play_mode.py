import random

from pico2d import *

import config
import game_framework
import game_world
from objects import effect, projectile
from objects.player import Player
from systems import camera, combat, hitstop, sound, upgrades
from systems.room import Room
from ui import hud

player = None
room = None
enemies = []
boss = None      # 현재 방의 보스 (없으면 None), 보스 HUD용
run_rooms = []   # 이번 런의 방 순서 (템플릿 이름, 전투방은 중복 없음, 보스방 포함)
room_index = 0   # 런에서 현재 몇 번째 방인지 (run_rooms 기준)
play_time = 0.0  # 결과 화면 통계 (s)
death_timer = 0.0
upgrade_pending = False  # 강화 선택이 끝나 돌아오면(resume) 다음 방으로


def enter_room(index):
    # 월드를 비우고 index번째 방을 불러온다. 플레이어 객체는 그대로 옮겨 체력 등을 유지한다
    global room, enemies, room_index, boss
    room_index = index
    game_world.clear()
    hitstop.reset()
    camera.reset()
    room = Room(run_rooms[index])
    game_world.add_objects(room.platforms, config.DEPTH_MAP)
    game_world.add_object(room.door, config.DEPTH_MAP)
    player.enter_room(room.platforms, room.player_start)
    game_world.add_object(player, config.DEPTH_PLAYER)
    # 투사체는 생성될 때 b쪽에 스스로 등록한다
    game_world.add_collision_pair(projectile.GROUP_PLAYER, player, None)
    enemies = room.spawn_enemies(player)
    game_world.add_objects(enemies, config.DEPTH_ENEMY)
    boss = next((e for e in enemies if e.is_boss), None)
    for e in enemies:
        game_world.add_collision_pair(projectile.GROUP_ENEMY, e, None)
    sound.play_music('boss' if boss else 'battle')


def init():
    global player, run_rooms, play_time, death_timer, upgrade_pending
    run_rooms = random.sample(config.ROOM_TEMPLATES, config.RUN_COMBAT_ROOMS)
    for index, name in config.RUN_BOSS_ROOMS:
        run_rooms.insert(index, name)
    play_time = 0.0
    death_timer = 0.0
    upgrade_pending = False
    hud.init()
    player = Player([], (0, 0))
    enter_room(0)


def finish():
    global player, room, enemies, run_rooms, room_index, boss
    game_world.clear()
    hud.finish()
    player = None
    room = None
    enemies = []
    boss = None
    run_rooms = []
    room_index = 0


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
    combat.resolve(player, enemies)
    game_world.handle_collisions()
    game_framework.frame_time = dt
    enemies = [e for e in enemies if e.is_alive()]
    if not enemies and not room.door.opened:
        room.door.open()
        effect.door_opened(room.door.x, room.door.y + config.DOOR_H / 2)
    if room.door.opened and not player.dead and game_world.collide(player, room.door):
        leave_room()


def leave_room():
    # 정해진 방을 클리어했으면 강화 선택 화면을 위에 올리고, 고르고 돌아오면 다음 방으로
    global upgrade_pending
    if room_index + 1 in config.RUN_UPGRADE_AFTER:
        from modes import upgrade_mode
        upgrade_pending = True
        upgrade_mode.set_choices(player, upgrades.roll_choices(player))
        game_framework.push_mode(upgrade_mode)
    else:
        next_room()


def next_room():
    if room_index + 1 < len(run_rooms):
        enter_room(room_index + 1)
    else:
        end_run(True)


def end_run(cleared):
    from modes import result_mode
    sound.stop_music()
    result_mode.set_result(cleared, room_index + 1, len(run_rooms), player.parry_count, play_time)
    game_framework.change_mode(result_mode)


def draw_scene():
    # 위에 올라온 모드(강화 선택 등)가 배경으로 쓸 수 있게 update_canvas 없이 그린다
    clear_canvas()
    draw_rectangle(0, 0, config.SCREEN_W, config.SCREEN_H, *config.COLOR_PLAY_BG, filled=True)
    camera.begin()
    game_world.render()
    camera.end()
    hud.draw(player, boss if boss and boss.is_alive() else None)


def draw():
    draw_scene()
    update_canvas()


def pause():
    pass


def resume():
    global upgrade_pending
    player.clear_input()
    if upgrade_pending:
        upgrade_pending = False
        next_room()
