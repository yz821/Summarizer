"""
ニュース要約ツール (v2)
RSSフィードからニュースを取得し、Claude APIで要約してファイルに保存する
GitHub Actionsでの自動実行を想定

事前準備:
    pip install feedparser anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."

実行:
    python news_summarizer.py
"""

import os
from datetime import datetime
import feedparser
import anthropic

# 要約したいRSSフィードのURL一覧(お好みで追加・変更してください)
RSS_FEEDS = {
    "NHKニュース": "https://www.nhk.or.jp/rss/news/cat0.xml",
}

MAX_ARTICLES_PER_FEED = 5
MODEL = "claude-sonnet-5"


def fetch_articles() -> list[dict]:
    """各RSSフィードから記事を取得する"""
    articles = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
            articles.append({
                "source": source,
                "title": entry.title,
                "link": entry.link,
                "summary": getattr(entry, "summary", ""),
            })
    return articles


def build_prompt(articles: list[dict]) -> str:
    combined = "\n\n".join(
        f"[{a['source']}] {a['title']}\n{a['summary']}\nURL: {a['link']}"
        for a in articles
    )
    return (
        "以下は本日のニュース一覧です。重要なニュースを5つ選び、"
        "それぞれ2〜3文で要約してください。出力は日本語で、"
        "見出し + 要約の形式にしてください。\n\n"
        f"{combined}"
    )


def summarize(articles: list[dict], client: anthropic.Anthropic) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": build_prompt(articles)}],
    )
    text_parts = [block.text for block in message.content if block.type == "text"]
    return "\n".join(text_parts)

def save_summary(summary: str) -> str:
    """要約結果を日付付きファイルとして summaries/ 以下に保存する"""
    os.makedirs("summaries", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path = f"summaries/{today}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {today} のニュース要約\n\n{summary}\n")
    return path


def main():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    articles = fetch_articles()
    print(f"{len(articles)}件の記事を取得しました。要約中...\n")
    summary = summarize(articles, client)
    path = save_summary(summary)
    print(f"保存しました: {path}")


if __name__ == "__main__":
    main()
