"""Gemini API との通信をまとめたモジュール。"""

import time
from collections.abc import Iterator

from google import genai
from google.genai import errors, types

# 指定したモデルが混雑しているときに、順番に試す予備のモデル
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite"]
RETRY_CODES = {429, 500, 503}  # 待てば直る可能性があるエラー
RETRIES_PER_MODEL = 2


def stream_text(
    api_key: str,
    model: str,
    system_instruction: str,
    prompt: str,
    temperature: float = 0.7,
    files: list[tuple[bytes, str]] | None = None,
) -> Iterator[str]:
    """Gemini に問い合わせ、生成されたテキストを少しずつ返す。

    混雑エラーのときは少し待って再試行し、それでもだめなら予備のモデルに切り替える。
    """
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        # 関数呼び出しは使わないので無効にする（不要な警告も出なくなる）
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    # PDF などの添付ファイルは、指示文の前に並べて送る
    contents = [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in files or []]
    contents.append(prompt)

    models = [model] + [m for m in FALLBACK_MODELS if m != model]
    last_error = None
    for current in models:
        for attempt in range(RETRIES_PER_MODEL):
            started = False
            try:
                for chunk in client.models.generate_content_stream(
                    model=current, contents=contents, config=config
                ):
                    if chunk.text:
                        started = True
                        yield chunk.text
                return
            except errors.APIError as e:
                # 途中まで出力済みなら、やり直すと文章が重複するのでそのままエラーにする
                if started or e.code not in RETRY_CODES:
                    raise
                last_error = e
                time.sleep(2 * (attempt + 1))
    raise last_error
