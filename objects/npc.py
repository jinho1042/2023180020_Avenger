import config
import game_world
from systems import camera


class Npc:
    # NPC·석판 (2.5): objects의 ["npc", x, y, NPC id], ["tablet", x, y, 석판 id]. (x, y) = 아래쪽 중심
    # ["warning_tablet", x, y, 석판 id] = 경고·안내 석판. 모양·대화는 석판과 같고 수집품(12.7)으로 세지 않음 (18장 60번)
    # 가까이 서서 ↑를 누르면 대화 (play_mode.check_npcs → dialog_mode). 대사는 data/dialog/<id>.json
    # ["carver", x, y, id] = 새김터의 룬지기 오람. 말을 걸면 대화 대신 carver_mode.talk() (T43)
    # T39는 보름(상점)과 석판. 하르(T62)는 대사 har.json의 forge로 대장간 목록 (dialog_mode), 숫돌 첫 대사 har_whetstone(T64). 실종 광부는 T61
    def __init__(self, kind, x, y, npc_id):
        self.kind = kind          # 'npc' | 'tablet' | 'warning_tablet' | 'carver'
        self.x, self.y = x, y
        self.id = npc_id
        self.w, self.h = (config.TABLET_W, config.TABLET_H) if kind in ('tablet', 'warning_tablet') else (config.NPC_W, config.NPC_H)
        self.prompt = False       # 말 걸 수 있으면 머리 위에 ↑ 표시 (play_mode가 매 프레임 정함)

    def update(self):
        pass

    def dialog_id(self, state):
        # 보름 힌트 (7.5): 숨의 룬 없이 숨막이 갱에서 HINT_FAIL_COUNT번 기절하면 바람 소리 이야기
        if (self.id == 'borum' and state.hint_fail_count >= config.HINT_FAIL_COUNT
                and not state.player.runes.get('breath', 0)):
            return 'borum_hint'
        # 하르 (13.3, T64): 수정 숫돌을 처음 가져가면 짧은 대사 뒤 곡괭이 강화 목록 (대사의 flag로 한 번만)
        if (self.id == 'har' and config.FORGE_PICKAXE_UNLOCK_FLAG in state.flags
                and config.FORGE_WHETSTONE_TALKED_FLAG not in state.flags):
            return 'har_whetstone'
        return self.id

    def can_talk(self, player):
        if not player.on_ground or player.is_locked():
            return False
        return abs(player.x - self.x) <= config.NPC_TALK_RADIUS and abs(player.y - self.y) <= self.h

    def draw(self):
        if self.kind in ('tablet', 'warning_tablet'):
            self.draw_tablet()
        elif self.kind == 'carver':
            self.draw_carver()
        else:
            self.draw_npc()
        if self.prompt:
            self.draw_prompt(self.x, self.y + self.h + config.TALK_PROMPT_GAP)
        if game_world.show_hitbox:
            camera.draw_rect(*self.get_bb(), *config.COLOR_TALK_PROMPT)

    def draw_npc(self):
        # 몸 사각형 + 헬멧 랜턴 (14.5 도형 규칙의 광부 모양)
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *config.COLOR_NPC.get(self.id, config.COLOR_NPC_DEFAULT), filled=True)
        lamp = config.NPC_LAMP / 2
        camera.draw_rect(self.x - lamp, t, self.x + lamp, t + config.NPC_LAMP, *config.COLOR_NPC_LAMP, filled=True)

    def draw_carver(self):
        # 몸 절반이 돌이 된 룬지기 (2.5): 아래 절반은 돌 색, 위는 몸 색
        l, b, r, t = self.get_bb()
        mid = (b + t) / 2
        camera.draw_rect(l, b, r, mid, *config.COLOR_CARVER_STONE, filled=True)
        camera.draw_rect(l, mid, r, t, *config.COLOR_NPC.get(self.id, config.COLOR_NPC_DEFAULT), filled=True)

    def draw_tablet(self):
        # 돌판 + 가운데 룬 문양 줄
        l, b, r, t = self.get_bb()
        camera.draw_rect(l, b, r, t, *config.COLOR_TABLET, filled=True)
        pad = self.w / 4
        for i in range(3):
            y = t - pad - i * pad
            camera.draw_rect(l + pad, y - 2, r - pad, y + 2, *config.COLOR_TABLET_RUNE, filled=True)

    def draw_prompt(self, cx, y):
        # ↑ 화살표 (가로줄 쌓기 삼각형 + 막대)
        size = config.TALK_PROMPT_SIZE
        color = config.COLOR_TALK_PROMPT
        camera.draw_rect(cx - size / 6, y, cx + size / 6, y + size, *color, filled=True)
        for i in range(0, int(size), 3):
            half = size / 2 * (1 - i / size)
            camera.draw_rect(cx - half, y + size + i, cx + half, y + size + i + 3, *color, filled=True)

    def get_bb(self):
        return self.x - self.w / 2, self.y, self.x + self.w / 2, self.y + self.h

    def handle_collision(self, group, other):
        pass
