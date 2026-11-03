import json
import os
import random

from objects.boss_greatsword import BossGreatsword
from objects.boss_twinblade import BossTwinblade
from objects.door import Door
from objects.enemy_archer import EnemyArcher
from objects.enemy_flyer import EnemyFlyer
from objects.enemy_melee import EnemyMelee
from objects.platform import Platform

ROOM_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'rooms')
# spawns의 이름 → 적 클래스
ENEMY_TYPES = {'melee': EnemyMelee, 'flyer': EnemyFlyer, 'archer': EnemyArcher,
               'greatsword': BossGreatsword, 'twinblade': BossTwinblade}


class Room:
    # 방 템플릿 JSON 하나를 읽어 지형 객체와 배치 정보를 보관한다
    def __init__(self, name):
        path = os.path.join(ROOM_DIR, name + '.json')
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.name = data['name']
        self.type = data['type']
        self.platforms = [Platform(*p) for p in data['platforms']]
        # spawn_sets(적 배치 세트 여러 개) 중 하나를 무작위로 고른다. 세트가 하나뿐이면 spawns로 써도 된다
        spawn_sets = data.get('spawn_sets') or [data.get('spawns', [])]
        self.spawns = random.choice(spawn_sets)
        self.player_start = tuple(data['player_start'])
        self.door = Door(*data['door'])

    def spawn_enemies(self, player):
        return [ENEMY_TYPES[kind](x, y, player, self.platforms) for kind, x, y in self.spawns]
