# 플레이어와 적이 함께 쓰는 지형 충돌. x, y는 발 중심 좌표, w, h는 몸 크기


def overlaps_x(x, w, p):
    half_w = w / 2
    return x + half_w > p.left and x - half_w < p.right


def resolve_x(x, y, w, h, platforms):
    half_w = w / 2
    for p in platforms:
        if p.kind != 'solid' or not overlaps_x(x, w, p):
            continue
        if y + h <= p.bottom or y >= p.top:
            continue
        # 블록 중심 기준으로 가까운 쪽으로 밀어낸다 (끼임 방지)
        if x < (p.left + p.right) / 2:
            x = p.left - half_w
        else:
            x = p.right + half_w
    return x


def body_blocked(x, y, w, h, platforms):
    # (x, y) 자리에 몸을 두면 solid와 겹치는가
    for p in platforms:
        if p.kind == 'solid' and overlaps_x(x, w, p) and y + h > p.bottom and y < p.top:
            return True
    return False


def corner_correct(x, prev_y, y, w, h, platforms, max_px):
    # 상승 중 머리가 천장 모서리에 max_px 이내로만 걸리면 옆으로 밀어 통과시킨 x를 돌려준다 (6.4)
    # 밀 곳이 막혀 있거나 더 깊게 걸렸으면 x 그대로
    half_w = w / 2
    for p in platforms:
        if p.kind != 'solid' or not overlaps_x(x, w, p):
            continue
        if not (prev_y + h <= p.bottom < y + h):
            continue
        if x + half_w - p.left <= max_px:
            new_x = p.left - half_w
        elif p.right - (x - half_w) <= max_px:
            new_x = p.right + half_w
        else:
            return x
        if body_blocked(new_x, y, w, h, platforms):
            return x
        return new_x
    return x


def resolve_y(x, prev_y, y, vy, w, h, platforms):
    # 이동 전후 구간으로 판정해서 빠르게 떨어질 때 얇은 발판을 뚫지 않게 한다
    # 반환: (y, vy, on_ground)
    on_ground = False
    for p in platforms:
        # kind가 None이면 부서진 벽·열린 문 (objects/breakable.py, gate.py)
        if p.kind is None or not overlaps_x(x, w, p):
            continue
        if vy <= 0 and prev_y >= p.top and y <= p.top:
            # 착지: solid, oneway 모두 위에서 떨어질 때만
            y = p.top
            vy = 0
            on_ground = True
        elif p.kind == 'solid' and vy > 0:
            prev_head = prev_y + h
            head = y + h
            if prev_head <= p.bottom and head > p.bottom:
                y = p.bottom - h
                vy = 0
    return y, vy, on_ground
