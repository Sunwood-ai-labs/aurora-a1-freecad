---
message: "コンセプト画像3枚から、AIエージェントがFreeCAD MCPで84部品・12サブアセンブリのF1アッシーを組み上げるまで"
mode: autonomous
canvas: 1920x1080
duration: 106
music: assets/audio/bgm.mp3 (120 BPM, bar = 2s; drop 48s, breakdown 62–80s, return 80s, outro 96s)
---

## Frame 1
status: outline
src: compositions/frames/01-intro.html
start: 0
duration: 8
motion: rules — multi-phase-camera (hero render), waterfall-entry (title), spring-pop-entrance (tool chips)
beat: タイトル「AURORA A1」。完成レンダーを背に、何を作ったか・誰が作ったか（Claude Code × FreeCAD MCP）。

## Frame 2
status: outline
src: compositions/frames/02-connect.html
start: 8
duration: 8
motion: rules — discrete-text-sequence (ツール呼び出し→JSON応答), spring-pop-entrance (状態ピル)
beat: STEP 01 接続確認。get_rpc_status → running / healthy、list_documents → []。

## Frame 3
status: outline
src: compositions/frames/03-input.html
start: 16
duration: 10
motion: rules — spring-pop-entrance (画像カード3枚), multi-phase-camera (三面図へ寄る)
beat: STEP 02 インプット。ユーザーが渡したのはコンセプト画像3枚。

## Frame 4
status: outline
src: compositions/frames/04-dims.html
start: 26
duration: 10
motion: rules — svg-path-draw (寸法線), spring-pop-entrance (諸元カード)
beat: STEP 03 寸法抽出。側面の正投影レンダーに全長・WB・全高の寸法線。図面値とモデル値を併記。

## Frame 5
status: outline
src: compositions/frames/05-script.html
start: 36
duration: 12
motion: rules — discrete-text-sequence (コードの一括貼り付け), spring-pop-entrance (アセンブリツリー)
beat: STEP 04 スクリプト。build_aurora_a1.py（608行）の要点と App::Part 階層（7グループ・84部品）。

## Frame 6
status: outline
src: compositions/frames/06-build.html
start: 48
duration: 14
motion: rules — counting-dynamic-scale (0→84 部品), multi-phase-camera (組み上がるレンダー)
beat: STEP 05 ビルド。サブアセンブリ単位で組み上がる様子＋実測値（53.8 s / invalid 0 / 5640×2002×965）。

## Frame 7
status: outline
src: compositions/frames/07-fix.html
start: 62
duration: 18
motion: rules — discrete-text-sequence (エラーログ), spring-pop-entrance (ISSUE カード), multi-phase-camera (前後比較)
beat: STEP 06 検証ループ。黒いウイング→Shaded、デカール失敗→ずらした複製で代替、はみ出し部品→移設。

## Frame 8
status: outline
src: compositions/frames/08-explode.html
start: 80
duration: 10
motion: rules — multi-phase-camera (組立→分解), spring-pop-entrance (グループ一覧)
beat: STEP 07 分解図。explode() でサブアセンブリをオフセット。

## Frame 9
status: outline
src: compositions/frames/09-export.html
start: 90
duration: 6
motion: rules — spring-pop-entrance (ファイルカード)
beat: STEP 08 出力。FCStd / STEP / Python スクリプト。

## Frame 10
status: outline
src: compositions/frames/10-outro.html
start: 96
duration: 10
motion: rules — waterfall-entry (締めのタイトル)
beat: ターンテーブル。「画像3枚 → 608行 → 84部品」。AURORA A1 — Built with Claude Code × FreeCAD MCP。
