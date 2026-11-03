import os

from pico2d import get_time, load_music, load_wav

import config

# 효과음·배경음. 파일이 없거나 오디오 장치가 없으면 조용히 건너뛴다
# open_canvas 이후(오디오 초기화 뒤)에 init()을 부른다

ROOT = os.path.join(os.path.dirname(__file__), '..', config.SOUND_DIR)

sounds = {}
last_played = {}
music = None
music_name = None


def init():
    for name, volume in config.SOUND_VOLUME.items():
        path = os.path.join(ROOT, name + '.wav')
        if not os.path.exists(path):
            continue
        try:
            wav = load_wav(path)
        except IOError:
            return  # 오디오 장치 없음: 이후 파일도 마찬가지
        wav.set_volume(volume)
        sounds[name] = wav


def play(name):
    wav = sounds.get(name)
    if wav is None:
        return
    now = get_time()
    if now - last_played.get(name, -1) < config.SOUND_MIN_INTERVAL:
        return
    last_played[name] = now
    wav.play()


def play_music(name):
    # 이미 같은 곡이 나오고 있으면 이어서 재생한다
    global music, music_name
    if name == music_name:
        return
    stop_music()
    path = os.path.join(ROOT, config.MUSIC_FILES[name])
    if not os.path.exists(path):
        return
    try:
        music = load_music(path)
    except IOError:
        return
    music_name = name
    music.set_volume(config.MUSIC_VOLUME)
    music.repeat_play()


def stop_music():
    global music, music_name
    if music:
        music.stop()
    music = None
    music_name = None
