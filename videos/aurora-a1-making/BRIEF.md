---
workflow: general-video
flow: automation
storyboard: no
message: "コンセプト画像3枚から、AIエージェントがFreeCAD MCPで84部品・12サブアセンブリのF1アッシーを組み上げるまで"
aspect: 1920x1080
language: ja
length: 106s
angle: making-of
---

## Intent

AURORA A1（ユーザーのオリジナルF1コンセプト）のアッシーモデルを、AIエージェント（Claude Code）が
FreeCAD MCP 経由で作り上げたメイキング動画。ユーザーの依頼文「エージェントの作成したフローとかをベースにして」
に沿い、実際のセッションの工程（接続確認 → 画像読み取り → 寸法抽出 → スクリプト → ビルド → 検証と修正 → 分解図 → STEP出力）
を順にたどる。ナレーションなし、日本語テロップ＋BGM。

## Assets

- assets/concept/1.webp, 2.webp, 3.webp — ユーザー提供のコンセプト画像（STEP 02 インプット）
- assets/renders/*.png — FreeCAD から撮影した透過レンダー（hero / exploded / stage_1-6 / wing_before・after / side_ortho）
- assets/renders/turntable.mp4 — 240フレームのターンテーブル（背景焼き込み、クロージング用）
- assets/audio/bgm.mp3 (= .media bgm_001) — scripts/synth_bgm.py で生成したオリジナルBGM（120BPM、シーン境界に小節を合わせた構成）

## Notes

- 数値は実セッションの実測値のみ使用：初回ビルド 53.8s・invalid 0・bbox 5640×2002×965、部品ソリッド 84 / App::Part 12 / ドキュメントオブジェクト 192、STEP 10,733,035 bytes。
- 「約190部品」は誤り（192はOrigin等を含むオブジェクト総数）。動画では 84 部品 / 12 サブアセンブリと表記する。
- HeyGen 未サインイン・ローカル音楽エンジン未導入のため、BGM は手続き的に合成したオリジナル音源。
