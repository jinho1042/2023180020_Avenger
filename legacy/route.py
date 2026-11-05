import random

import config


def _enemy_count(name, layer):
    # 1층은 최소값, 마지막 층은 최대값. 그 사이는 층 깊이에 비례
    lo, hi = config.ROUTE_DIFFICULTY[name]['enemy_count']
    if config.ROUTE_LAYERS == 1:
        return lo
    return lo + round((hi - lo) * layer / (config.ROUTE_LAYERS - 1))


def _node(template, enemies=None):
    # enemies가 None이면 템플릿의 spawns를 그대로 쓴다 (보스방)
    return dict(template=template, enemies=enemies, has_chest=False, cleared=False)


def generate(name):
    # 루트 = 층 목록. 1층 노드 1개, 2층부터 ROUTE_BRANCH개, 마지막은 보스 노드. 루트 안에서 템플릿 중복 없음
    sizes = [1] + [config.ROUTE_BRANCH] * (config.ROUTE_LAYERS - 1)
    templates = random.sample(config.ROOM_TEMPLATES, sum(sizes))
    kinds = config.ROUTE_ENEMIES[name]
    layers = []
    for layer, size in enumerate(sizes):
        count = _enemy_count(name, layer)
        layers.append([_node(templates.pop(), [random.choice(kinds) for _ in range(count)])
                       for _ in range(size)])
    layers.append([_node(config.ROUTE_BOSS_ROOM[name])])
    _place_chests(layers)
    return layers


def _place_chests(layers):
    # 첫 상자는 항상 1층 방(어느 길로 가도 하나는 얻도록), 나머지는 2층~마지막 전투층 노드 중 무작위
    count = random.randint(*config.CHESTS_PER_ROUTE)
    if count <= 0:
        return
    layers[0][0]['has_chest'] = True
    rest = [node for layer in layers[1:config.ROUTE_LAYERS] for node in layer]
    for node in random.sample(rest, min(len(rest), count - 1)):
        node['has_chest'] = True


def new_run_state():
    # 런 시작 시 세 루트를 모두 미리 만든다. route가 None이면 안전지대
    return dict(routes={name: generate(name) for name in config.ROUTE_ORDER},
                cleared=[], route=None, layer=0, node=0, rooms_entered=0)


def total_rooms():
    return len(config.ROUTE_ORDER) * (config.ROUTE_LAYERS + 1)


def current_node(state):
    return state['routes'][state['route']][state['layer']][state['node']]


def is_boss_layer(state):
    return state['layer'] == config.ROUTE_LAYERS


def next_nodes(state):
    # 이 방의 문이 이어지는 노드들 (i번째 문 → i번째 노드). 보스방이면 빈 목록 (안전지대로 간다)
    if is_boss_layer(state):
        return []
    return state['routes'][state['route']][state['layer'] + 1]


def exit_count(state):
    # 방을 클리어하면 열릴 문 수 = 다음 층 노드 수. 보스방이면 안전지대로 돌아가는 문 1개
    if is_boss_layer(state):
        return 1
    return len(state['routes'][state['route']][state['layer'] + 1])
