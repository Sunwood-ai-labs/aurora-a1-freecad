# frame.md — AURORA A1 Making-of

**Concept angle:** エンジニアのビルドログ。製図グリッドの上で、エージェントの声（等幅のツール呼び出し・数値）と
人の声（日本語の見出し）が交互に語り、実物のレンダーがその証拠として置かれる。

## Palette (one accent)

| role    | hex       | use                                                     |
| ------- | --------- | ------------------------------------------------------- |
| bg      | `#0C0B14` | 全シーン共通のキャンバス（紫寄りのインク）              |
| surface | `#16131F` | パネル・端末・カード                                    |
| line    | `#2E2945` | 罫線・枠・製図グリッド                                  |
| fg      | `#EDEAF6` | 本文・見出し                                            |
| muted   | `#A49EBE` | 補足テキスト                                            |
| accent  | `#A77BFF` | STEP番号・成功・寸法線（リバリーの紫）                  |
| signal  | `#FF4FA3` | 問題（ISSUE）表示のみ（タイヤのピンク）。常用しない     |

## Type

- **Noto Sans JP** 700 / 400 — 見出し・本文（人の声）。見出し 64–96px、本文 30–40px。
- **JetBrains Mono** 400 / 700 — ツール呼び出し・コード・数値・ラベル（エージェントの声）。ラベル 22–26px、数値は `tabular-nums`。
- 見出しは tracking -0.02em。英字タイトルのみ -0.03em。

## Frame grammar

- 上部 HUD（index 常駐）：左「AURORA A1 — MAKING OF」、右「STEP nn / 08 ＋工程名」。
- 下部に 8 セグメントの進行バー（index 常駐）。
- シーン見出しは左上固定：STEP タグ（mono, accent）→ 見出し → 補足。
- 背景：`assets/renders/plate_bg.png`（インク＋中央の紫グロー＋80px 製図グリッド）を全編共通で敷く。
- レンダーは透過 PNG をそのまま置き、枠で囲まない。パネルは 2px の `line` 枠＋`surface`。

## Motion

- シーン切替は小節頭（2秒単位）のハードカット＋ accent の走査線ワイプ。
- 登場：見出しは waterfall-entry、カード群は spring-pop-entrance（power3.out, 反動なし）。
- レンダーは multi-phase-camera の緩いドリフトで常に呼吸させる。
- 禁止：back.out の跳ね、グラデーション文字、全画面リニアグラデーション。
