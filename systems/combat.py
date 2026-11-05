import config
import game_world
from objects import effect

# 공격 hitbox와 몸 hitbox의 판정. 적 공격이 닿으면 패링 성공/피격으로 분기한다


def resolve(player, enemies, gimmicks=()):
    attack_bb = player.get_attack_bb()
    if attack_bb:
        hit_gimmicks(player, attack_bb, gimmicks)
        for e in enemies:
            if not e.is_alive() or e in player.attack_hits:
                continue
            if game_world.overlap(attack_bb, e.get_bb()):
                player.attack_hits.add(e)
                x, y = contact_point(attack_bb, e.get_bb())
                strong = player.on_attack_hit()   # 반동·포고·세 번째 일격 (휘두름당 1번)
                if e.kind == 'statue':
                    effect.statue_spark(x, y)       # 연습 석상은 회색 스파크만 (5.4)
                    continue
                e.take_damage(player.attack_damage(), player.attack_knockback(e))
                effect.attack_hit(x, y, player.attack_angle(), strong, not e.is_alive())

    body_bb = player.get_bb()
    for e in enemies:
        if not e.is_alive() or e.attack_hit:
            continue
        enemy_bb = e.get_attack_bb()
        if enemy_bb and game_world.overlap(enemy_bb, body_bb):
            if player.is_parrying() and e.attack.parryable:
                # 패링 성공 (무적 중이어도 패링이 우선)
                e.attack_hit = True
                player.on_parry_success(e)
                e.on_parried()
                effect.parry_success(*contact_point(enemy_bb, body_bb))
            elif e.attack_damage() > 0:
                # 무적이라 피해가 없었으면 판정 구간이 남아 있는 동안 다시 검사한다 (피해 0 = 연습 석상은 맞아도 무시)
                e.attack_hit = player.take_hit(e.attack_damage(), e.x)
                if e.attack_hit:
                    effect.player_hit(player.x, player.y + config.PLAYER_H / 2)

    # 몸 접촉 피해 (6.8). 공격 판정 뒤에 본다 (같은 프레임에 공격에 맞았으면 무적이라 무시됨)
    for e in enemies:
        if e.is_alive() and e.deals_contact() and game_world.overlap(e.get_bb(), body_bb):
            if player.take_hit(config.CONTACT_DAMAGE, e.x):
                effect.player_hit(player.x, player.y + config.PLAYER_H / 2)


def hit_gimmicks(player, attack_bb, gimmicks):
    # 곡괭이가 벽·문·레버·가시에 닿음 (5.4). 대상마다 휘두름당 1번, 맞은 대상은 적과 똑같이 반동·포고
    for g in gimmicks:
        if g in player.attack_hits or not game_world.overlap(attack_bb, g.get_bb()):
            continue
        player.attack_hits.add(g)
        if g.on_pickaxe_hit(player):
            player.on_attack_hit()
            effect.attack_hit(*contact_point(attack_bb, g.get_bb()), player.attack_angle(), False, False)


def projectile_hit(player, p):
    # 투사체가 플레이어 몸에 닿았을 때. 무적(대시 등)이면 그대로 지나간다
    if player.is_parrying() and p.parryable:
        player.on_parry_success(p)
        effect.parry_success(*contact_point(p.get_bb(), player.get_bb()))
        # 반사 해금 전에는 튕겨 사라지고, 해금 후에는 되돌아간다 (9.3). 자세는 반사탄이 맞을 때 쌓인다
        if player.can('reflect'):
            p.on_parried(player, player.reflect_damage_mult)
        else:
            p.on_blocked()
    # 밀려나는 방향은 투사체 진행 방향을 따른다
    elif player.take_hit(p.damage, player.x - p.dir_x):
        effect.player_hit(player.x, player.y + config.PLAYER_H / 2)
        p.destroy()


def contact_point(bb_a, bb_b):
    # 겹친 영역의 중심
    l, b = max(bb_a[0], bb_b[0]), max(bb_a[1], bb_b[1])
    r, t = min(bb_a[2], bb_b[2]), min(bb_a[3], bb_b[3])
    return (l + r) / 2, (b + t) / 2
