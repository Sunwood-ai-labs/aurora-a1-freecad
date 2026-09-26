---
workflow: general-video
flow: automation
storyboard: no
message: "AIエージェントが FreeCAD TechDraw で AURORA A1 の図面一式（A3・11枚、断面9箇所、部品表84点）を出図するまで"
aspect: 1920x1080
language: ja
length: 90-110s
angle: making-of
---

## Intent

前作 videos/aurora-a1-making と同じ形式（ユーザー指定「前回と同じ形式で」）で、出図工程のメイキング動画。
デザイン（frame.md のビルドログ風・紫アクセント・Noto Sans JP + JetBrains Mono）、HUD/進行バー/走査線ワイプ、
手続き合成BGM（scripts/synth_bgm.py を流用）、ナレーションなし・日本語テロップを踏襲する。

## Flow to tell (実セッションの事実のみ)

1. 「FreeCADで出図ってできる？」→ TechDraw ワークベンチで可能
2. 要望：部品ごとの寸法＋断面図 → A3 11枚の構成を設計
3. 試作ページ：テンプレート・寸法API（makeExtentDim / makeDistanceDim）・断面・PDF出力を検証
4. 問題と対策：
   - 投影が非同期（エッジ0本）→ Qt イベントを回して完了待ち
   - ポリゴン翼型ロフトの辺で図が真っ黒 → 翼型を B-spline 化してモデル再構築（主翼 3面・3辺）
   - テンプレートが出ない → ページを GUI で開いてから PDF 出力
   - 寸法が図に重なる・小数表示 → 外形の外へ配置、%.0f
   - makeDistanceDim はスケール後座標（10倍ずれ）→ 座標×縮尺
   - 90秒タイムアウト → シートをジェネレータ化して段階実行
   - モノコックの輪郭欠け → CoarseView
5. 成果：01 総組立 / 02 縦断面 A-A / 03 FW (B-B) / 04 RW (C-C) / 05 モノコック (D,E,F) /
   06 ボディ (G,H) / 07 ホイール (J,K) / 08 サスペンション / 09 PU (L) / 10-11 部品表 84点、PDF+DXF

## Assets

- ../../aurora_a1/drawings/*.pdf — 完成図面（ラスタ化して素材に使う）
- ../../aurora_a1/make_drawings.py — コード抜粋用
- ../aurora-a1-making/scripts/synth_bgm.py, assets/renders/plate_bg.png — 流用
