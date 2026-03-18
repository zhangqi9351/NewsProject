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
                all_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.get('summary', ''),
                    'source': source['name']
                })
        except Exception as e:
            print(f"⚠️ 无法抓取 {source['name']}: {e}")
    return all_articles