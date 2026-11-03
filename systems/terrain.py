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


def resolve_y(x, prev_y, y, vy, w, h, platforms):
    # 이동 전후 구간으로 판정해서 빠르게 떨어질 때 얇은 발판을 뚫지 않게 한다
    # 반환: (y, vy, on_ground)
    on_ground = False
    for p in platforms:
        if not overlaps_x(x, w, p):
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
