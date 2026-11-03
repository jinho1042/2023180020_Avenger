from pico2d import open_canvas, close_canvas

import config
import game_framework
from modes import title_mode
from systems import sound

open_canvas(config.SCREEN_W, config.SCREEN_H)
sound.init()
game_framework.run(title_mode)
close_canvas()
