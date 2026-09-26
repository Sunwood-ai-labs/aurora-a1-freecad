---
message: "AIエージェントが FreeCAD TechDraw で AURORA A1 の図面一式（A3・11枚、断面9箇所、部品表84点）を出図するまで"
mode: autonomous
canvas: 1920x1080
duration: 106
music: .media/audio/bgm/bgm_001.mp3 (reused from aurora-a1-making; 120 BPM, drop 48s, breakdown 62–80s, return 80s, outro 96s)
---

## Frame 1
status: outline
src: compositions/frames/01-intro.html
start: 0
duration: 8
motion: rules — multi-phase-camera (傾けた総組立図), waterfall-entry (タイトル), spring-pop-entrance (チップ)
beat: タイトル。3Dモデルから A3 図面 11 枚へ。

## Frame 2
status: outline
src: compositions/frames/02-ask.html
start: 8
duration: 8
motion: rules — spring-pop-entrance (チャット吹き出し・要件チップ)
beat: STEP 01 依頼。「出図ってできる？」→ TechDraw で可能 →「部品ごとの寸法と断面図がほしい」。

## Frame 3
status: outline
src: compositions/frames/03-plan.html
start: 16
duration: 10
motion: rules — spring-pop-entrance (11 枚のサムネイル), multi-phase-camera
beat: STEP 02 構成。A3 × 11 枚のシート構成。

## Frame 4
status: outline
src: compositions/frames/04-probe.html
start: 26
duration: 10
motion: rules — discrete-text-sequence (API 呼び出し), spring-pop-entrance (結果カード)
beat: STEP 03 試作。外形寸法 545/2000 ✓、距離寸法 19,700（縮尺ずれ）、断面 742 エッジ、PDF。

## Frame 5
status: outline
src: compositions/frames/05-bspline.html
start: 36
duration: 12
motion: rules — discrete-text-sequence (コード差分), counting-dynamic-scale (56 → 3 面)
beat: STEP 04 モデル修正。ポリゴン翼型 → B-spline、主翼の面数 56 → 3。

## Frame 6
status: outline
src: compositions/frames/06-automate.html
start: 48
duration: 14
motion: rules — spring-pop-entrance (つまずき 5 行)
beat: STEP 05 自動化。非同期投影 / テンプレート / 寸法配置 / タイムアウト / 輪郭欠け。

## Frame 7
status: outline
src: compositions/frames/07-sections.html
start: 62
duration: 18
motion: rules — multi-phase-camera (図面上の断面へ寄る), spring-pop-entrance
beat: STEP 06 断面図。A-A / B-B / D-F / G-H / J-K / L の 9 箇所。

## Frame 8
status: outline
src: compositions/frames/08-bom.html
start: 80
duration: 10
motion: rules — counting-dynamic-scale (0 → 84), multi-phase-camera (表をパン)
beat: STEP 07 部品表。84 部品の外形寸法と体積。

## Frame 9
status: outline
src: compositions/frames/09-export.html
start: 90
duration: 6
motion: rules — spring-pop-entrance
beat: STEP 08 出力。PDF 11 / DXF 11 / 再生成スクリプト。

## Frame 10
status: outline
src: compositions/frames/10-outro.html
start: 96
duration: 10
motion: rules — spring-pop-entrance (シートの扇), waterfall-entry (締め)
beat: 11 枚を並べて締め。
