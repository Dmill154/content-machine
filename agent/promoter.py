"""
Auto Promotion Engine
=====================
Automatically promotes content across multiple channels.
Handles social media posting, search engine submission, and backlink building.
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import re


class AutoPromoter:
    """
    Autonomous content promotion engine.
    Submits to search engines, posts to social media, builds backlinks.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        self.promotion_log = self.data_dir / "promotion_log.json"
        self.site_url = config.get('site', {}).get('base_url', '')

        # Load promotion history
        self.history = self._load_history()

    def _load_history(self) -> dict:
        """Load promotion history."""
        if self.promotion_log.exists():
            with open(self.promotion_log, 'r') as f:
                return json.load(f)
        return {
            "google_submitted": False,
            "bing_submitted": False,
            "promoted_articles": [],
            "last_promotion": None
        }

    def _save_history(self):
        """Save promotion history."""
        with open(self.promotion_log, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)

    async def submit_to_google(self) -> bool:
        """
        Submit sitemap to Google Search Console.
        Note: For full automation, you'd need Google Search Console API setup.
        This creates the ping URL for manual or automated submission.
        """
        sitemap_url = f"{self.site_url}/sitemap.xml"
        ping_url = f"https://www.google.com/ping?sitemap={sitemap_url}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ping_url) as response:
                    if response.status == 200:
                        self.history["google_submitted"] = True
                        self.history["google_submit_date"] = datetime.now().isoformat()
                        self._save_history()
                        print(f"[OK] Submitted sitemap to Google")
                        return True
        except Exception as e:
            print(f"[WARN] Google ping failed: {e}")

        return False

    async def submit_to_bing(self) -> bool:
        """Submit sitemap to Bing Webmaster."""
        sitemap_url = f"{self.site_url}/sitemap.xml"
        ping_url = f"https://www.bing.com/ping?sitemap={sitemap_url}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ping_url) as response:
                    if response.status == 200:
                        self.history["bing_submitted"] = True
                        self.history["bing_submit_date"] = datetime.now().isoformat()
                        self._save_history()
                        print(f"[OK] Submitted sitemap to Bing")
                        return True
        except Exception as e:
            print(f"[WARN] Bing ping failed: {e}")

        return False

    async def submit_to_indexnow(self, urls: List[str]) -> bool:
        """
        Submit URLs to IndexNow (instant indexing for Bing, Yandex, etc.)
        """
        # IndexNow requires an API key file on your domain
        # For now, we'll use the basic ping method
        print(f"[INFO] IndexNow: Would submit {len(urls)} URLs")
        return True

    def generate_social_posts(self, article: Dict) -> Dict[str, str]:
        """
        Generate social media posts for an article.
        Returns dict with platform-specific content.
        """
        title = article.get('title', '')
        slug = article.get('slug', '')
        keyword = article.get('keyword', '')
        url = f"{self.site_url}/{slug}/"

        posts = {}

        # Twitter/X post (280 chars)
        twitter_post = f"{title}\n\n{url}\n\n#homeoffice #wfh #desksetup #workfromhome"
        if len(twitter_post) > 280:
            twitter_post = f"{title[:200]}...\n\n{url}"
        posts['twitter'] = twitter_post

        # Reddit post
        posts['reddit'] = {
            "title": title,
            "url": url,
            "subreddits": self._get_relevant_subreddits(keyword)
        }

        # Pinterest post
        posts['pinterest'] = {
            "title": title,
            "description": f"{title} - Find the best budget options for your home office setup. Click to read our full guide!",
            "link": url,
            "board": "Home Office Ideas"
        }

        # Facebook post
        posts['facebook'] = f"{title}\n\nLooking to upgrade your home office without breaking the bank? Check out our latest guide!\n\n{url}"

        return posts

    def _get_relevant_subreddits(self, keyword: str) -> List[str]:
        """Get relevant subreddits for a keyword."""
        keyword_lower = keyword.lower()

        subreddits = ["homeoffice", "workfromhome", "battlestations"]

        if "desk" in keyword_lower:
            subreddits.extend(["Workspaces", "desksetup"])
        if "chair" in keyword_lower:
            subreddits.extend(["OfficeChairs", "Ergonomics"])
        if "monitor" in keyword_lower:
            subreddits.extend(["Monitors", "buildapc"])
        if "keyboard" in keyword_lower:
            subreddits.extend(["MechanicalKeyboards", "keyboards"])
        if "lighting" in keyword_lower or "lamp" in keyword_lower:
            subreddits.extend(["Lighting", "CozyPlaces"])

        return list(set(subreddits))[:5]

    async def auto_promote_article(self, article: Dict) -> Dict:
        """
        Automatically promote an article across channels.
        Returns promotion results.
        """
        results = {
            "article_id": article.get('id'),
            "timestamp": datetime.now().isoformat(),
            "channels": {}
        }

        # Generate posts
        posts = self.generate_social_posts(article)

        # For now, save the posts for manual sharing or future automation
        # Full automation would require API keys for each platform

        results["channels"]["generated_posts"] = posts
        results["status"] = "posts_generated"

        # Log promotion
        self.history["promoted_articles"].append({
            "id": article.get('id'),
            "slug": article.get('slug'),
            "promoted_at": datetime.now().isoformat()
        })
        self.history["last_promotion"] = datetime.now().isoformat()
        self._save_history()

        return results

    async def run_promotion_cycle(self, articles: List[Dict]) -> Dict:
        """
        Run a full promotion cycle.
        """
        results = {
            "search_engines": {},
            "articles_promoted": 0
        }

        # Submit sitemaps to search engines
        results["search_engines"]["google"] = await self.submit_to_google()
        results["search_engines"]["bing"] = await self.submit_to_bing()

        # Promote new articles
        for article in articles:
            article_id = article.get('id')
            # Check if already promoted
            promoted_ids = [p['id'] for p in self.history.get('promoted_articles', [])]
            if article_id not in promoted_ids:
                await self.auto_promote_article(article)
                results["articles_promoted"] += 1

        return results

    def get_promotion_status(self) -> Dict:
        """Get current promotion status."""
        return {
            "google_submitted": self.history.get("google_submitted", False),
            "bing_submitted": self.history.get("bing_submitted", False),
            "total_promoted": len(self.history.get("promoted_articles", [])),
            "last_promotion": self.history.get("last_promotion")
        }


class PinterestPromoter:
    """
    Pinterest automation for driving traffic.
    Pinterest is great for home office content - visual + high purchase intent.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path("data")
        self.pins_queue = self.data_dir / "pinterest_queue.json"

    def generate_pin_ideas(self, article: Dict) -> List[Dict]:
        """Generate Pinterest pin ideas for an article."""
        title = article.get('title', '')
        keyword = article.get('keyword', '')
        url = f"{self.config.get('site', {}).get('base_url', '')}/{article.get('slug')}/"

        pins = []

        # Main pin
        pins.append({
            "title": title,
            "description": f"{title} | Budget-friendly picks for your home office. Save money without sacrificing quality! #homeoffice #wfh #desksetup",
            "link": url,
            "board": "Home Office Setup Ideas"
        })

        # Listicle pin
        if "best" in keyword.lower():
            pins.append({
                "title": f"Top Picks: {keyword.title()}",
                "description": f"Looking for {keyword}? We've tested the best options for every budget. Click to see our top recommendations!",
                "link": url,
                "board": "Budget Office Gear"
            })

        return pins

    def queue_pins(self, pins: List[Dict]):
        """Add pins to the queue for posting."""
        queue = []
        if self.pins_queue.exists():
            with open(self.pins_queue, 'r') as f:
                queue = json.load(f)

        queue.extend(pins)

        with open(self.pins_queue, 'w') as f:
            json.dump(queue, f, indent=2)


class RedditPromoter:
    """
    Reddit promotion helper.
    Note: Be careful with Reddit - they don't like spam.
    Focus on being helpful, not promotional.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path("data")
        self.reddit_log = self.data_dir / "reddit_posts.json"

        # Subreddits that allow self-promotion (with rules)
        self.allowed_subreddits = {
            "homeoffice": {"self_promo_day": "saturday", "karma_req": 100},
            "workfromhome": {"self_promo_day": None, "karma_req": 50},
            "Workspaces": {"self_promo_day": None, "karma_req": 100},
            "battlestations": {"self_promo_day": None, "karma_req": 50},
        }

    def generate_reddit_content(self, article: Dict) -> Dict:
        """
        Generate Reddit-friendly content.
        Focus on being helpful, not salesy.
        """
        title = article.get('title', '')
        keyword = article.get('keyword', '')

        # Reddit-style title (question or discussion format)
        reddit_titles = [
            f"I researched {keyword} so you don't have to - here's what I found",
            f"Comparison: {keyword} - which one is actually worth it?",
            f"After hours of research on {keyword}, here are my top picks",
        ]

        return {
            "suggested_titles": reddit_titles,
            "body_template": f"""Hey everyone!

I've been researching {keyword} and put together a guide comparing the best options at different price points.

**Quick Summary:**
- Best Budget Option: [Product Name]
- Best Mid-Range: [Product Name]
- Best Premium: [Product Name]

[Full article with detailed comparisons]({self.config.get('site', {}).get('base_url', '')}/{article.get('slug')}/)

Happy to answer any questions!

---
*Disclaimer: Article contains affiliate links*""",
            "target_subreddits": self._get_subreddits_for_keyword(keyword)
        }

    def _get_subreddits_for_keyword(self, keyword: str) -> List[str]:
        """Get best subreddits for a keyword."""
        kw = keyword.lower()

        subs = ["homeoffice"]

        if "chair" in kw:
            subs.extend(["OfficeChairs", "Ergonomics", "BuyItForLife"])
        if "desk" in kw:
            subs.extend(["desksetup", "Workspaces", "StandingDesk"])
        if "monitor" in kw:
            subs.extend(["Monitors", "ultrawidemasterrace", "buildapc"])
        if "keyboard" in kw:
            subs.extend(["MechanicalKeyboards", "keyboards", "ergonomics"])

        return list(set(subs))
