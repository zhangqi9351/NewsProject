import feedparser

def fetch_all_rss(sources):
    """
    抓取配置中所有的 RSS 源
    """
    all_articles = []
    errors = []
    seen_links = set()

    for source in sources:
        source_name = str(source.get('name', '未知来源')).strip() or '未知来源'
        source_url = str(source.get('url', '')).strip()

        if not source_url:
            errors.append(f"{source_name}: 缺少 URL 配置")
            continue

        try:
            feed = feedparser.parse(source_url, agent="NewsProject/1.0 (+Streamlit)")
            if getattr(feed, 'bozo', 0) and not getattr(feed, 'entries', []):
                bozo_error = getattr(feed, 'bozo_exception', '未知解析错误')
                errors.append(f"{source_name}: RSS 解析失败 ({bozo_error})")
                continue

            for entry in feed.entries:
                try:
                    title = getattr(entry, 'title', '').strip()
                    link = getattr(entry, 'link', '').strip()

                    if not title or not link or link in seen_links:
                        continue

                    seen_links.add(link)
                    all_articles.append({
                        'title': title,
                        'link': link,
                        'summary': entry.get('summary', ''),
                        'source': source_name
                    })
                except Exception as entry_error:
                    errors.append(f"{source_name}: 单条文章解析失败 ({entry_error})")
        except Exception as e:
            errors.append(f"{source_name}: 无法抓取 ({e})")

    return {
        "articles": all_articles,
        "errors": errors,
        "source_count": len(sources),
        "article_count": len(all_articles),
    }
