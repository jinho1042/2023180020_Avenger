# 효과음 합성기. 표준 라이브러리만으로 assets/sounds/*.wav를 만든다
# 실행: python tools/gen_sounds.py  (게임 실행에는 필요 없음, 소리를 바꾸고 싶을 때만 다시 실행)
# 여기 숫자들은 게임 수치가 아니라 "소리 파일의 재료"라서 config.py가 아닌 이 파일에 둔다

import math
import os
import random
import struct
import wave

RATE = 44100
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sounds')


def tone(freq, t, wave_type='sine'):
    phase = (freq * t) % 1.0
    if wave_type == 'square':
        return 1.0 if phase < 0.5 else -1.0
    if wave_type == 'saw':
        return phase * 2 - 1
    if wave_type == 'tri':
        return 4 * abs(phase - 0.5) - 1
    return math.sin(2 * math.pi * phase)


def envelope(t, length, attack, decay_power=2.0):
    # 짧게 올라갔다가 거듭제곱 곡선으로 사라진다
    if t < attack:
        return t / attack
    return (1 - (t - attack) / (length - attack)) ** decay_power


def render(length, sample_fn):
    return [sample_fn(i / RATE) for i in range(int(length * RATE))]


def mix(*tracks):
    n = max(len(tr) for tr in tracks)
    return [sum(tr[i] for tr in tracks if i < len(tr)) for i in range(n)]


def lowpass(samples, amount):
    # amount 0~1, 클수록 먹먹하다
    out, prev = [], 0.0
    for s in samples:
        prev = prev * amount + s * (1 - amount)
        out.append(prev)
    return out


def save(name, samples, volume=0.8):
    peak = max(abs(s) for s in samples) or 1.0
    data = b''.join(struct.pack('<h', int(s / peak * volume * 32767)) for s in samples)
    with wave.open(os.path.join(OUT_DIR, name + '.wav'), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data)
    print('saved', name)


def noise_burst(length, attack, power, lp):
    return lowpass(render(length, lambda t: random.uniform(-1, 1) * envelope(t, length, attack, power)), lp)


# ---- 소리 레시피 ----

def parry():
    # 금속 충돌: 비정수배 배음 여러 개가 길게 울리고, 앞부분에 짧은 잡음 타격
    length = 0.6
    partials = [(1250, 1.0), (1870, 0.7), (2610, 0.5), (3390, 0.35), (4920, 0.2)]
    ring = render(length, lambda t: sum(a * tone(f, t) for f, a in partials) * envelope(t, length, 0.002, 3))
    clank = noise_burst(0.05, 0.001, 2, 0.2)
    return mix(ring, [s * 3 for s in clank])


def parry_miss():
    # 허공을 가르는 바람 소리 + 낮게 떨어지는 음
    length = 0.25
    air = noise_burst(length, 0.03, 2, 0.7)
    drop = render(length, lambda t: tone(320 - 600 * t, t, 'tri') * envelope(t, length, 0.01) * 0.4)
    return mix(air, drop)


def swing():
    # 검 휘두르기: 짧은 바람 소리
    return noise_burst(0.14, 0.03, 3, 0.55)


def hit():
    # 플레이어 피격: 둔탁한 저음 + 잡음
    length = 0.25
    thud = render(length, lambda t: tone(140 - 200 * t, t) * envelope(t, length, 0.002, 3))
    return mix(thud, noise_burst(0.1, 0.001, 2, 0.5))


def enemy_hurt():
    # 적이 공격에 맞음: 짧고 가벼운 타격
    length = 0.1
    snap = render(length, lambda t: tone(260 - 900 * t, t, 'square') * envelope(t, length, 0.001, 3) * 0.4)
    return mix(snap, noise_burst(0.06, 0.001, 2, 0.35))


def kill():
    # 적 처치: 터지는 잡음 + 내려가는 음
    length = 0.4
    pop = noise_burst(length, 0.002, 2.5, 0.4)
    fall = render(length, lambda t: tone(500 - 900 * t, t, 'square') * envelope(t, length, 0.002, 2) * 0.3)
    return mix(pop, fall)


def telegraph_white():
    # 패링 가능 예고: 높고 맑은 '띵'
    length = 0.25
    return render(length, lambda t: (tone(1760, t) + 0.3 * tone(3520, t)) * envelope(t, length, 0.003, 2))


def telegraph_red():
    # 패링 불가 예고: 낮고 거친 두 번 울림
    beep = 0.09
    gap = 0.04
    length = beep * 2 + gap

    def sample(t):
        local = t if t < beep else t - beep - gap
        if local < 0 or local >= beep:
            return 0.0
        return (tone(440, t, 'saw') + tone(466, t, 'saw')) * envelope(local, beep, 0.003, 1) * 0.5
    return render(length, sample)


def groggy():
    # 보스 그로기: 크게 울리는 종 + 저음
    length = 1.2
    partials = [(220, 1.0), (440, 0.6), (660, 0.4), (1180, 0.25)]
    bell = render(length, lambda t: sum(a * tone(f, t) for f, a in partials) * envelope(t, length, 0.003, 2.5))
    boom = render(0.4, lambda t: tone(60, t) * envelope(t, 0.4, 0.005, 2))
    return mix(bell, boom)


def phase2():
    # 2페이즈 진입: 낮게 부풀어 오르는 굉음
    length = 0.9
    rumble = render(length, lambda t: (tone(55 + 40 * t, t, 'saw') + tone(82 + 60 * t, t, 'saw'))
                    * min(1, t / 0.5) * (1 - t / length) * 0.5)
    return lowpass(mix(rumble, noise_burst(length, 0.4, 1, 0.8)), 0.5)


def dash():
    # 대시: 빠르게 올라가는 바람 소리
    length = 0.2
    air = render(length, lambda t: random.uniform(-1, 1) * math.sin(math.pi * t / length))
    return lowpass(air, 0.35)


def jump():
    length = 0.12
    return render(length, lambda t: tone(300 + 900 * t, t, 'tri') * envelope(t, length, 0.005, 2))


def shoot():
    # 활 시위: 짧은 '퉁'
    length = 0.15
    twang = render(length, lambda t: tone(180, t, 'tri') * envelope(t, length, 0.001, 3))
    return mix(twang, noise_burst(0.08, 0.002, 2, 0.3))


def door():
    # 문 열림: 두 음 상승 차임
    note = 0.18
    length = note * 2

    def sample(t):
        freq, local = (660, t) if t < note else (990, t - note)
        return tone(freq, t) * envelope(local, note, 0.005, 1.5)
    return render(length, sample)


def death():
    length = 1.0
    fall = render(length, lambda t: tone(330 * (1 - 0.6 * t), t, 'square') * envelope(t, length, 0.01, 1.5) * 0.4)
    return lowpass(mix(fall, noise_burst(0.3, 0.002, 2, 0.5)), 0.3)


def cursor():
    length = 0.05
    return render(length, lambda t: tone(880, t, 'square') * envelope(t, length, 0.002, 2) * 0.4)


def select():
    note = 0.07
    length = note * 2

    def sample(t):
        freq, local = (880, t) if t < note else (1320, t - note)
        return tone(freq, t, 'square') * envelope(local, note, 0.002, 1.5) * 0.4
    return render(length, sample)


RECIPES = [parry, parry_miss, swing, hit, enemy_hurt, kill, telegraph_white, telegraph_red,
           groggy, phase2, dash, jump, shoot, door, death, cursor, select]

if __name__ == '__main__':
    random.seed(1)  # 다시 실행해도 같은 소리
    os.makedirs(OUT_DIR, exist_ok=True)
    for recipe in RECIPES:
        save(recipe.__name__, recipe())
