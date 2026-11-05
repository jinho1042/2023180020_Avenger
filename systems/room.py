import json
import random

import config
from objects.air_vent import AirVent
from objects.bosses.crystal_archsage import CrystalArchsage
from objects.bosses.moss_warden import MossWarden
from objects.bosses.rockshell_borer import RockshellBorer
from objects.bosses.scythe_sovereign import ScytheSovereign
from objects.breath_zone import BreathGate, BreathZone
from objects import enemy_base
from objects.breakable import Breakable
from objects.enemies.bat import Bat
from objects.enemies.crawler import Crawler
from objects.enemies.crystal_sage import CrystalSage
from objects.enemies.crystal_sprite import CrystalSprite
from objects.enemies.scythe_mantis import ScytheMantis
from objects.enemies.shadow_stalker import ShadowStalker
from objects.enemies.shell_warrior import ShellWarrior
from objects.enemies.spore_shroom import SporeShroom
from objects.enemies.thorn_flower import ThornFlower
from objects.enemies.vine_lurker import VineLurker
from objects.exit_zone import ExitZone
from objects.gate import Gate
from objects.hazard import Hazard, Rockfall
from objects.npc import Npc
from objects.platform import Platform
from objects.safe_zone import SafeZone
from objects.switch import Switch
from objects.training_statue import TrainingStatue

# spawns의 이름 → 적 클래스 (10.2). 독 거머리·유적 골렘은 T53
ENEMY_TYPES = {'crawler': Crawler, 'bat': Bat, 'shell_warrior': ShellWarrior, 'thorn_flower': ThornFlower,
               'spore_shroom': SporeShroom, 'vine_lurker': VineLurker,
               'crystal_sprite': CrystalSprite, 'crystal_sage': CrystalSage,
               'scythe_mantis': ScytheMantis, 'shadow_stalker': ShadowStalker}
# 보스 (11.4): 방 JSON boss 값 = 키. 보스 자리는 spawns에 같은 이름으로 둔다 ([종류, x, y])
BOSS_TYPES = {'borer': RockshellBorer, 'moss_warden': MossWarden, 'archsage': CrystalArchsage, 'scythe': ScytheSovereign}
ARENA_ZONE_ID = 'arena'   # 처치 후 아레나 전체를 덮는 안전지대 id (앉는 자리 없음, 11.2)


class Room:
    # 방 JSON v3 (12.5) 하나를 읽어 지형·출구 객체와 배치 정보를 보관한다. 방 파일 찾기는 systems/world.py
    # [v2] 템플릿(id 대신 name, exits 없음)도 읽는다. 보스방을 F4로 시험하는 용도 (T45에서 v3로 옮김)
    def __init__(self, path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.id = data.get('id') or data['name']
        self.region = data.get('region')
        # size: [가로, 세로] 화면 수. 방 크기 = size × (SCREEN_W, SCREEN_H), 월드 좌표는 방 좌하단 = (0, 0)
        self.size = tuple(data.get('size', (1, 1)))
        self.width = self.size[0] * config.SCREEN_W
        self.height = self.size[1] * config.SCREEN_H
        self.platforms = [Platform(*p) for p in data['platforms']]
        self.exits = [ExitZone(e, self.width, self.height) for e in data.get('exits', [])]
        # 일반 적은 저장하지 않고 방을 불러올 때마다 spawns대로 다시 만든다 (5.6). [v2] spawn_sets면 하나를 고른다
        spawn_sets = data.get('spawn_sets') or [data.get('spawns', [])]
        self.spawns = random.choice(spawn_sets)
        # safe_points: 환경 피해 뒤 돌아올 지점 [x, y] (6.8, 12.5). 없으면 플레이어가 오래 서 있던 바닥
        self.safe_points = [tuple(p) for p in data.get('safe_points', [])]
        # [v2] player_start. v3 방은 출구로 들어오고, 워프는 safe_points[0] → 첫 출구 순으로 자리를 고른다
        self.player_start = tuple(data['player_start']) if 'player_start' in data else None
        # 나머지 12.5 필드. 기믹 객체는 build()가 만든다 (T35~). 아직 객체가 없는 필드는 배치 정보만 보관한다
        self.map_cell = tuple(data.get('map_cell', (0, 0)))
        self.music = data.get('music')
        self.air = data.get('air')
        self.hub = data.get('hub', False)
        self.boss = data.get('boss')
        # breath_gates: (x, y, w, h, 게이트 id, 요구 숨 Lv). 방 전체를 덮는다 (7.3)
        self.breath_gates = [tuple(g) for g in data.get('breath_gates', [])]
        # gates: (x, y, w, h, 종류, id, 속성 dict). 속성(open_from, to_hub)은 선택이라 없으면 빈 dict
        self.gates = [tuple(g[:6]) + (dict(g[6]) if len(g) > 6 else {},) for g in data.get('gates', [])]
        for field in ('hazards', 'water', 'breath_zones', 'safe_zones', 'air_vents', 'breakables',
                      'switches', 'objects', 'triggers'):
            setattr(self, field, [tuple(item) for item in data.get(field, [])])

    def build(self, state):
        # 기믹 객체를 만든다 (12.6). 부서진 벽·열린 문은 만들지 않는다 (5.6)
        # 닫힌 문·부서지기 전 벽은 terrain에 넣어 플레이어·적·투사체가 지형처럼 부딪힌다
        self.hazard_objects = ([Hazard(*h) for h in self.hazards if h[4] in Hazard.KINDS]
                               + [Rockfall(*h) for h in self.hazards if h[4] in Rockfall.KINDS])
        breakables = [Breakable(self.id, *b, state) for b in self.breakables
                      if b[4] in Breakable.KINDS and f'{self.id}:{b[5]}' not in state.broken]
        gates = {g[5]: Gate(self.id, *g, state) for g in self.gates
                 if g[4] in Gate.KINDS and f'{self.id}:{g[5]}' not in state.opened}
        switches = [Switch(self.id, *s, gates.get(s[4]), state) for s in self.switches if s[2] in Switch.KINDS]
        # 보스를 처치한 아레나는 전체가 영구 안전지대 (11.2). 앉는 자리는 없어 저장·부활 지점은 아니다
        if self.boss_defeated(state) and not self.zone_floor(ARENA_ZONE_ID):
            self.safe_zones.append(self.arena_zone())
        self.safe_zone_objects = [SafeZone(self.id, *z, self.seat_of(z[4]), state) for z in self.safe_zones]
        # 숨 (7.2): 배율 영역 + water(자동으로 water 배율), 숨 게이트, 숨구멍
        self.breath_zone_objects = ([BreathZone(*z) for z in self.breath_zones]
                                    + [BreathZone(*w[:4], 'water') for w in self.water])
        self.breath_gate_objects = [BreathGate(*g) for g in self.breath_gates]
        self.air_vent_objects = [AirVent(self.id, *v, self.region) for v in self.air_vents]
        # NPC·석판·룬지기 (2.5): ↑로 말 걸기. 지형이 아니라 곡괭이에도 맞지 않는다
        self.npc_objects = [Npc(*o[:4]) for o in self.objects if o[0] in ('npc', 'tablet', 'carver')]
        # 연습 석상 (9.5): 부서진 것은 만들지 않는다. 적 목록에 넣어 패링 판정을 쓴다 (spawn_enemies)
        self.statues = [(o[1], o[2], o[3]) for o in self.objects
                        if o[0] == 'statue' and f'{self.id}:{o[3]}' not in state.broken]
        self.state = state
        self.arena_gates = [g for g in gates.values() if g.type == 'arena']
        self.terrain = self.platforms + breakables + list(gates.values())
        # 곡괭이에 맞는 기믹 전부 (combat.hit_gimmicks)
        self.gimmicks = self.hazard_objects + breakables + list(gates.values()) + switches

    def boss_defeated(self, state):
        return bool(self.boss) and self.boss in state.bosses_defeated

    def arena_zone(self):
        return 0, 0, self.width, self.height, ARENA_ZONE_ID

    def release_air(self, state):
        # 보스를 처치한 순간: 아레나가 공기가 있는 곳이 된다. 새 안전지대 객체를 돌려준다 (play_mode가 월드에 넣음)
        self.safe_zones.append(self.arena_zone())
        zone = SafeZone(self.id, *self.arena_zone(), None, state)
        self.safe_zone_objects.append(zone)
        enemy_base.set_safe_zones(z.get_bb() for z in self.safe_zone_objects)
        return zone

    def seat_of(self, zone_id):
        # objects의 ["seat", x, y, 안전지대 id] → (x, y). 없으면 None
        return next(((o[1], o[2]) for o in self.objects if o[0] == 'seat' and o[3] == zone_id), None)

    def zone_floor(self, zone_id):
        # 안전지대 영역 바닥 가운데 (기절 복귀, 7.3). 없는 id면 None
        zone = next((z for z in self.safe_zones if z[4] == zone_id), None)
        return (zone[0] + zone[2] / 2, zone[1]) if zone else None

    def seat_spot(self, zone_id):
        # 이어하기·부활 자리: 앉는 자리, 없으면 안전지대 바닥 가운데. zone_id가 None이거나 없는 id면 None
        zone = next((z for z in self.safe_zones if z[4] == zone_id), None)
        if zone is None:
            return None
        x, y, w, h = zone[:4]
        return self.seat_of(zone_id) or (x + w / 2, y)

    def exit(self, exit_id):
        return next(e for e in self.exits if e.id == exit_id)

    def spawn_enemies(self, player):
        # 일반 적은 안전지대 영역에 들어오지 않는다 (10.1)
        enemy_base.set_safe_zones(z.get_bb() for z in self.safe_zone_objects)
        enemies = [ENEMY_TYPES[kind](x, y, player, self.terrain) for kind, x, y in self.spawns if kind in ENEMY_TYPES]
        if not self.boss_defeated(self.state):
            enemies += [BOSS_TYPES[kind](x, y, player, self.terrain) for kind, x, y in self.spawns
                        if kind in BOSS_TYPES]
        statues = [TrainingStatue(self.id, x, y, sid, player, self.terrain, self.state) for x, y, sid in self.statues]
        return enemies + statues
