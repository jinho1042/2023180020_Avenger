# Tiled 맵(JSON 내보내기, .tmj/.json) → 방 JSON (12.5)
# 실행: python tools/tiled_to_room.py <맵 파일> [출력 폴더]   (기본 data/rooms/<region>/<id>.json)
#
# Tiled 쪽 규칙 (12.5)
# - 맵 크기는 화면(1280×720)의 배수. 맵 속성: id(없으면 파일 이름), region, map_cell("x,y"), music, air, hub, boss
# - 오브젝트 레이어 이름 = 방 JSON 필드 이름. 사각형 오브젝트는 [x, y, w, h, ...], 점 오브젝트는 [x, y, ...]
# - 사용자 속성: id, to, to_exit, kind, open_from, to_hub, need_lv. kind가 없으면 오브젝트의 class(type)를 쓴다
#   exits: id·to·to_exit / switches: to = 여는 gate id / objects: 정예는 kind "elite" + 오브젝트 name = 적 종류
# - Tiled는 y가 아래로 늘고 사각형의 y가 위쪽 모서리다. 여기서 방 좌표(좌하단 원점, y 위로)로 뒤집는다

import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
import config  # noqa: E402

ROOM_DIR = os.path.join(ROOT, 'data', 'rooms')
RECT_FIELDS = ('platforms', 'hazards', 'water', 'breath_zones', 'breath_gates', 'safe_zones',
               'breakables', 'gates', 'exits', 'triggers')
POINT_FIELDS = ('air_vents', 'switches', 'spawns', 'objects', 'safe_points')
DEFAULT_KIND = dict(platforms='solid')


def props(obj):
    # Tiled 1.x 속성 목록 [{name, type, value}] → dict (옛 형식 dict도 받는다)
    raw = obj.get('properties', [])
    if isinstance(raw, dict):
        return dict(raw)
    return {p['name']: p['value'] for p in raw}


def kind_of(obj, field):
    p = props(obj)
    return p.get('kind') or obj.get('class') or obj.get('type') or DEFAULT_KIND.get(field)


def rect_entry(field, obj, map_h):
    p = props(obj)
    x, w, h = round(obj['x']), round(obj['width']), round(obj['height'])
    y = round(map_h - obj['y'] - obj['height'])
    if field == 'exits':
        return {'id': p['id'], 'rect': [x, y, w, h], 'to': p['to'], 'to_exit': p['to_exit']}
    if field == 'water':
        return [x, y, w, h]
    if field == 'breath_gates':
        return [x, y, w, h, p['id'], int(p['need_lv'])]
    if field == 'safe_zones':
        return [x, y, w, h, p['id']]
    if field in ('platforms', 'hazards', 'breath_zones'):
        return [x, y, w, h, kind_of(obj, field)]
    entry = [x, y, w, h, kind_of(obj, field), p['id']]   # breakables, gates, triggers(kind = 스크립트 이름)
    if field == 'gates':
        attrs = {k: p[k] for k in ('open_from', 'to_hub') if k in p}
        if attrs:
            entry.append(attrs)
    return entry


def point_entry(field, obj, map_h):
    p = props(obj)
    x, y = round(obj['x']), round(map_h - obj['y'])
    if field == 'safe_points':
        return [x, y]
    if field == 'air_vents':
        return [x, y, p['id']]
    if field == 'switches':
        return [x, y, kind_of(obj, field), p['id'], p['to']]
    if field == 'spawns':
        return [kind_of(obj, field), x, y]
    kind = kind_of(obj, field)   # objects
    if kind == 'elite':
        return ['elite', x, y, obj['name'], p['id']]
    return [kind, x, y, p['id']] if 'id' in p else [kind, x, y]


def convert(path):
    with open(path, encoding='utf-8') as f:
        tmap = json.load(f)
    map_w = tmap['width'] * tmap['tilewidth']
    map_h = tmap['height'] * tmap['tileheight']
    if map_w % config.SCREEN_W or map_h % config.SCREEN_H:
        raise ValueError(f'맵 크기 {map_w}×{map_h}가 화면({config.SCREEN_W}×{config.SCREEN_H})의 배수가 아님')
    mp = props(tmap)
    room_id = mp.get('id') or os.path.splitext(os.path.basename(path))[0]
    cell = [int(v) for v in str(mp.get('map_cell', '0,0')).split(',')]
    room = {
        'id': room_id, 'region': mp['region'],
        'size': [map_w // config.SCREEN_W, map_h // config.SCREEN_H], 'map_cell': cell,
        'music': mp.get('music') or None, 'air': mp.get('air') or None, 'hub': bool(mp.get('hub', False)),
    }
    for field in RECT_FIELDS + POINT_FIELDS:
        room[field] = []
    for layer in tmap['layers']:
        field = layer['name']
        if layer['type'] != 'objectgroup':
            continue
        if field not in room:
            print(f'[경고] 알 수 없는 레이어 {field} — 건너뜀')
            continue
        for obj in layer['objects']:
            if field in POINT_FIELDS:
                room[field].append(point_entry(field, obj, map_h))
            else:
                room[field].append(rect_entry(field, obj, map_h))
    room['boss'] = mp.get('boss') or None
    return room


def write_room(room, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, room['id'] + '.json')
    # 한 항목을 한 줄로 써서 사람이 읽고 고치기 쉽게 한다
    lines = ['{']
    keys = list(room)
    for i, key in enumerate(keys):
        comma = ',' if i < len(keys) - 1 else ''
        value = room[key]
        if isinstance(value, list) and value and isinstance(value[0], (list, dict)):
            items = [json.dumps(v, ensure_ascii=False) for v in value]
            lines.append(f'  "{key}": [\n    ' + ',\n    '.join(items) + f'\n  ]{comma}')
        else:
            lines.append(f'  "{key}": {json.dumps(value, ensure_ascii=False)}{comma}')
    lines.append('}')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out


def main():
    if len(sys.argv) < 2:
        print('사용법: python tools/tiled_to_room.py <맵 파일> [출력 폴더]')
        sys.exit(1)
    room = convert(sys.argv[1])
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOM_DIR, room['region'])
    print(f'변환: {sys.argv[1]} → {write_room(room, out_dir)}')


if __name__ == '__main__':
    main()
