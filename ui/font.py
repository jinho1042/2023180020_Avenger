# 한글 TTF 로드 (14.5). 크기별로 한 번만 만들어 재사용한다 (16장: 크기 2~3개만)
# FONT_PATH가 없으면 FONT_FALLBACK_PATH(한글 없는 영문 폰트)로 바꾸고, 문구는 영어 대체 문구를 쓴다
# 둘 다 없으면 get()이 None을 돌려주고 글자를 그리지 않는다

import os

from pico2d import load_font

import config

fonts = {}        # 크기 → pico2d 폰트


def path():
    if os.path.exists(config.FONT_PATH):
        return config.FONT_PATH
    if os.path.exists(config.FONT_FALLBACK_PATH):
        return config.FONT_FALLBACK_PATH
    return None


def has_korean():
    return os.path.exists(config.FONT_PATH)


def get(size):
    if size not in fonts:
        p = path()
        fonts[size] = load_font(p, size) if p else None
    return fonts[size]


def text(ko, en):
    # 한글 폰트가 없으면 영어 대체 문구
    return ko if has_korean() else en
