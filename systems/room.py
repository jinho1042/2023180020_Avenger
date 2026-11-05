import json
import random

import config
from objects.boss_greatsword import BossGreatsword
from objects.boss_mage import BossMage
from objects.boss_twinblade import BossTwinblade
from objects.enemy_adept_mage import EnemyAdeptMage
from objects.enemy_apprentice_mage import EnemyApprenticeMage
from objects.enemy_archer import EnemyArcher
from objects.enemy_assassin import EnemyAssassin
from objects.enemy_dual_dagger import EnemyDualDagger
from objects.enemy_flyer import EnemyFlyer
from objects.enemy_melee import EnemyMelee
from objects.exit_zone import ExitZone
from objects.platform import Platform

# spawns의 이름 → 적 클래스
ENEMY_TYPES = {'melee': EnemyMelee, 'flyer': EnemyFlyer, 'archer': EnemyArcher,
               'apprentice_mage': EnemyApprenticeMage, 'adept_mage': EnemyAdeptMage,
               'dual_dagger': EnemyDualDagger, 'assassin': EnemyAssassin,
               'greatsword': BossGreatsword, 'mage': BossMage, 'twinblade': BossTwinblade}


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
        # 나머지 12.5 필드. 객체로 만드는 것은 각 기믹 작업에서 (T35~). 지금은 배치 정보만 보관한다
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

    def exit(self, exit_id):
        return next(e for e in self.exits if e.id == exit_id)

    def spawn_enemies(self, player):
        return [ENEMY_TYPES[kind](x, y, player, self.platforms) for kind, x, y in self.spawns]
