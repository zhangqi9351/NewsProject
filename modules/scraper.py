import feedparser

def fetch_all_rss(sources):
    """
    抓取配置中所有的 RSS 源
    """
    all_articles = []
    for source in sources:
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries:
                try:
                    title = getattr(entry, 'title', '').strip()
                    link = getattr(entry, 'link', '').strip()

                    if not title or not link:
                        continue

                    all_articles.append({
                        'title': title,
                        'link': link,
                        'summary': entry.get('summary', ''),
                        'source': source.get('name', '未知来源')
                    })
                except Exception as entry_error:
                    print(f"⚠️ 文章解析失败，已跳过单条记录: {entry_error}")
        except Exception as e:
            print(f"⚠️ 无法抓取 {source.get('name', '未知来源')}: {e}")
    return all_articles
