"""
Site Publisher Module
=====================
Builds and publishes the static site from generated content.
Handles site generation, deployment, and sitemap creation.
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import markdown
from jinja2 import Environment, FileSystemLoader
import re


class SitePublisher:
    """
    Autonomous site publisher.
    Builds static HTML from markdown content and deploys to hosting.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path("data")
        self.content_dir = Path("site/content")
        self.templates_dir = Path("site/templates")
        self.output_dir = Path("site/public")
        self.static_dir = Path("site/static")

        # Ensure directories exist
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.articles_file = self.data_dir / "articles.json"
        self.pending_file = self.data_dir / "pending_articles.json"

        # Initialize markdown processor
        self.md = markdown.Markdown(extensions=['meta', 'tables', 'fenced_code', 'toc'])

        # Initialize Jinja2
        self._ensure_templates()
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.templates_dir)))

    def _ensure_templates(self):
        """Ensure HTML templates exist."""
        base_template = self.templates_dir / "base.html"
        if not base_template.exists():
            self._create_default_templates()

    def _create_default_templates(self):
        """Create default HTML templates."""
        # Base template
        base_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{{ meta_description }}">
    <title>{{ title }} | {{ site_name }}</title>
    <link rel="canonical" href="{{ canonical_url }}">
    <link rel="stylesheet" href="/css/style.css">
    <!-- Google tag (gtag.js) - Replace GA_MEASUREMENT_ID -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'GA_MEASUREMENT_ID');
    </script>
</head>
<body>
    <header>
        <nav>
            <a href="/" class="logo">{{ site_name }}</a>
            <ul>
                {% for cat in categories %}
                <li><a href="/{{ cat }}/">{{ cat|title }}</a></li>
                {% endfor %}
            </ul>
        </nav>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        <p>&copy; {{ year }} {{ site_name }}. All rights reserved.</p>
        <p><small>As an Amazon Associate, we earn from qualifying purchases.</small></p>
    </footer>
</body>
</html>'''

        # Article template
        article_html = '''{% extends "base.html" %}
{% block content %}
<article class="post">
    <header class="post-header">
        <h1>{{ title }}</h1>
        <div class="meta">
            <span class="category">{{ category|title }}</span>
            <time datetime="{{ date }}">{{ date_formatted }}</time>
        </div>
    </header>
    <div class="post-content">
        {{ content|safe }}
    </div>
    <footer class="post-footer">
        <p>Last updated: {{ date_formatted }}</p>
    </footer>
</article>
{% endblock %}'''

        # Index template
        index_html = '''{% extends "base.html" %}
{% block content %}
<section class="hero">
    <h1>{{ site_tagline }}</h1>
    <p>Expert reviews and recommendations for your home office setup.</p>
</section>
<section class="latest-posts">
    <h2>Latest Articles</h2>
    <div class="posts-grid">
        {% for article in articles[:12] %}
        <article class="post-card">
            <a href="/{{ article.slug }}/">
                <h3>{{ article.title }}</h3>
                <p>{{ article.meta_description[:100] }}...</p>
                <span class="category">{{ article.category|title }}</span>
            </a>
        </article>
        {% endfor %}
    </div>
</section>
<section class="categories">
    <h2>Browse by Category</h2>
    <div class="category-grid">
        {% for cat in categories %}
        <a href="/{{ cat }}/" class="category-card">
            <h3>{{ cat|title }}</h3>
        </a>
        {% endfor %}
    </div>
</section>
{% endblock %}'''

        # Category template
        category_html = '''{% extends "base.html" %}
{% block content %}
<section class="category-page">
    <h1>{{ category|title }}</h1>
    <p>Browse our {{ category }} guides and reviews.</p>
    <div class="posts-grid">
        {% for article in articles %}
        <article class="post-card">
            <a href="/{{ article.slug }}/">
                <h3>{{ article.title }}</h3>
                <p>{{ article.meta_description[:100] }}...</p>
            </a>
        </article>
        {% endfor %}
    </div>
</section>
{% endblock %}'''

        # Write templates
        (self.templates_dir / "base.html").write_text(base_html)
        (self.templates_dir / "article.html").write_text(article_html)
        (self.templates_dir / "index.html").write_text(index_html)
        (self.templates_dir / "category.html").write_text(category_html)

        # Create CSS
        self._create_default_css()

    def _create_default_css(self):
        """Create default stylesheet."""
        css_dir = self.static_dir / "css"
        css_dir.mkdir(parents=True, exist_ok=True)

        css = '''/* Budget Office Setup - Styles */
:root {
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --text: #1f2937;
    --text-light: #6b7280;
    --bg: #ffffff;
    --bg-alt: #f9fafb;
    --border: #e5e7eb;
    --max-width: 1200px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg);
}

header {
    border-bottom: 1px solid var(--border);
    padding: 1rem;
}

nav {
    max-width: var(--max-width);
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary);
    text-decoration: none;
}

nav ul {
    display: flex;
    list-style: none;
    gap: 2rem;
}

nav a {
    color: var(--text);
    text-decoration: none;
}

nav a:hover {
    color: var(--primary);
}

main {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 2rem 1rem;
}

.hero {
    text-align: center;
    padding: 4rem 0;
    background: var(--bg-alt);
    margin: -2rem -1rem 2rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.posts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.post-card {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    transition: box-shadow 0.2s;
}

.post-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.post-card a {
    text-decoration: none;
    color: inherit;
}

.post-card h3 {
    color: var(--text);
    margin-bottom: 0.5rem;
}

.post-card p {
    color: var(--text-light);
    font-size: 0.9rem;
}

.category {
    display: inline-block;
    background: var(--bg-alt);
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    margin-top: 1rem;
    color: var(--primary);
}

.post-header {
    margin-bottom: 2rem;
}

.post-header h1 {
    font-size: 2rem;
    margin-bottom: 1rem;
}

.meta {
    color: var(--text-light);
    font-size: 0.9rem;
}

.post-content {
    max-width: 800px;
}

.post-content h2 {
    margin-top: 2rem;
    margin-bottom: 1rem;
}

.post-content h3 {
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
}

.post-content p {
    margin-bottom: 1rem;
}

.post-content ul, .post-content ol {
    margin-bottom: 1rem;
    padding-left: 2rem;
}

.post-content li {
    margin-bottom: 0.5rem;
}

.post-content a {
    color: var(--primary);
}

.post-content a:hover {
    text-decoration: underline;
}

.post-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.post-content th, .post-content td {
    border: 1px solid var(--border);
    padding: 0.75rem;
    text-align: left;
}

.post-content th {
    background: var(--bg-alt);
}

.category-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 2rem;
}

.category-card {
    background: var(--bg-alt);
    padding: 2rem;
    border-radius: 8px;
    text-align: center;
    text-decoration: none;
    color: var(--text);
    transition: background 0.2s;
}

.category-card:hover {
    background: var(--primary);
    color: white;
}

footer {
    border-top: 1px solid var(--border);
    padding: 2rem 1rem;
    text-align: center;
    color: var(--text-light);
    margin-top: 4rem;
}

@media (max-width: 768px) {
    nav {
        flex-direction: column;
        gap: 1rem;
    }

    nav ul {
        gap: 1rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    .hero h1 {
        font-size: 1.75rem;
    }
}'''

        (css_dir / "style.css").write_text(css)

    async def publish_pending(self) -> int:
        """Publish all pending articles. Returns count of published articles."""
        if not self.pending_file.exists():
            return 0

        with open(self.pending_file, 'r') as f:
            pending = json.load(f)

        if not pending:
            return 0

        # Load existing articles
        articles = []
        if self.articles_file.exists():
            with open(self.articles_file, 'r') as f:
                articles = json.load(f)

        published_count = 0
        remaining_pending = []

        for article_meta in pending:
            # Read the markdown file
            md_file = self.content_dir / f"{article_meta['slug']}.md"
            if not md_file.exists():
                remaining_pending.append(article_meta)
                continue

            # Update status
            article_meta['status'] = 'published'
            article_meta['published_at'] = datetime.now().isoformat()

            # Add to published articles
            articles.append(article_meta)
            published_count += 1

        # Save updated articles list
        with open(self.articles_file, 'w') as f:
            json.dump(articles, f, indent=2)

        # Save remaining pending
        with open(self.pending_file, 'w') as f:
            json.dump(remaining_pending, f, indent=2)

        return published_count

    async def rebuild_site(self):
        """Rebuild the entire static site."""
        # Clean output directory
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

        # Copy static files
        if self.static_dir.exists():
            shutil.copytree(self.static_dir, self.output_dir / "css", dirs_exist_ok=True)

        # Load articles
        articles = []
        if self.articles_file.exists():
            with open(self.articles_file, 'r') as f:
                articles = json.load(f)

        # Sort by date (newest first)
        articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)

        categories = self.config['niche']['categories']

        # Common template context
        common_context = {
            'site_name': self.config['site']['name'],
            'site_tagline': self.config['site']['tagline'],
            'categories': categories,
            'year': datetime.now().year,
        }

        # Build index page
        self._build_index(articles, common_context)

        # Build category pages
        for category in categories:
            self._build_category_page(category, articles, common_context)

        # Build article pages
        for article in articles:
            self._build_article_page(article, common_context)

        # Generate sitemap
        self._generate_sitemap(articles)

        # Generate robots.txt
        self._generate_robots()

    def _build_index(self, articles: List[Dict], context: Dict):
        """Build the homepage."""
        template = self.jinja_env.get_template('index.html')

        html = template.render(
            **context,
            title=self.config['site']['name'],
            meta_description=f"{self.config['site']['tagline']} - Expert reviews and buying guides.",
            canonical_url=self.config['site']['base_url'],
            articles=articles,
        )

        (self.output_dir / "index.html").write_text(html)

    def _build_category_page(self, category: str, all_articles: List[Dict], context: Dict):
        """Build a category page."""
        template = self.jinja_env.get_template('category.html')

        cat_articles = [a for a in all_articles if a.get('category') == category]

        cat_dir = self.output_dir / category
        cat_dir.mkdir(exist_ok=True)

        html = template.render(
            **context,
            title=f"{category.title()} - {self.config['site']['name']}",
            meta_description=f"Best {category} for your home office. Reviews, comparisons and buying guides.",
            canonical_url=f"{self.config['site']['base_url']}/{category}/",
            category=category,
            articles=cat_articles,
        )

        (cat_dir / "index.html").write_text(html)

    def _build_article_page(self, article: Dict, context: Dict):
        """Build an individual article page."""
        template = self.jinja_env.get_template('article.html')

        # Read markdown content
        md_file = self.content_dir / f"{article['slug']}.md"
        if not md_file.exists():
            return

        md_content = md_file.read_text(encoding='utf-8')

        # Remove frontmatter
        if md_content.startswith('---'):
            parts = md_content.split('---', 2)
            if len(parts) >= 3:
                md_content = parts[2]

        # Convert to HTML
        self.md.reset()
        html_content = self.md.convert(md_content)

        # Add affiliate links
        html_content = self._add_affiliate_links(html_content)

        # Create article directory
        article_dir = self.output_dir / article['slug']
        article_dir.mkdir(exist_ok=True)

        # Format date
        date_obj = datetime.fromisoformat(article.get('published_at', article['created_at']))
        date_formatted = date_obj.strftime('%B %d, %Y')

        html = template.render(
            **context,
            title=article['title'],
            meta_description=article.get('meta_description', ''),
            canonical_url=f"{self.config['site']['base_url']}/{article['slug']}/",
            content=html_content,
            category=article.get('category', 'general'),
            date=article.get('published_at', article['created_at']),
            date_formatted=date_formatted,
        )

        (article_dir / "index.html").write_text(html)

    def _add_affiliate_links(self, html: str) -> str:
        """Add affiliate tags to Amazon links."""
        tag = self.config['affiliate']['amazon_associate_tag']
        if not tag or tag == "YOUR-TAG-20":
            return html

        # Add affiliate tag to Amazon links
        amazon_pattern = r'(https?://(?:www\.)?amazon\.com/[^\s"\'<>]+)'

        def add_tag(match):
            url = match.group(1)
            if 'tag=' not in url:
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}tag={tag}"
            return url

        return re.sub(amazon_pattern, add_tag, html)

    def _generate_sitemap(self, articles: List[Dict]):
        """Generate XML sitemap."""
        base_url = self.config['site']['base_url']

        urls = [
            f'<url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>'
        ]

        # Category pages
        for cat in self.config['niche']['categories']:
            urls.append(f'<url><loc>{base_url}/{cat}/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')

        # Article pages
        for article in articles:
            date = article.get('published_at', article['created_at'])[:10]
            urls.append(f'<url><loc>{base_url}/{article["slug"]}/</loc><lastmod>{date}</lastmod><priority>0.7</priority></url>')

        sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''

        (self.output_dir / "sitemap.xml").write_text(sitemap)

    def _generate_robots(self):
        """Generate robots.txt."""
        base_url = self.config['site']['base_url']
        robots = f'''User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml'''

        (self.output_dir / "robots.txt").write_text(robots)

    def get_stats(self) -> Dict:
        """Get publisher statistics."""
        articles = []
        if self.articles_file.exists():
            with open(self.articles_file, 'r') as f:
                articles = json.load(f)

        pending = []
        if self.pending_file.exists():
            with open(self.pending_file, 'r') as f:
                pending = json.load(f)

        return {
            "published": len(articles),
            "pending": len(pending),
            "categories": len(self.config['niche']['categories']),
        }
