# 범용 이미지 AI 프롬프트 (배경 · 타일 · 문 · 아이콘)

> 대상: ChatGPT 이미지 생성, Gemini.
> 파일 경로·크기의 기준은 [스프라이트_명세.md](스프라이트_명세.md)다.

## 0. 사용 요령

- 범용 AI는 32×32 같은 **작은 크기를 정확히 못 맞춘다.** 크게(예: 512×512) 뽑아도 된다. 넣어 주면 스크립트로 줄인다.
- 캐릭터와 화풍을 맞추려면 픽셀아트 AI로 만든 `player/idle.png`를 **참고 이미지로 함께 첨부**하고 "match the pixel art style of the attached image"를 붙인다.
- 투명 배경이 필요한 것(문, 아이콘)은 "transparent background"를 꼭 넣는다. 안 되면 **단색 초록 배경**(`solid pure green #00FF00 background`)으로 받는다. 나중에 스크립트로 지운다.
- 한 번에 하나씩 요청한다. 여러 개를 한 장에 요청하면 크기와 간격이 엉킨다.

### 공통 스타일 (모든 프롬프트 앞에 붙이기)

```
2D pixel art for a side-scrolling action game, dark medieval castle theme,
muted low-saturation colors, crisp pixels, no text, no watermark.
```

---

## 1. 배경 — `assets/images/map/background.png` · 1280×720

```
[공통 스타일]
Interior of a dark ruined castle hall seen from the side, stone pillars,
broken arched windows with faint moonlight, hanging chains, distant torches.
Very dark and desaturated (main tone around RGB 30,30,40) so characters
and white/red flashes stand out clearly in front of it.
No floor in the bottom area, no characters. 16:9 landscape, 1280x720.
```

> 예고 번쩍임이 흰색과 빨간색이므로 **밝은 흰빛이나 붉은빛이 넓게 들어간 결과는 버린다.**

## 2. 타이틀 배경 (선택) — `assets/images/ui/title_bg.png` · 1280×720

```
[공통 스타일]
A lone swordsman silhouette standing before a huge dark castle gate at night,
cold moonlight, drifting embers. Leave the center area calm and empty
for the game title text. No text. 16:9 landscape, 1280x720.
```

---

## 3. 바닥·벽 타일 — `assets/images/map/tile_solid.png` · 32×32

```
[공통 스타일]
A single seamless tileable stone brick tile for floors and walls,
dark gray stone (around RGB 70,70,80), subtle cracks.
Must tile seamlessly on all four sides. Square, viewed straight on, flat lighting.
```

## 4. 발판 타일 — `assets/images/map/tile_oneway.png` · 32×16

```
[공통 스타일]
A single seamless tileable wooden plank platform segment, side view,
brown wood with a lighter top edge, small iron nails.
Must tile seamlessly left and right. Wide rectangle, 2:1 ratio,
transparent background.
```

> 타일은 이어 붙였을 때 이음새가 보이면 다시 뽑는다. ChatGPT에서 "show it tiled 3x3 to check seams"라고 요청하면 확인하기 쉽다(확인용 이미지는 저장하지 않는다).

---

## 5. 문 — `assets/images/map/` · 64×112 (세로로 긴 비율 4:7)

두 장의 모양이 같아야 하므로 **닫힌 문을 먼저 만들고, 그 이미지를 첨부해서 열린 문을 요청**한다.

**`door_locked.png`**
```
[공통 스타일]
A tall arched iron-reinforced wooden castle door, front view, closed,
dark wood with heavy iron bands and a large padlock, stone frame.
Tall narrow 4:7 portrait ratio, transparent background.
```

**`door_open.png`** (닫힌 문 첨부)
```
[공통 스타일]
The same door frame as the attached image, but the door is open
and warm golden light (around RGB 240,220,140) shines out from inside.
Same size, same frame, same angle. Transparent background.
```

---

## 6. 강화 아이콘 (선택) — `assets/images/ui/upgrade_icons.png` · 32×32 × 12

12개를 **하나씩 따로** 만든다. 파일명은 임시로 `icon_01.png ~ icon_12.png`로 저장하면, 스크립트로 한 줄 시트로 합친다. 번호 순서가 곧 시트 순서다.

**아이콘 공통 문구** (공통 스타일 뒤에 붙이기)
```
A single game skill icon, square, centered symbol, simple and readable at 32x32,
thick outline, transparent background. Background tint: [카테고리 색].
```

카테고리 색: 패링 = `soft white-silver`, 기초 스탯 = `warm orange`, 유틸리티 = `cool green`

| 번호 | 강화 | 카테고리 | 아이콘 설명 (프롬프트에 넣을 문장) |
|---|---|---|---|
| 01 | 예리한 감각 (패링 판정 +) | 패링 | `an eye inside a sword-shaped outline` |
| 02 | 반격의 검기 | 패링 | `a crescent sword energy wave flying from a raised sword` |
| 03 | 되받아치기 (반사 피해 2배) | 패링 | `an arrow bouncing back off a sword blade, curved arrow` |
| 04 | 흡수 (패링 시 회복) | 패링 | `a red heart behind two crossing swords sparking` |
| 05 | 강인한 몸 (최대 체력 +) | 기초 | `a big red heart with a plus sign` |
| 06 | 날 선 검 (공격력 +) | 기초 | `a sharp sword with a bright gleam on the blade` |
| 07 | 마무리 일격 (3타 피해 +) | 기초 | `a heavy downward sword strike with three slash marks` |
| 08 | 불굴 (피격 무적 +) | 기초 | `a shield with a small clock on it` |
| 09 | 2단 점프 | 유틸 | `a boot with two upward arrows` |
| 10 | 질풍 (대시 거리 +) | 유틸 | `a running figure with long speed lines` |
| 11 | 순보 (대시 쿨타임 −) | 유틸 | `an hourglass with a lightning bolt` |
| 12 | 기습 (대시 후 첫 공격 2배) | 유틸 | `a dagger striking out of a speed blur` |
