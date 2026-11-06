# 범용 이미지 AI 프롬프트 (배경 · 타일 · 기믹 · 아이템 · 아이콘 · UI)

> 대상: ChatGPT 이미지 생성, Gemini.
> 기준: `개발문서v3.5.md` (12.2 구역 표, 12.6 기믹 목록, 8.2 룬, 8.4 각인, 14.1 HUD, 14.5 아트) · `config.py`의 `REGIONS` 색.
> 플레이어·적·보스·NPC·투사체는 [프롬프트_픽셀아트.md](프롬프트_픽셀아트.md).
> 이미지 연결은 T19에서 한다. 그 전까지 코드는 도형으로 그리므로, 파일은 아래 경로에 모아 두기만 하면 된다.

## 0. 사용 요령

- 범용 AI는 32×32 같은 **작은 크기를 정확히 못 맞춘다.** 크게(512×512 등) 뽑아도 된다. 비율만 맞으면 스크립트로 줄인다.
- 캐릭터와 화풍을 맞추려면 픽셀아트 AI로 만든 `player/idle.png`를 **참고 이미지로 함께 첨부**하고 `match the pixel art style of the attached image`를 붙인다.
- 투명 배경이 필요한 것(기믹·아이템·아이콘)은 `transparent background`를 꼭 넣는다. 안 되면 **단색 초록 배경**(`solid pure green #00FF00 background`)으로 받는다. 스크립트로 지운다. 초록 계열 물체(이끼·덩굴)는 대신 `solid pure magenta #FF00FF background`.
- 한 번에 하나씩 요청한다. 여러 개를 한 장에 요청하면 크기와 간격이 엉킨다. (아이콘은 예외: 6장 참고)
- 다른 게임 이름을 넣지 않는다 ("in the style of ..." 금지). 이 게임의 그림은 오리지널이어야 한다.

### 0.1 색 규칙 (14.5)

- **흰색과 빨간색은 적 공격 예고 전용이다.** 배경·타일·기믹에 순백색이나 선명한 빨강을 넓게 쓰지 않는다. 결과에 밝은 흰빛·붉은빛이 크게 들어가면 버린다.
- 하늘색(`RGB 120,200,240`)은 **숨·공기** 표시 색이다. 안전지대·숨구멍·결정 숨주머니에만 쓰고, 배경에는 넓게 쓰지 않는다.
- 금색(`RGB 240,190,90`)은 **광석** 색이다. 광석·광맥 말고는 아껴 쓴다.

### 0.2 공통 스타일 (모든 프롬프트 앞에 붙이기)

```
2D pixel art for a side-scrolling action exploration game,
underground buried ancient kingdom ruins, muted low-saturation colors,
crisp pixels, no text, no watermark, no characters.
```

### 0.3 구역 표 (배경·타일에 넣을 구역 문구)

| 구역 | 폴더 | 대표 색 (`REGIONS.color`) | 구역 문구 (`[구역 문구]` 자리에 넣기) |
|---|---|---|---|
| R0 광산 | `mine` | 120,85,55 갈색 | `a working mine tunnel with wooden support beams, hanging oil lanterns, rail tracks, warm brown earth` |
| R1 잊힌 회랑 | `corridor` | 90,100,125 청회색 | `a collapsed ancient stone corridor, broken arches and fallen pillars, blue-gray stone, faint rune carvings` |
| R2 이끼 동굴 | `moss` | 60,120,70 녹색 | `a damp cave overgrown with moss and giant mushrooms, dripping water, deep green tones` |
| R3 수정 광맥 | `crystal` | 130,90,200 보라 | `a cave vein full of violet crystal pillars, soft reflected light, abandoned scholar desks turned to crystal` |
| R4 침수 신전 | `temple` | 40,120,130 청록 | `a half-flooded ancient temple, carved teal stone, still water, sunken statues and waterweed` |
| R5 그림자 둥지 | `nest` | 40,50,90 남색 | `a dark nest of black cocoons and thick silk threads, deep navy shadows, very dim` |
| R6 왕의 묘실 | `tomb` | 170,130,60 황토 | `a royal tomb of golden-ochre stone, tall carved walls, ancient banners, dusty and silent` |

---

## 1. 구역 배경 — `assets/images/bg/<폴더>/`

구역마다 **3장**을 만든다. 코드가 먼 배경부터 겹쳐 그리고, 가까운 두 장은 카메라보다 느리게 움직인다(패럴랙스 0.3배, 0.6배).

| 파일 | 크기 | 내용 |
|---|---|---|
| `back.png` | 1280×720 | 가장 먼 배경. 투명 없음, 화면 전체를 채움 |
| `far.png` | 1920×720 | 먼 실루엣 층 (0.3배). 가로로 이어 붙일 수 있게, **아래쪽 절반 이상은 투명** |
| `near.png` | 1920×720 | 가까운 실루엣 층 (0.6배). 가로로 이어 붙일 수 있게, **가운데는 비우고** 위아래 가장자리에만 물체 |

**`back.png`**
```
[공통 스타일]
Background of [구역 문구], seen from the side, deep in the distance.
Very dark and desaturated (main tone close to RGB [대표 색] but much darker)
so characters and white/red flashes stand out clearly in front of it.
No floor, no platforms. 16:9 landscape, 1280x720.
```

**`far.png`** (`back.png` 첨부)
```
[공통 스타일]
A parallax silhouette layer for the attached background: distant shapes of [구역 문구],
slightly lighter than the background but still dark. Seamless left and right.
Transparent background, the lower half mostly empty. Wide 8:3 landscape, 1920x720.
```

**`near.png`** (`back.png` 첨부)
```
[공통 스타일]
A foreground parallax layer for the attached background: hanging and rising details of
[구역 문구] only along the top and bottom edges, the middle area completely empty.
Dark silhouettes. Seamless left and right. Transparent background. 1920x720.
```

> 예고 번쩍임이 흰색·빨간색이므로 배경에 밝은 흰빛이나 붉은빛이 넓게 들어간 결과는 버린다.
> R0 광산의 랜턴 불빛은 **주황색 작은 점** 정도만 허용한다.

---

## 2. 구역 타일 — `assets/images/tile/<폴더>/`

발판은 크기가 제각각인 사각형이라, 코드가 타일을 **반복해서 채운다.** 이음새가 보이면 다시 뽑는다.

| 파일 | 크기 | 내용 |
|---|---|---|
| `solid.png` | 32×32 | 바닥·벽 안쪽 채움 |
| `solid_top.png` | 32×32 | 바닥 윗면 (위쪽 8px에 풀·이끼·모서리 등 구역 장식) |
| `oneway.png` | 32×16 | 아래에서 뚫고 올라갈 수 있는 얇은 발판 |

**`solid.png`**
```
[공통 스타일]
A single seamless tileable ground/wall tile for [구역 문구],
dark stone close to RGB [대표 색] but darker and grayer, subtle cracks.
Must tile seamlessly on all four sides. Square, viewed straight on, flat lighting.
```

**`solid_top.png`** (`solid.png` 첨부)
```
[공통 스타일]
The same tile as the attached image, but the top edge is a floor surface with
[구역별 윗면 장식]. Must tile seamlessly left and right. Square, flat lighting.
```

구역별 윗면 장식: R0 `packed dirt and small pebbles` · R1 `worn flagstone edge` · R2 `a thin layer of green moss` · R3 `small violet crystal sprouts` · R4 `wet stone with a thin waterline` · R5 `sticky black silk strands` · R6 `a carved golden trim`.

**`oneway.png`**
```
[공통 스타일]
A single seamless tileable thin platform segment for [구역 문구], side view
([구역별 발판 재료]). Must tile seamlessly left and right. Wide rectangle, 2:1 ratio,
transparent background.
```

구역별 발판 재료: R0 `wooden plank with iron nails` · R1 `broken stone ledge` · R2 `a giant mushroom cap shelf` · R3 `a flat crystal slab` · R4 `a carved temple ledge` · R5 `a taut bundle of silk threads` · R6 `a gilded stone beam`.

> ChatGPT에서 `show it tiled 3x3 to check seams`라고 요청하면 이음새를 확인하기 쉽다 (확인용 이미지는 저장하지 않는다).

---

## 3. 환경 · 숨 — `assets/images/env/`

| 파일 | 크기 | 프롬프트 (공통 스타일 뒤에) |
|---|---|---|
| `seat.png` | 96×64 | `A small resting spot in the ruins: a flat stone bench with a worn cushion of moss, a crack above letting in a thin draft of fresh air. Side view, transparent background.` (안전지대 앉는 자리) |
| `air_vent.png` | 32×32 × 3프레임 | `A small crack in the rock wall with pale sky-blue air (RGB 120,200,240) seeping out, 3 frames of gentle flicker in a single horizontal row, transparent background.` (숨구멍) |
| `air_vent_moss.png` | 32×32 × 3프레임 | 위와 같은 문장 + `surrounded by small clumps of green moss` (R2 이끼 숨구멍) |
| `spike.png` | 32×16 | `A seamless row of sharp dark stone spikes pointing up, tile left and right, transparent background.` |
| `acid.png` | 32×16 | `A seamless strip of bubbling murky yellow-green acid pool surface, tile left and right, transparent background.` |
| `water.png` | 32×32 | `A seamless semi-transparent teal water tile (RGB 40,160,170) with faint ripples, tile on all sides.` |
| `water_top.png` | 32×8 | `A seamless thin bright teal water surface line (RGB 120,220,225) with small wave crests, tile left and right, transparent background.` |
| `tablet.png` | 64×96 | `An ancient stone tablet standing upright, covered in carved rune text (unreadable symbols, not letters), slightly cracked, side-front view, transparent background.` (석판) |
| `carver_altar.png` | 128×96 | `A small hidden carving workshop corner: a stone workbench with chisels and rune stencils, faint pale-blue rune glow, transparent background.` (숨은 새김터 소품) |
| `camp.png` | 160×96 | `A small miners' camp: a backpack, a bedroll, an oil lantern and a pickaxe leaning on a rock, transparent background.` (보름 캠프 소품) |
| `forge.png` | 160×128 | `A small cave forge made of stacked stones, a glowing orange furnace mouth, an anvil, tongs, transparent background.` (하르 대장간 소품) |

> 포자 지대·탁한 공기·숨 게이트 빗금은 코드가 그린다 (만들지 않는다).

---

## 4. 기믹 — `assets/images/gimmick/`

> 벽·문은 방마다 높이가 달라서 **세로로 이어 붙이는 텍스처**로 만든다. 표의 크기가 한 칸이다.
> 문장 끝에 공통으로 `Must tile seamlessly top and bottom, transparent background.`를 붙인다 (벽·문만).

### 4.1 부서지는 것 (12.6)

| 파일 | 크기 | 프롬프트 (공통 스타일 뒤에) |
|---|---|---|
| `crack_wall.png` | 48×64 | `A section of stone wall with a large visible crack running through it, slightly different color from normal walls so it looks breakable.` (균열벽) |
| `soil_wall.png` | 48×64 | `A section of soft crumbly brown earth wall with loose clods and pebbles.` (무른 흙벽, 굴착의 룬) |
| `hard_soil_wall.png` | 48×64 | `A section of dense dark packed earth wall with embedded stones, tougher than soft earth.` (단단한 흙벽, 굴착 Lv3) |
| `ore_vein_wall.png` | 48×64 | `A section of dark rock wall with diagonal streaks of glittering gold ore (RGB 240,190,90).` (광맥벽) |
| `ore_chunk.png` | 64×48 | `A single lump of rock studded with gold ore nuggets (RGB 240,190,90), sitting on the ground, transparent background.` (광석 덩어리) |
| `break_floor.png` | 32×16 | `A seamless strip of cracked thin stone floor that looks like it could cave in, tile left and right, transparent background.` (깨지는 바닥, 낙반) |
| `air_crystal.png` | 48×48 × 2프레임 | `A cluster of crystal with pale sky-blue air (RGB 120,200,240) trapped inside, frame 1 intact, frame 2 shattered, single horizontal row, transparent background.` (결정 숨주머니) |
| `thorn_vine_wall.png` | 32×64 | `A wall-hugging strip of thick thorny vines, dark green with brown thorns.` (가시 덩굴벽. 마젠타 배경 권장) |

### 4.2 문 · 스위치

| 파일 | 크기 | 프롬프트 (공통 스타일 뒤에) |
|---|---|---|
| `lever_gate.png` | 48×64 | `A section of heavy iron portcullis bars, dark rusted brown-red iron (RGB 110,60,50), front view.` (레버문 · 아레나 문) |
| `one_way.png` | 48×64 | `A section of a thick wooden plank door reinforced with iron bands, with a heavy bolt on one side only.` (한쪽 문 · 숏컷) |
| `shadow_curtain.png` | 48×64 × 3프레임 | `A section of a curtain of drifting black shadow mist, 3 frames of slow wavering in a single horizontal row.` (그림자 장막) |
| `seal_door.png` | 192×256 | `A massive sealed ancient royal gate of golden-ochre stone, carved rune circle in the center with three empty round sockets for cores, transparent background.` (봉인문, 크기 고정) |
| `lever.png` | 48×64 × 2프레임 | `A simple iron wall lever on a stone base, frame 1 handle tilted left, frame 2 handle tilted right, single horizontal row, transparent background.` |
| `crystal_switch.png` | 40×180 × 2프레임 | `A tall violet crystal pillar switch with facets, frame 1 dim, frame 2 glowing from inside, single horizontal row, transparent background.` (수정 스위치) |
| `bolt_trap.png` | 56×96 | `A wall-mounted ancient crossbow trap in a stone housing, the bolt slot facing right, transparent background.` (쇠뇌 함정) |
| `chest.png` | 52×38 × 2프레임 | `A small old iron-banded wooden chest, frame 1 closed, frame 2 lid open, single horizontal row, transparent background.` |

---

## 5. 아이템 — `assets/images/item/` · 투명 배경

| 파일 | 크기 | 프롬프트 (공통 스타일 뒤에) |
|---|---|---|
| `ore.png` | 16×16 | `A tiny glittering gold ore nugget (RGB 240,190,90), centered.` |
| `rare_ore.png` | 32×32 | `A rare deep-teal and gold gemstone ore, faceted, faint inner sparkle, centered.` |
| `engraving.png` | 32×32 | `A small round stone token with a glowing carved rune pattern, pale blue light, centered.` (바닥에 떨어진 각인) |
| `core_crystal.png` | 48×48 | `A round violet crystal core orb with a carved rune ring, centered.` (수정 핵) |
| `core_temple.png` | 48×48 | `A round teal stone core orb with a carved rune ring, faint water shimmer, centered.` (신전 핵) |
| `core_nest.png` | 48×48 | `A round dark navy core orb wrapped in black silk threads with a carved rune ring, centered.` (둥지 핵) |
| `whetstone.png` | 48×48 | `A sharpening whetstone made of violet crystal, rectangular, centered.` (수정 숫돌) |

---

## 6. 아이콘 — `assets/images/icon/`

아이콘은 **4개씩 한 장(2×2 격자)** 으로 요청하면 화풍이 덜 흔들린다. 받은 그림은 스크립트로 잘라 `<id>.png`로 저장한다. 크기는 모두 32×32.

**아이콘 공통 문구** (공통 스타일 대신 이것만 쓴다)
```
Pixel art game icons, a 2x2 grid of 4 separate square icons with equal spacing,
each icon a single centered symbol, simple and readable at 32x32, thick dark outline,
dark rounded-square backplate tinted [배경 색]. No text.
Icons: 1) [설명] 2) [설명] 3) [설명] 4) [설명]
```

### 6.1 룬 6개 (8.2) — 배경 색 `deep slate blue`

| id | 룬 | 아이콘 설명 |
|---|---|---|
| `rune_breath` | 숨의 룬 | `a carved rune of a curling breath of air, pale sky-blue` |
| `rune_burrow` | 굴착의 룬 | `a carved rune of a drill-like arrow piercing through soil, earthy brown` |
| `rune_brace` | 버팀의 룬 | `a carved rune of a pickaxe driven into a wall, moss green` |
| `rune_crystal` | 결정의 룬 | `a carved rune of a floating crystal platform, violet` |
| `rune_breakthrough` | 돌파의 룬 | `a carved rune of a fist bursting through a stone wall, teal` |
| `rune_shadow` | 그림자의 룬 | `a carved rune of a figure dashing through a shadow veil, dark navy` |

### 6.2 각인 21개 (8.4) — 배경 색은 대상별

대상별 배경 색: 곡괭이 = `warm orange`, 숨 = `pale sky blue`, 굴착 = `earthy brown`, 결정 = `soft violet`, 공용 = `cool gray`

| id | 각인 | 대상 | 아이콘 설명 |
|---|---|---|---|
| `third_strike` | 세 번째 일격 | 곡괭이 | `a pickaxe with three impact marks` |
| `quick_hands` | 빠른 손놀림 | 곡괭이 | `a pickaxe with speed lines` |
| `long_handle` | 긴 자루 | 곡괭이 | `a pickaxe with an extra-long handle` |
| `miners_grit` | 광부의 근성 | 곡괭이 | `a clenched fist gripping a pickaxe` |
| `last_stand` | 벼랑 끝 | 곡괭이 | `a pickaxe on the edge of a cliff with one small crystal heart` |
| `deep_lung` | 깊은 폐 | 숨 | `a pair of large lungs with an air swirl` |
| `parry_breath` | 받아친 숨 | 숨 | `a pickaxe handle blocking, with a breath of air rising from the impact` |
| `steady_breath` | 고른 숨 | 숨 | `a calm even wave line of air` |
| `thrifty_breath` | 아끼는 숨 | 숨 | `a small closed pouch with a breath of air inside` |
| `wind_step` | 바람걸음 | 굴착 | `a boot with a gust of wind` |
| `long_dash` | 긴 질주 | 굴착 | `a long arrow with a trail of dirt` |
| `dash_strike` | 질풍 일격 | 굴착 | `a pickaxe striking out of a speed blur` |
| `mirror_crystal` | 거울 결정 | 결정 | `a crystal shard reflecting a bouncing projectile` |
| `counter_wave` | 반격 파동 | 공용 | `a crescent air wave flying from a raised pickaxe` |
| `sharp_counter` | 날카로운 반격 | 공용 | `an eye inside a pickaxe-handle outline` |
| `stone_skin` | 단단한 껍질 | 공용 | `a stone shell plate with a small clock` |
| `thorn_shell` | 가시 갑각 | 공용 | `a shell plate with sharp thorns sticking out` |
| `compass` | 광부의 나침반 | 공용 | `an old brass compass` |
| `ore_magnet` | 광석 자석 | 공용 | `a horseshoe magnet pulling gold nuggets` |
| `first_breath` | 먼저 간 이의 숨 | 숨 | `a broken old mining helmet with a faint breath of air` |
| `breath_echo` | 되받은 숨 | 공용 | `two breath swirls echoing each other` |

> 묶음 예: `third_strike · quick_hands · long_handle · miners_grit`처럼 **같은 배경 색끼리 4개씩**. 남는 칸은 다음 묶음과 합쳐도 된다 (그때는 아이콘마다 `[배경 색]`을 따로 적는다).

### 6.3 HUD · 지도

| id | 크기 | 아이콘 설명 | 배경 |
|---|---|---|---|
| `hp_full` | 24×24 | `a small faceted pale blue-white crystal, full` (체력 1칸) | 없음 (투명) |
| `hp_empty` | 24×24 | 같은 결정 `but empty, dark hollow outline only` | 없음 (투명) |
| `breath_zone_spore` | 16×16 | `a small yellow spore dot cluster` (숨 막대 옆 배율 표시) | 없음 |
| `breath_zone_water` | 16×16 | `a small teal water drop` | 없음 |
| `map_safe` | 16×16 | `a tiny bench with an air swirl` (지도: 안전지대) | 없음 |
| `map_carver` | 16×16 | `a tiny chisel with a rune` (지도: 새김터) | 없음 |
| `map_player` | 16×16 | `a tiny miner helmet with a lamp` (지도: 현재 위치) | 없음 |

> HUD 아이콘은 크기가 작아 2×2 격자에 넣지 말고 하나씩, `transparent background, readable at 16x16`으로 요청한다.

---

## 7. UI 화면 — `assets/images/ui/` · 1280×720

**`title_bg.png`** 타이틀
```
[공통 스타일]
A lone young miner with a helmet lamp standing at the edge of a huge dark underground chasm,
far below the faint outline of a buried ancient kingdom, a thin beam of light from the lamp.
Leave the center-top area calm and empty for the game title text. No text. 16:9 landscape, 1280x720.
```

**`ending_seal.png`** 엔딩 · 봉인 (선택)
```
[공통 스타일]
A group of miners climbing out of a mine entrance into a quiet dawn on a mountainside,
behind them the mine slowly falling dark and still. Peaceful, bittersweet. No text. 1280x720.
```

**`ending_open.png`** 엔딩 · 개방 (선택)
```
[공통 스타일]
Wind rushing up through a collapsing underground kingdom, pale sky-blue air streaming upward,
a small miner silhouette running up toward daylight above. Hopeful and dramatic. No text. 1280x720.
```

> 문자가 그림에 들어가면 버린다. 제목·메뉴 글자는 코드가 폰트로 쓴다.
