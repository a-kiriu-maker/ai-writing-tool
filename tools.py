"""各ライティングツールの入力フォームとプロンプトの定義。

ツールを追加するときは、入力フォームを描画して Request を返す関数を書き、
TOOLS に登録する。
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import streamlit as st

MAX_PDF_MB = 20  # Gemini にそのまま送れるサイズの目安

BASE_SYSTEM = (
    "あなたは日本語の文章作成に長けたプロのライターです。"
    "指示された条件を守り、自然で読みやすい日本語で出力してください。"
    "前置きや「承知しました」などの返事は書かず、成果物だけを出力してください。"
)


@dataclass
class Request:
    """Gemini に送る内容。"""

    system: str
    prompt: str
    temperature: float = 0.7
    files: list[tuple[bytes, str]] = field(default_factory=list)  # (データ, MIMEタイプ)


@dataclass
class Tool:
    key: str
    label: str
    icon: str
    description: str
    render: Callable[[], Request | None]


def _require(*values: str) -> bool:
    """必須項目が空ならエラーを出して False を返す。"""
    if all(v.strip() for v in values):
        return True
    st.error("必須項目（*）を入力してください。")
    return False


# ---------------------------------------------------------------- ブログ記事
def blog_writer() -> Request | None:
    with st.form("blog"):
        theme = st.text_input("記事のテーマ *", placeholder="例：初心者向けの家庭菜園の始め方")
        keywords = st.text_input("入れたいキーワード（カンマ区切り）", placeholder="例：ベランダ, ミニトマト, プランター")
        col1, col2 = st.columns(2)
        reader = col1.text_input("想定読者", placeholder="例：一人暮らしの20代")
        tone = col2.selectbox("文体", ["です・ます調（丁寧）", "だ・である調", "カジュアル・親しみやすい", "専門的・論理的"])
        col3, col4 = st.columns(2)
        length = col3.select_slider("文字数の目安", [800, 1500, 2500, 4000, 6000], value=2500)
        output = col4.radio("出力", ["本文まで書く", "構成案（見出し）だけ"], horizontal=True)
        notes = st.text_area("その他の要望", placeholder="例：自分の体験談を交えた雰囲気で。最後にまとめを入れて。")
        submitted = st.form_submit_button("記事を作成", type="primary", width="stretch")

    if not submitted or not _require(theme):
        return None

    if output == "構成案（見出し）だけ":
        task = "記事のタイトル案を3つと、H2・H3の見出し構成案を作成してください。各見出しには書く内容を1行で添えてください。"
    else:
        task = (
            f"約{length}文字のブログ記事を書いてください。"
            "Markdown 形式で、最初に `# タイトル`、続いて導入文、`##` `###` の見出しで構成した本文、最後にまとめを入れてください。"
        )
    prompt = f"""{task}

- テーマ: {theme}
- キーワード: {keywords or "指定なし"}
- 想定読者: {reader or "指定なし"}
- 文体: {tone}
- その他の要望: {notes or "なし"}"""
    return Request(BASE_SYSTEM + "SEOを意識し、読者が最後まで読みたくなる記事を書きます。", prompt, 0.8)


# ---------------------------------------------------------------- メール返信
def email_reply() -> Request | None:
    with st.form("email"):
        received = st.text_area("受信したメール *", height=200, placeholder="返信したいメールの本文を貼り付けてください")
        col1, col2 = st.columns(2)
        intent = col1.selectbox("返信の方向性", ["おまかせ", "承諾・了承する", "丁寧にお断りする", "質問・確認する", "お礼を伝える", "日程を調整する", "謝罪する"])
        relation = col2.selectbox("相手との関係", ["社外（取引先・顧客）", "社内（上司）", "社内（同僚・部下）", "友人・知人"])
        points = st.text_area("返信に入れたい内容", placeholder="例：来週水曜の14時以降なら対応可能。資料は金曜までに送る。")
        sender = st.text_input("署名に使う名前", placeholder="例：山田 太郎")
        variants = st.radio("作成するパターン数", [1, 2, 3], horizontal=True)
        submitted = st.form_submit_button("返信文を作成", type="primary", width="stretch")

    if not submitted or not _require(received):
        return None

    prompt = f"""以下の受信メールに対する返信文を{variants}パターン作成してください。
件名（「Re:」を付けたもの）と本文を書いてください。複数パターンの場合は「## パターン1」のように見出しで区切り、それぞれ少し印象を変えてください。

- 返信の方向性: {intent}
- 相手との関係: {relation}（関係に合った敬語・言葉づかいにする）
- 入れたい内容: {points or "特になし（受信メールの内容から適切に判断）"}
- 署名の名前: {sender or "（名前）"}

--- 受信メール ---
{received}"""
    return Request(BASE_SYSTEM + "ビジネスマナーに沿った、相手に好印象を与えるメールを書きます。", prompt, 0.6)


# ---------------------------------------------------------------- 要約
def summarizer() -> Request | None:
    with st.form("summary"):
        pdf = st.file_uploader("PDFをアップロード", type="pdf", help=f"{MAX_PDF_MB}MBまで。スキャンしたPDFも読み取れます。")
        text = st.text_area("または、要約したい文章を貼り付け", height=200)
        col1, col2 = st.columns(2)
        style = col1.selectbox("形式", ["箇条書き", "文章（段落）", "3行まとめ", "見出し＋箇条書き（議事録風）", "一言で"])
        length = col2.select_slider("詳しさ", ["かなり短く", "短く", "標準", "詳しく"], value="標準")
        focus = st.text_input("特に注目してほしい観点", placeholder="例：決定事項とTODO、数字に関する部分")
        submitted = st.form_submit_button("要約する", type="primary", width="stretch")

    if not submitted:
        return None
    if not pdf and not text.strip():
        st.error("PDFをアップロードするか、文章を貼り付けてください。")
        return None
    if pdf and pdf.size > MAX_PDF_MB * 1024 * 1024:
        st.error(f"PDFが大きすぎます（{pdf.size / 1024 / 1024:.1f}MB）。{MAX_PDF_MB}MB以下のファイルにしてください。")
        return None

    files = []
    sources = []
    if pdf:
        files.append((pdf.getvalue(), "application/pdf"))
        sources.append(f"添付のPDF（{pdf.name}）")
    if text.strip():
        sources.append("下に貼り付けた文章")

    prompt = f"""{"と".join(sources)}の内容を要約してください。原文にない情報は加えないでください。

- 形式: {style}
- 詳しさ: {length}
- 注目する観点: {focus or "指定なし"}"""
    if text.strip():
        prompt += f"\n\n--- 原文 ---\n{text}"
    return Request(BASE_SYSTEM + "文章の要点を正確に読み取り、簡潔にまとめます。", prompt, 0.3, files)


# ---------------------------------------------------------------- 校正
def proofreader() -> Request | None:
    with st.form("proofread"):
        text = st.text_area("校正したい文章 *", height=280)
        level = st.radio("修正の度合い", ["誤字脱字・文法だけ", "読みやすさも改善", "大幅に推敲してよい"], horizontal=True)
        submitted = st.form_submit_button("校正する", type="primary", width="stretch")

    if not submitted or not _require(text):
        return None

    prompt = f"""以下の文章を校正してください。修正の度合いは「{level}」です。

次の形式で出力してください。
## 修正後の文章
（修正後の全文）

## 修正点
| 修正前 | 修正後 | 理由 |
（主な修正点を表で。修正がなければ「修正点はありません」）

--- 原文 ---
{text}"""
    return Request(BASE_SYSTEM + "誤字脱字、文法、表記ゆれ、わかりにくい表現を見逃さない校正者です。", prompt, 0.2)


# ---------------------------------------------------------------- リライト
def rewriter() -> Request | None:
    with st.form("rewrite"):
        text = st.text_area("書き換えたい文章 *", height=240)
        col1, col2 = st.columns(2)
        tone = col1.selectbox("変換先のトーン", ["丁寧なビジネス文", "やわらかく親しみやすい", "カジュアル・フランク", "簡潔・端的", "説得力のある文章", "小学生にもわかる言葉", "ポジティブな言い回し"])
        length = col2.selectbox("長さ", ["ほぼ同じ", "短くする", "長く・詳しくする"])
        submitted = st.form_submit_button("書き換える", type="primary", width="stretch")

    if not submitted or not _require(text):
        return None

    prompt = f"""以下の文章を、意味を保ったまま書き換えてください。

- トーン: {tone}
- 長さ: {length}

--- 原文 ---
{text}"""
    return Request(BASE_SYSTEM, prompt, 0.7)


# ---------------------------------------------------------------- 翻訳
def translator() -> Request | None:
    with st.form("translate"):
        text = st.text_area("翻訳したい文章 *", height=240)
        col1, col2 = st.columns(2)
        target = col1.selectbox("翻訳先の言語", ["英語", "日本語", "中国語（簡体字）", "韓国語", "スペイン語", "フランス語", "ドイツ語"])
        style = col2.selectbox("スタイル", ["自然な意訳", "原文に忠実な直訳", "ビジネス向け", "カジュアル"])
        submitted = st.form_submit_button("翻訳する", type="primary", width="stretch")

    if not submitted or not _require(text):
        return None

    prompt = f"""以下の文章を{target}に翻訳してください（スタイル: {style}）。翻訳文だけを出力してください。

--- 原文 ---
{text}"""
    return Request("あなたはプロの翻訳者です。文脈とニュアンスを正確に汲み取って翻訳します。前置きは書かず、翻訳文だけを出力してください。", prompt, 0.3)


# ---------------------------------------------------------------- SNS投稿
def sns_post() -> Request | None:
    with st.form("sns"):
        content = st.text_area("投稿したい内容 *", height=160, placeholder="例：新しいブログ記事「家庭菜園の始め方」を公開した")
        col1, col2 = st.columns(2)
        platform = col1.selectbox("プラットフォーム", ["X（旧Twitter）", "Instagram", "Threads", "LinkedIn", "Facebook", "note の紹介文"])
        variants = col2.radio("パターン数", [1, 3, 5], index=1, horizontal=True)
        col3, col4 = st.columns(2)
        hashtags = col3.checkbox("ハッシュタグを付ける", value=True)
        emoji = col4.checkbox("絵文字を使う", value=True)
        submitted = st.form_submit_button("投稿文を作成", type="primary", width="stretch")

    if not submitted or not _require(content):
        return None

    prompt = f"""{platform}向けの投稿文を{variants}パターン作成してください。
プラットフォームの文字数制限や文化に合わせ、思わず反応したくなる文章にしてください。
各パターンは「## パターン1」のように見出しで区切ってください。

- 内容: {content}
- ハッシュタグ: {"付ける" if hashtags else "付けない"}
- 絵文字: {"使う" if emoji else "使わない"}"""
    return Request(BASE_SYSTEM + "SNSマーケティングに詳しく、拡散されやすい投稿を書きます。", prompt, 0.9)


# ---------------------------------------------------------------- タイトル・キャッチコピー
def headline() -> Request | None:
    with st.form("headline"):
        content = st.text_area("対象の内容 *", height=160, placeholder="記事・商品・イベントなどの概要")
        col1, col2 = st.columns(2)
        kind = col1.selectbox("種類", ["ブログ記事のタイトル", "キャッチコピー", "メールの件名", "YouTube動画のタイトル", "プレゼン資料のタイトル"])
        count = col2.slider("案の数", 3, 20, 10)
        submitted = st.form_submit_button("案を出す", type="primary", width="stretch")

    if not submitted or not _require(content):
        return None

    prompt = f"""以下の内容について「{kind}」の案を{count}個出してください。
切り口（数字を使う、疑問形、ベネフィット訴求、意外性など）をばらけさせ、番号付きリストで出力してください。
各案の後ろに（ ）で狙いを短く添えてください。最後に「おすすめ」を1つ選び、理由を一言で書いてください。

--- 内容 ---
{content}"""
    return Request(BASE_SYSTEM + "人の目を引く言葉選びが得意なコピーライターです。", prompt, 1.0)


# ---------------------------------------------------------------- フリー入力
def free_prompt() -> Request | None:
    with st.form("free"):
        prompt = st.text_area("指示 *", height=240, placeholder="例：退職する同僚へのメッセージカードの文面を3つ考えて")
        submitted = st.form_submit_button("実行", type="primary", width="stretch")

    if not submitted or not _require(prompt):
        return None
    return Request(BASE_SYSTEM, prompt, 0.7)


TOOLS: list[Tool] = [
    Tool("blog", "ブログ記事作成", "📝", "テーマとキーワードからブログ記事や構成案を作成します。", blog_writer),
    Tool("email", "メール返信", "✉️", "受信したメールに合わせた返信文を考えます。", email_reply),
    Tool("summary", "文章要約", "📋", "長い文章を指定した形式で要約します。", summarizer),
    Tool("proofread", "文章校正", "🔍", "誤字脱字や文法をチェックし、修正点を一覧にします。", proofreader),
    Tool("rewrite", "リライト・トーン変換", "🔄", "文章の雰囲気や長さを変えて書き換えます。", rewriter),
    Tool("translate", "翻訳", "🌐", "自然な文章で多言語に翻訳します。", translator),
    Tool("sns", "SNS投稿作成", "📣", "各SNSに合った投稿文を作成します。", sns_post),
    Tool("headline", "タイトル・コピー案", "💡", "タイトルやキャッチコピーの案をたくさん出します。", headline),
    Tool("free", "フリー入力", "✨", "自由に指示して文章を作成します。", free_prompt),
]
