import json
import os
import random

import config
from objects.boss_greatsword import BossGreatsword
from objects.boss_mage import BossMage
from objects.boss_twinblade import BossTwinblade
from objects.door import Door
from objects.enemy_adept_mage import EnemyAdeptMage
from objects.enemy_apprentice_mage import EnemyApprenticeMage
from objects.enemy_archer import EnemyArcher
from objects.enemy_assassin import EnemyAssassin
from objects.enemy_dual_dagger import EnemyDualDagger
from objects.enemy_flyer import EnemyFlyer
from objects.enemy_melee import EnemyMelee
from objects.platform import Platform

ROOM_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'rooms')
# spawns의 이름 → 적 클래스
ENEMY_TYPES = {'melee': EnemyMelee, 'flyer': EnemyFlyer, 'archer': EnemyArcher,
               'apprentice_mage': EnemyApprenticeMage, 'adept_mage': EnemyAdeptMage,
               'dual_dagger': EnemyDualDagger, 'assassin': EnemyAssassin,
               'greatsword': BossGreatsword, 'mage': BossMage, 'twinblade': BossTwinblade}


class Room:
    # 방 템플릿 JSON 하나를 읽어 지형 객체와 배치 정보를 보관한다
    def __init__(self, name):
        path = os.path.join(ROOM_DIR, name + '.json')
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.name = data['name']
        self.type = data['type']
        # size: [가로, 세로] 화면 수 (12.5). 방 크기 = size × (SCREEN_W, SCREEN_H), 월드 좌표는 방 좌하단 = (0, 0)
        self.size = tuple(data.get('size', (1, 1)))
        self.width = self.size[0] * config.SCREEN_W
        self.height = self.size[1] * config.SCREEN_H
        self.platforms = [Platform(*p) for p in data['platforms']]
        # spawn_sets(적 배치 세트 여러 개) 중 하나를 무작위로 고른다. 세트가 하나뿐이면 spawns로 써도 된다
        spawn_sets = data.get('spawn_sets') or [data.get('spawns', [])]
        self.spawns = random.choice(spawn_sets)
        # [v2] spawn_points: 루트 적을 놓을 자리 [x, y, 'air|ground']. 적 종류는 루트 노드가 정한다
        self.spawn_points = [tuple(p) for p in data.get('spawn_points', [])]
        self.player_start = tuple(data['player_start'])
        # safe_points: 환경 피해 뒤 돌아올 지점 [x, y] (6.8, 12.5). 없으면 플레이어가 오래 서 있던 바닥
        self.safe_points = [tuple(p) for p in data.get('safe_points', [])]
        self.door = Door(*data['door'])
        # [v2] doors: 여러 문 위치 (안전지대는 루트 문 3개). 없으면 door 하나만 쓴다
        self.doors = [Door(*p) for p in data['doors']] if 'doors' in data else [self.door]
        # [v2] chest_spot: 이 방에 보물상자가 배정되면 놓일 자리 (없으면 상자를 놓지 않는다)
        self.chest_spot = tuple(data['chest_spot']) if 'chest_spot' in data else None

    def place(self, kinds):
        # 공중 적은 air 자리, 나머지는 ground 자리에 무작위로 놓는다. 한쪽 자리가 모자라면 다른 쪽을 쓴다
        air = [(x, y) for x, y, kind in self.spawn_points if kind == 'air']
        ground = [(x, y) for x, y, kind in self.spawn_points if kind != 'air']
        random.shuffle(air)
        random.shuffle(ground)
        spawns = []
        for kind in kinds:
            pool = air if kind in config.AIR_ENEMIES else ground
            pool = pool or air or ground
            if not pool:
                break
            spawns.append((kind, *pool.pop()))
        return spawns

    def spawn_enemies(self, player, kinds=None):
        # kinds가 없으면 템플릿의 spawns(보스방 등)를 그대로 쓴다
        spawns = self.spawns if kinds is None else self.place(kinds)
        return [ENEMY_TYPES[kind](x, y, player, self.platforms) for kind, x, y in spawns]
