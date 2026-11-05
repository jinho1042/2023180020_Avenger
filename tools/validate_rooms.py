# 방 JSON 검사 (12.5). 방 JSON을 추가·수정한 작업은 끝나기 전에 오류 0을 확인한다 (0장 13번)
# 실행: python tools/validate_rooms.py [방 폴더]   (기본 data/rooms, 하위 폴더 포함)
# 오류가 하나라도 있으면 종료 코드 1. 경고는 통과한다
# 미작성 처리: 없는 방으로 가는 출구, 방 수가 12.2 표(config.REGIONS rooms)에 못 미친 구역에 걸린 검사는 경고

import json
import os
import sys
from collections import deque

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
import config  # noqa: E402

ROOM_DIR = os.path.join(ROOT, 'data', 'rooms')
ITEMS_PATH = os.path.join(ROOT, 'data', 'items.json')
COLLECTIBLE_STRICT = False   # T61에서 True (수집품 개수 검사 경고 → 오류)
OPPOSITE = dict(left='right', right='left', up='down', down='up')
# 전역에서 겹치면 안 되는 id (세이브에 방 id 없이 저장된다, 13.6 collected·miners_rescued)
GLOBAL_ID_OBJECTS = ('item', 'miner', 'carver')

errors = []
warnings = []


def error(room_id, msg):
    errors.append(f'[오류] {room_id}: {msg}')


def warn(room_id, msg):
    warnings.append(f'[경고] {room_id}: {msg}')


def report(strict, room_id, msg):
    (error if strict else warn)(room_id, msg)


def load_rooms(folder):
    rooms = {}
    for path, _, files in os.walk(folder):
        for name in sorted(files):
            if not name.endswith('.json'):
                continue
            with open(os.path.join(path, name), encoding='utf-8') as f:
                data = json.load(f)
            if 'id' not in data:
                continue  # [v2] 템플릿 (id 대신 name, 출구 없음). T42·T45에서 정리
            if data['id'] != name[:-len('.json')]:
                error(data['id'], f'파일 이름({name})과 id가 다름')
            if data['id'] in rooms:
                error(data['id'], '같은 id의 방 파일이 둘 이상')
            rooms[data['id']] = data
    return rooms


def room_size(data):
    w, h = data.get('size', (1, 1))
    return w * config.SCREEN_W, h * config.SCREEN_H


def exit_side(e, data):
    # objects/exit_zone.py와 같은 규칙 (그쪽은 pico2d를 불러오므로 여기서 다시 계산)
    x, y, w, h = e['rect']
    room_w, room_h = room_size(data)
    if w <= h:
        return 'left' if x + w / 2 < room_w / 2 else 'right'
    return 'down' if y + h / 2 < room_h / 2 else 'up'


def object_id(obj):
    # objects 항목의 id. 정예는 ["elite", x, y, 종류, id], 나머지는 [종류, x, y, id]
    if obj[0] == 'elite':
        return obj[4] if len(obj) > 4 else None
    return obj[3] if len(obj) > 3 else None


def neighbors(room_id, rooms):
    # 출구로 바로 이어진 방 (양방향, 있는 방만)
    result = set()
    for e in rooms[room_id].get('exits', []):
        if e['to'] in rooms:
            result.add(e['to'])
    for other_id, other in rooms.items():
        if any(e['to'] == room_id for e in other.get('exits', [])):
            result.add(other_id)
    return result


def check_exits(rooms):
    for room_id, data in rooms.items():
        for e in data.get('exits', []):
            if e['to'] not in rooms:
                warn(room_id, f"미작성 출구 {e['id']} → {e['to']}")
                continue
            target = rooms[e['to']]
            back = next((t for t in target.get('exits', []) if t['id'] == e['to_exit']), None)
            if back is None:
                error(room_id, f"출구 {e['id']}: {e['to']}에 출구 {e['to_exit']}가 없음")
                continue
            if back['to'] != room_id or back['to_exit'] != e['id']:
                error(room_id, f"출구 짝이 맞지 않음: {e['id']} → {e['to']}:{e['to_exit']}, "
                               f"되돌아오는 출구는 → {back['to']}:{back['to_exit']}")
            side, back_side = exit_side(e, data), exit_side(back, target)
            if OPPOSITE[side] != back_side:
                error(room_id, f"출구 방향이 반대가 아님: {e['id']}({side}) ↔ {e['to']}:{back['id']}({back_side})")
            elif side == 'down':
                check_landing(e['to'], target, back)


def check_landing(room_id, data, exit_data):
    # 아래 출구로 떨어져 들어온 방: 도착 출구 아래에 받쳐 줄 발판이 있어야 한다
    x, y, w, h = exit_data['rect']
    for px, py, pw, ph, _ in data['platforms']:
        if px < x + w and x < px + pw and py + ph <= y:
            return
    error(room_id, f"출구 {exit_data['id']}로 떨어져 들어온 자리 아래에 발판이 없음")


def check_room(room_id, data, items, global_ids):
    room_w, room_h = room_size(data)
    if data.get('region') not in config.REGIONS:
        error(room_id, f"알 수 없는 구역 {data.get('region')}")
    # 영구 id: 방 안에서 겹치면 안 됨. seat는 같은 id의 safe_zones와 짝이므로 따로 본다
    local = []
    local += [b[5] for b in data.get('breakables', [])]
    local += [g[5] for g in data.get('gates', [])]
    local += [s[3] for s in data.get('switches', [])]
    local += [z[4] for z in data.get('safe_zones', [])]
    local += [v[2] for v in data.get('air_vents', [])]
    local += [t[5] for t in data.get('triggers', [])]
    objects = data.get('objects', [])
    for obj in objects:
        oid = object_id(obj)
        if obj[0] in GLOBAL_ID_OBJECTS:
            if oid in global_ids:
                error(room_id, f"{obj[0]} id {oid}가 {global_ids[oid]} 방과 겹침")
            global_ids[oid] = room_id
        elif obj[0] not in ('seat', 'npc') and oid is not None:
            local.append(oid)
    for oid in sorted({i for i in local if local.count(i) > 1}):
        error(room_id, f'영구 id {oid} 중복')
    # 앉는 자리마다 같은 id의 안전지대
    zone_ids = {z[4] for z in data.get('safe_zones', [])}
    for obj in objects:
        if obj[0] == 'seat' and obj[3] not in zone_ids:
            error(room_id, f"앉는 자리 {obj[3]}에 같은 id의 safe_zones가 없음")
        if obj[0] == 'item' and items is not None and obj[3] not in items:
            error(room_id, f"아이템 {obj[3]}가 items.json에 없음")
    # 숨 게이트: 방 전체를 덮고, 요구 레벨 1~숨의 룬 최대
    for x, y, w, h, gate_id, need_lv in data.get('breath_gates', []):
        if x > 0 or y > 0 or x + w < room_w or y + h < room_h:
            error(room_id, f'숨 게이트 {gate_id}가 방 전체({room_w}×{room_h})를 덮지 않음')
        if not isinstance(need_lv, int) or not 1 <= need_lv <= config.RUNE_MAX_LEVEL['breath']:
            error(room_id, f'숨 게이트 {gate_id} 요구 레벨 {need_lv}이 1~{config.RUNE_MAX_LEVEL["breath"]} 밖')
    # 한쪽 문은 열리는 쪽(open_from)이 있어야 한다. 허브행 숏컷(to_hub)도 한쪽 문이어야 한다
    for g in data.get('gates', []):
        attrs = g[6] if len(g) > 6 else {}
        if g[4] == 'one_way' and attrs.get('open_from') not in OPPOSITE:
            error(room_id, f'한쪽 문 {g[5]}에 open_from(left|right|up|down)이 없음')
        if attrs.get('to_hub') and g[4] != 'one_way':
            error(room_id, f'허브행 숏컷 {g[5]}이 한쪽 문(one_way)이 아님')


def check_map_cells(rooms):
    owner = {}
    for room_id, data in sorted(rooms.items()):
        cx, cy = data.get('map_cell', (0, 0))
        w, h = data.get('size', (1, 1))
        for i in range(w):
            for j in range(h):
                key = (data.get('region'), cx + i, cy + j)
                if key in owner:
                    error(room_id, f'map_cell {key[1:]} 칸이 {owner[key]}와 겹침')
                owner[key] = room_id


def is_gate_room(data):
    return bool(data.get('breath_gates'))


def check_bosses(rooms):
    for room_id, data in rooms.items():
        if not data.get('boss'):
            continue
        # 11.2: 보스 종류, 등장 트리거(arena), 출구를 막는 아레나 문, spawns의 보스 자리
        boss = data['boss']
        if boss not in config.BOSS_NAME:
            error(room_id, f'알 수 없는 보스 종류 {boss}')
        if not any(t[4] == 'arena' for t in data.get('triggers', [])):
            error(room_id, '보스방에 아레나 트리거(triggers의 "arena")가 없음')
        if not any(g[4] == 'arena' for g in data.get('gates', [])):
            error(room_id, '보스방에 아레나 문(gates의 "arena")이 없음')
        if not any(s[0] == boss for s in data.get('spawns', [])):
            error(room_id, f'spawns에 보스 자리({boss})가 없음')
        before =[n for n in neighbors(room_id, rooms) if not rooms[n].get('boss')]
        if not before:
            warn(room_id, '보스방 앞 방이 아직 없음')
        elif not any(rooms[n].get('safe_zones') for n in before):
            error(room_id, f'보스방 바로 앞 방({", ".join(sorted(before))})에 안전지대가 없음')


def region_rooms(rooms, region):
    return [r for r, d in rooms.items() if d.get('region') == region]


def check_regions(rooms, items):
    scope_regions = config.SCOPE_REGIONS[config.SCOPE]
    complete = {}
    for region in scope_regions:
        count = len(region_rooms(rooms, region))
        complete[region] = count >= config.REGIONS[region]['rooms']
        if count == 0:
            print(f"[미작성] {region} ({config.REGIONS[region]['name']})")
        elif not complete[region]:
            warn(region, f"방 {count}/{config.REGIONS[region]['rooms']} — 구역 검사는 경고만")
    for room_id, data in rooms.items():
        region = data.get('region')
        if region in config.REGIONS and region != 'test' and region not in scope_regions:
            warn(room_id, f'SCOPE {config.SCOPE}에 없는 구역 {region}')
    check_carver_hub(rooms, complete)
    check_hub_shortcuts(rooms, complete, scope_regions)
    check_safe_distance(rooms, complete, scope_regions)
    check_collectibles(rooms, complete, items)


def check_carver_hub(rooms, complete):
    # 새김터·허브는 R1(corridor)에 걸린 검사. R1 방이 없으면 미작성
    if not region_rooms(rooms, 'corridor'):
        return
    strict = complete['corridor']
    carvers = [r for r, d in rooms.items() for o in d.get('objects', []) if o[0] == 'carver']
    hubs = [r for r, d in rooms.items() if d.get('hub')]
    if len(carvers) != 1:
        report(strict, 'corridor', f'새김터(carver)가 전체에 {len(carvers)}개 (정확히 1개)')
    if len(hubs) != 1:
        report(strict, 'corridor', f'hub: true 방이 전체에 {len(hubs)}개 (정확히 1개)')
    if len(carvers) == 1 and len(hubs) == 1 and hubs[0] not in neighbors(carvers[0], rooms):
        report(strict, carvers[0], f'새김터 방이 허브 방({hubs[0]})과 출구로 바로 이어져 있지 않음')


def check_hub_shortcuts(rooms, complete, scope_regions):
    for region in config.HUB_SHORTCUT_REGIONS:
        if region not in scope_regions or not region_rooms(rooms, region):
            continue
        found = any(g[4] == 'one_way' and len(g) > 6 and g[6].get('to_hub')
                    for r in region_rooms(rooms, region) for g in rooms[r].get('gates', []))
        if not found:
            report(complete[region], region, 'R1 허브행 숏컷(to_hub: true인 one_way 문)이 없음')


def check_safe_distance(rooms, complete, scope_regions):
    # 방 그래프 거리. 게이트 방·보스 아레나·숨이 없는 구역(광산)·테스트 방은 계산에서 뺀다
    def counted(room_id):
        data = rooms[room_id]
        region = data.get('region')
        return (region in scope_regions and config.REGIONS[region]['air'] is not None
                and not is_gate_room(data) and not data.get('boss'))
    nodes = [r for r in rooms if counted(r)]
    dist = {r: 0 for r in nodes if rooms[r].get('safe_zones')}
    queue = deque(dist)
    while queue:
        room_id = queue.popleft()
        for n in neighbors(room_id, rooms):
            if counted(n) and n not in dist:
                dist[n] = dist[room_id] + 1
                queue.append(n)
    for room_id in sorted(nodes):
        d = dist.get(room_id)
        if d is None or d > config.SAFE_ZONE_MAX_ROOMS:
            text = '닿는 안전지대 없음' if d is None else f'{d}방'
            report(complete[rooms[room_id]['region']], room_id,
                   f'가장 가까운 안전지대까지 {text} (최대 {config.SAFE_ZONE_MAX_ROOMS}방)')


def collectible_kind(obj, items):
    # 수집품 종류. items.json이 있으면 그 kind, 없으면 id 접두어로 짐작
    if obj[0] in ('miner', 'tablet'):
        return obj[0]
    if obj[0] != 'item':
        return None
    item_id = obj[3]
    if items is not None and item_id in items:
        return items[item_id].get('kind')
    if item_id.startswith('rare_ore'):
        return 'rare_ore'
    if item_id.startswith('map_stone'):
        return 'map_stone'
    return None


def count_ore_veins(rooms, region):
    # 광맥벽(breakables 'ore_vein')도 희귀 광석 1개로 센다 (12.7 '구역별 3개 중 1개는 광맥벽', T64)
    # 최소판은 곡괭이 Lv1 고정이라 방에 만들지 않으므로(room.py) 세지 않는다
    if config.SCOPE == 'minimum':
        return 0
    return sum(1 for r in region_rooms(rooms, region) for b in rooms[r].get('breakables', []) if b[4] == 'ore_vein')


def check_collectibles(rooms, complete, items):
    table = config.COLLECTIBLE_COUNTS[config.SCOPE]
    for kind, per_region in table.items():
        for region, need in per_region.items():
            if not region_rooms(rooms, region):
                continue
            have = sum(1 for r in region_rooms(rooms, region) for o in rooms[r].get('objects', [])
                       if collectible_kind(o, items) == kind)
            if kind == 'rare_ore':
                have += count_ore_veins(rooms, region)
            if have != need:
                report(COLLECTIBLE_STRICT and complete[region], region, f'{kind} {have}개 (12.7 표 {need}개)')


def load_items():
    if not os.path.exists(ITEMS_PATH):
        return None
    with open(ITEMS_PATH, encoding='utf-8') as f:
        return json.load(f)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else ROOM_DIR
    rooms = load_rooms(folder)
    items = load_items()
    if items is None:
        warn('items.json', '파일 없음 → 아이템 id 검사 생략 (T44)')
    global_ids = {}
    for room_id, data in sorted(rooms.items()):
        check_room(room_id, data, items, global_ids)
    check_exits(rooms)
    check_map_cells(rooms)
    check_bosses(rooms)
    check_regions(rooms, items)
    for line in warnings + errors:
        print(line)
    print(f'방 {len(rooms)}개 (SCOPE {config.SCOPE}) — 오류 {len(errors)}, 경고 {len(warnings)}')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
