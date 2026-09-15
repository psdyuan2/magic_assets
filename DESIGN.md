# Design System

## Visual Theme

街区柴犬铺的白天柜台：窗光打在芝麻毛上，柿子色暖帘，墨色橡皮章，牛皮纸价签。像素店犬坐在铺面正中。页面是浅色店面，不是夜间 App。

## Color

策略：Full palette。参考物是柿子暖帘 + 芝麻毛 + 柜台墨印，不是「宠物店粉绿」。

| Token | Value | Role |
| --- | --- | --- |
| `--persimmon` | `oklch(62% 0.16 42)` | 暖帘、当前 Tab、主按钮 |
| `--sesame` | `oklch(78% 0.08 75)` | 皮毛高光、货架木色 |
| `--cream` | `oklch(96% 0.02 85)` | 店面墙 |
| `--ink` | `oklch(24% 0.03 50)` | 正文、描边 |
| `--moss` | `oklch(52% 0.07 130)` | 会员定制点缀 |
| `--paper` | `oklch(92% 0.025 80)` | 货架纸、模块底 |

中性色全部带 0.01 左右的暖 chroma，禁止纯黑纯白。

## Typography

- 店招 / 大标题：`Mochiy Pop One`（店帘字）+ 中文回退 `ZCOOL QingKe HuangYou`
- 标签 / 价签：`DotGothic16`
- 正文：`Noto Sans SC`

层级：店招与正文对比至少 1.6×。正文行宽不超过 65ch。

## Layout

上 Tab、中店犬、下货架与定制台。店犬居中是店招，不是模板堆叠。货架横向陈列、宽度可以不一样。定制台是一条工作台，不是第二组相同卡片。间距按 4 的倍数：8 / 16 / 24 / 48 / 80。

## Components

- Tab：像素图标 + 二字标签，当前项柿子色底板、墨色字。
- 货架项：图标、品类名、一句货品，宽度错落。
- 定制台：左侧说明，右侧三项选择（绣字、颜色、扣具），一个下单按钮。
- 焦点：2px 墨色外环，偏移 3px。

## Elevation

几乎不投影。分组靠纸色块、1px 墨色细线和留白。像素图用 `image-rendering: pixelated`，只按整数倍放大。

## Motion

店犬用 4 帧像素循环。Tab 进入用 pop，店犬外包一层轻微 bob。只动 transform / opacity。`prefers-reduced-motion` 时循环停在第一帧。
