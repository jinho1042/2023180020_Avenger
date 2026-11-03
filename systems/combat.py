import config
import game_world
from objects import effect

# 공격 hitbox와 몸 hitbox의 판정. 적 공격이 닿으면 패링 성공/피격으로 분기한다


def resolve(player, enemies):
    attack_bb = player.get_attack_bb()
    if attack_bb:
        for e in enemies:
            if not e.is_alive() or e in player.attack_hits:
                continue
            if game_world.overlap(attack_bb, e.get_bb()):
                player.attack_hits.add(e)
                e.take_damage(player.attack_damage(), player.face_dir * player.attack_knockback())

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
            else:
                # 무적이라 피해가 없었으면 판정 구간이 남아 있는 동안 다시 검사한다
                e.attack_hit = player.take_hit(e.attack.damage, e.x)
                if e.attack_hit:
                    effect.player_hit(player.x, player.y + config.PLAYER_H / 2)

    # 몸끼리 겹쳐도 피해. 연속 피해는 피격 무적이 막는다
    for e in enemies:
        if e.deals_contact_damage() and game_world.overlap(e.get_bb(), body_bb):
            if player.take_hit(config.CONTACT_DAMAGE, e.x):
                effect.player_hit(player.x, player.y + config.PLAYER_H / 2)
            break


def projectile_hit(player, p):
    # 투사체가 플레이어 몸에 닿았을 때. 무적(대시 등)이면 그대로 지나간다
    if player.is_parrying() and p.parryable:
        player.on_parry_success(p)
        effect.parry_success(*contact_point(p.get_bb(), player.get_bb()))
        p.on_parried(player.reflect_damage_mult)
    # 밀려나는 방향은 투사체 진행 방향을 따른다
    elif player.take_hit(p.damage, player.x - p.dir_x):
        effect.player_hit(player.x, player.y + config.PLAYER_H / 2)
        p.destroy()


def contact_point(bb_a, bb_b):
    # 겹친 영역의 중심
    l, b = max(bb_a[0], bb_b[0]), max(bb_a[1], bb_b[1])
    r, t = min(bb_a[2], bb_b[2]), min(bb_a[3], bb_b[3])
    return (l + r) / 2, (b + t) / 2
