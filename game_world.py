import config
from systems import camera

world = [[] for _ in range(config.LAYER_COUNT)]
# 현재 방 크기 (월드 좌표, 방 좌하단 = (0, 0)). 방을 불러올 때 play_mode가 정한다
room_w, room_h = config.SCREEN_W, config.SCREEN_H
collision_pairs = {}   # group -> [a 리스트, b 리스트]
_pending_removal = []
show_hitbox = False    # F1로 토글, 켜지면 객체가 hitbox 외곽선을 그린다


def add_object(o, depth):
    world[depth].append(o)


def add_objects(ol, depth):
    world[depth] += ol


def remove_object(o):
    # 순회 중 제거를 피하려고 모았다가 update 끝에 제거
    _pending_removal.append(o)


def _flush_removal():
    for o in _pending_removal:
        for layer in world:
            if o in layer:
                layer.remove(o)
                break
        for pairs in collision_pairs.values():
            if o in pairs[0]:
                pairs[0].remove(o)
            if o in pairs[1]:
                pairs[1].remove(o)
    _pending_removal.clear()


def update():
    for layer in world:
        for o in layer:
            o.update()
    _flush_removal()


def update_layer(depth):
    # 히트스톱 중 이펙트만 갱신할 때 쓴다
    for o in world[depth]:
        o.update()
    _flush_removal()


def set_room_size(w, h):
    global room_w, room_h
    room_w, room_h = w, h


def render():
    # get_bb가 있는 객체(월드 객체)는 화면 밖이면 건너뛴다. 화면 전체 연출은 get_bb가 없다
    for layer in world:
        for o in layer:
            if hasattr(o, 'get_bb') and not camera.visible(o.get_bb()):
                continue
            o.draw()


def add_collision_pair(group, a, b):
    if group not in collision_pairs:
        collision_pairs[group] = [[], []]
    if a:
        collision_pairs[group][0].append(a)
    if b:
        collision_pairs[group][1].append(b)


def overlap(bb_a, bb_b):
    la, ba, ra, ta = bb_a
    lb, bb, rb, tb = bb_b
    if la > rb or ra < lb or ta < bb or ba > tb:
        return False
    return True


def collide(a, b):
    return overlap(a.get_bb(), b.get_bb())


def handle_collisions():
    for group, pairs in collision_pairs.items():
        for a in pairs[0]:
            for b in pairs[1]:
                if collide(a, b):
                    a.handle_collision(group, b)
                    b.handle_collision(group, a)
    _flush_removal()


def clear():
    for layer in world:
        layer.clear()
    collision_pairs.clear()
    _pending_removal.clear()
