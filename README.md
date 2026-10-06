# ✍️ AIライティングツール

Streamlit と Gemini API で作った、個人用のAIライティングツールです。

## 機能

| ツール | 内容 |
| --- | --- |
| 📝 ブログ記事作成 | テーマ・キーワード・読者・文体・文字数から記事を作成（構成案のみも可） |
| ✉️ メール返信 | 受信メールと返信の方向性から返信文を作成（最大3パターン） |
| 📋 文章要約 | 文章や PDF（20MBまで、スキャンも可）を箇条書き・3行まとめ・議事録風などの形式で要約 |
| 🔍 文章校正 | 修正後の全文と、修正点の一覧（表）を出力 |
| 🔄 リライト・トーン変換 | 丁寧に／カジュアルに／短く などの書き換え |
| 🌐 翻訳 | 7言語に対応、意訳・直訳・ビジネス向けを選択 |
| 📣 SNS投稿作成 | X・Instagram・LinkedIn などに合った投稿文 |
| 💡 タイトル・コピー案 | タイトルやキャッチコピーをまとめて提案 |
| ✨ フリー入力 | 自由に指示して文章を作成 |

結果は「プレビュー」と「コピー用テキスト」で表示され、Markdown ファイルとして保存できます。
サイドバーには、そのセッションの生成履歴が残ります。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # .env を開いて GEMINI_API_KEY を記入
```

APIキーは [Google AI Studio](https://aistudio.google.com/apikey) で取得できます。
（.env を使わず、画面のサイドバーから入力することもできます）

## 起動

Finder で `start.command` をダブルクリックすると、ブラウザでアプリが開きます。
ターミナルから起動する場合は次のコマンドです。

```bash
.venv/bin/streamlit run app.py
```

Gemini が混み合っているときは自動で再試行し、それでもだめなら予備のモデル
（`gemini-3.5-flash` → `gemini-3.5-flash-lite`）に切り替えます。

## ファイル構成

- `app.py` … 画面（サイドバー、結果の表示、履歴）
- `tools.py` … 各ツールの入力フォームとプロンプト。ツールを増やすときはここに関数を足して `TOOLS` に登録
- `gemini_client.py` … Gemini API の呼び出し（ストリーミング、PDF添付、混雑時の再試行）
- `start.command` … ダブルクリック用の起動スクリプト
- `.streamlit/config.toml` … Streamlit の設定
