"""
AI Content Generation Engine
============================
Generates SEO-optimized articles with affiliate links autonomously.
Uses AI to create high-quality, helpful content.
"""

import os
import json
import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import hashlib

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class ContentEngine:
    """
    Autonomous content generation engine.
    Creates SEO-optimized articles with embedded affiliate links.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path("data")
        self.content_dir = Path("site/content")
        self.content_dir.mkdir(parents=True, exist_ok=True)

        self.articles_file = self.data_dir / "articles.json"
        self.pending_file = self.data_dir / "pending_articles.json"

        # Initialize AI client
        self.ai_client = self._init_ai_client()

        # Article templates
        self.article_types = {
            "listicle": self._generate_listicle_prompt,
            "review": self._generate_review_prompt,
            "comparison": self._generate_comparison_prompt,
            "guide": self._generate_guide_prompt,
            "roundup": self._generate_roundup_prompt,
        }

    def _init_ai_client(self):
        """Initialize the AI client (OpenAI or Anthropic)."""
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if openai_key and HAS_OPENAI:
            return AsyncOpenAI(api_key=openai_key)
        elif anthropic_key and HAS_ANTHROPIC:
            return AsyncAnthropic(api_key=anthropic_key)
        else:
            return None

    def _determine_article_type(self, keyword: str) -> str:
        """Determine the best article type for a keyword."""
        keyword_lower = keyword.lower()

        if "vs" in keyword_lower:
            return "comparison"
        elif "best" in keyword_lower and ("under" in keyword_lower or "$" in keyword_lower):
            return "roundup"
        elif "best" in keyword_lower:
            return "listicle"
        elif "review" in keyword_lower:
            return "review"
        elif "how to" in keyword_lower or "setup" in keyword_lower or "guide" in keyword_lower:
            return "guide"
        else:
            return "listicle"  # Default

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title."""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:60]

    def _generate_article_id(self, keyword: str) -> str:
        """Generate unique article ID."""
        hash_input = f"{keyword}-{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    async def generate_article(
        self,
        keyword: str,
        category: str = "general"
    ) -> Optional[Dict]:
        """
        Generate a complete article for a keyword.
        Returns article metadata and saves content to disk.
        """
        article_type = self._determine_article_type(keyword)
        article_id = self._generate_article_id(keyword)

        # Build the prompt
        prompt_builder = self.article_types.get(article_type, self._generate_listicle_prompt)
        system_prompt, user_prompt = prompt_builder(keyword, category)

        # Generate content
        content = await self._call_ai(system_prompt, user_prompt)

        if not content:
            return None

        # Parse the generated content
        article = self._parse_article(content, keyword, category, article_type, article_id)

        if article:
            # Save to pending articles
            self._save_pending_article(article)

            # Save markdown file
            self._save_article_file(article)

        return article

    async def _call_ai(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call the AI API to generate content."""
        if not self.ai_client:
            # Fallback: generate template content without AI
            return self._generate_fallback_content(user_prompt)

        try:
            if isinstance(self.ai_client, AsyncOpenAI):
                response = await self.ai_client.chat.completions.create(
                    model="gpt-4o-mini",  # Cost effective
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.7
                )
                return response.choices[0].message.content

            elif HAS_ANTHROPIC and isinstance(self.ai_client, AsyncAnthropic):
                response = await self.ai_client.messages.create(
                    model="claude-3-haiku-20240307",  # Cost effective
                    max_tokens=3000,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.content[0].text

        except Exception as e:
            print(f"AI API error: {e}")
            return self._generate_fallback_content(user_prompt)

        return None

    def _generate_fallback_content(self, prompt: str) -> str:
        """Generate basic template content when AI is unavailable."""
        # Extract keyword from prompt
        keyword = "home office product"
        if "keyword:" in prompt.lower():
            parts = prompt.split("keyword:")
            if len(parts) > 1:
                keyword = parts[1].split("\n")[0].strip()

        return f"""# {keyword.title()}

## Introduction

Finding the right {keyword} can be challenging with so many options available. In this guide, we'll help you find the perfect solution for your home office needs.

## What to Look For

When shopping for a {keyword}, consider these key factors:

- **Budget**: Determine how much you're willing to spend
- **Quality**: Look for durable materials and good reviews
- **Features**: Identify which features matter most to you
- **Space**: Consider the dimensions and your available space

## Our Top Picks

### Best Overall
A great all-around option that balances quality and value.

### Best Budget Option
Perfect for those watching their wallet without sacrificing quality.

### Premium Pick
For those who want the best of the best.

## Buying Guide

Before making your purchase, consider visiting Amazon to compare prices and read customer reviews. Look for products with high ratings and detailed feedback from verified purchasers.

## Conclusion

Choosing the right {keyword} is an investment in your comfort and productivity. Take your time to evaluate your needs and don't hesitate to read multiple reviews before deciding.

---
*This article contains affiliate links. We may earn a commission if you make a purchase.*
"""

    def _generate_listicle_prompt(self, keyword: str, category: str) -> tuple:
        """Generate prompt for listicle-style article."""
        system_prompt = """You are an expert content writer specializing in home office and remote work products.
You write helpful, detailed, and honest product recommendations. Your content is SEO-optimized but reads naturally.
Always include specific product features, pros/cons, and who each product is best for.
Include natural calls to action encouraging readers to check current prices."""

        user_prompt = f"""Write a comprehensive listicle article for the keyword: "{keyword}"

Category: {category}

Requirements:
1. Start with an engaging H1 title that includes the keyword
2. Write a compelling introduction (100-150 words) that addresses reader pain points
3. List 5-7 products with detailed descriptions
4. For each product include:
   - Product name as H3
   - Key features (bulleted list)
   - Pros and cons
   - Who it's best for
   - A call to action to "check the current price on Amazon"
5. Include a buying guide section with tips
6. End with a conclusion and FAQ section
7. Total length: {self.config['content']['min_word_count']}-{self.config['content']['max_word_count']} words

Write in a {self.config['content']['tone']} tone.

Format the output as Markdown."""

        return system_prompt, user_prompt

    def _generate_review_prompt(self, keyword: str, category: str) -> tuple:
        """Generate prompt for review-style article."""
        system_prompt = """You are an expert product reviewer for home office equipment.
You provide balanced, thorough reviews that help readers make informed decisions.
Your reviews are detailed, honest, and include real-world usage scenarios."""

        user_prompt = f"""Write a detailed review article for: "{keyword}"

Category: {category}

Structure:
1. H1 title with the keyword
2. Quick verdict box (rating, pros, cons, best for)
3. Introduction - who this review is for
4. Design and build quality section
5. Features breakdown
6. Performance in real use
7. Value for money analysis
8. Comparison with alternatives
9. Final verdict with recommendation
10. FAQ section

Length: {self.config['content']['min_word_count']}-{self.config['content']['max_word_count']} words
Tone: {self.config['content']['tone']}

Format as Markdown with clear headers."""

        return system_prompt, user_prompt

    def _generate_comparison_prompt(self, keyword: str, category: str) -> tuple:
        """Generate prompt for comparison article."""
        system_prompt = """You are a product comparison expert for home office equipment.
You create fair, detailed comparisons that help readers choose between options.
You highlight the strengths of each option and recommend based on user needs."""

        user_prompt = f"""Write a detailed comparison article for: "{keyword}"

Category: {category}

Structure:
1. H1 title with keyword
2. Quick comparison table
3. Introduction explaining why this comparison matters
4. Detailed breakdown of each option
5. Head-to-head comparison by feature:
   - Design/Build
   - Features
   - Performance
   - Price/Value
6. Who should choose each option
7. Final recommendation
8. FAQ

Length: {self.config['content']['min_word_count']}-{self.config['content']['max_word_count']} words
Tone: {self.config['content']['tone']}

Format as Markdown."""

        return system_prompt, user_prompt

    def _generate_guide_prompt(self, keyword: str, category: str) -> tuple:
        """Generate prompt for how-to/guide article."""
        system_prompt = """You are a home office setup expert.
You create helpful, actionable guides that solve real problems.
Your guides are step-by-step, beginner-friendly, and thorough."""

        user_prompt = f"""Write a comprehensive guide for: "{keyword}"

Category: {category}

Structure:
1. H1 title with keyword
2. Introduction - what readers will learn
3. Prerequisites/what you'll need
4. Step-by-step instructions with clear headers
5. Pro tips throughout
6. Common mistakes to avoid
7. Product recommendations where relevant
8. Conclusion with next steps
9. FAQ

Length: {self.config['content']['min_word_count']}-{self.config['content']['max_word_count']} words
Tone: {self.config['content']['tone']}

Format as Markdown."""

        return system_prompt, user_prompt

    def _generate_roundup_prompt(self, keyword: str, category: str) -> tuple:
        """Generate prompt for product roundup article."""
        system_prompt = """You are a budget-conscious home office product expert.
You curate the best products at different price points.
Your recommendations are practical, value-focused, and well-researched."""

        user_prompt = f"""Write a product roundup article for: "{keyword}"

Category: {category}

Structure:
1. H1 title with keyword and year
2. Quick picks summary box
3. Introduction - why budget matters
4. How we chose these products
5. Products organized by price tier:
   - Budget picks (under $50)
   - Mid-range picks ($50-150)
   - Worth the splurge ($150+)
6. Each product needs:
   - Name, price range
   - Key features
   - Why we like it
   - Any drawbacks
   - CTA to check price
7. Buying guide with tips
8. FAQ section

Length: {self.config['content']['min_word_count']}-{self.config['content']['max_word_count']} words
Tone: {self.config['content']['tone']}

Format as Markdown."""

        return system_prompt, user_prompt

    def _parse_article(
        self,
        content: str,
        keyword: str,
        category: str,
        article_type: str,
        article_id: str
    ) -> Optional[Dict]:
        """Parse AI output into structured article data."""
        # Extract title from first H1
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else keyword.title()

        # Clean title
        title = re.sub(r'\*+', '', title).strip()

        slug = self._generate_slug(title)

        # Add affiliate disclaimer if not present
        if "affiliate" not in content.lower():
            content += "\n\n---\n*This article contains affiliate links. As an Amazon Associate, we earn from qualifying purchases at no extra cost to you.*"

        # Generate meta description
        meta_desc = self._generate_meta_description(content, keyword)

        return {
            "id": article_id,
            "title": title,
            "slug": slug,
            "keyword": keyword,
            "category": category,
            "article_type": article_type,
            "content": content,
            "meta_description": meta_desc,
            "word_count": len(content.split()),
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "published_at": None,
        }

    def _generate_meta_description(self, content: str, keyword: str) -> str:
        """Generate SEO meta description."""
        # Take first paragraph after title
        paragraphs = content.split('\n\n')
        for p in paragraphs:
            if not p.startswith('#') and len(p) > 50:
                desc = p.strip()
                desc = re.sub(r'\[.*?\]\(.*?\)', '', desc)  # Remove links
                desc = re.sub(r'[#*_]', '', desc)  # Remove markdown
                if len(desc) > 160:
                    desc = desc[:157] + "..."
                return desc

        return f"Find the best {keyword} for your home office. Expert recommendations, reviews, and buying tips."

    def _save_pending_article(self, article: Dict):
        """Save article to pending queue."""
        pending = []
        if self.pending_file.exists():
            with open(self.pending_file, 'r') as f:
                pending = json.load(f)

        pending.append({k: v for k, v in article.items() if k != 'content'})

        with open(self.pending_file, 'w') as f:
            json.dump(pending, f, indent=2)

    def _save_article_file(self, article: Dict):
        """Save article content as markdown file."""
        filename = f"{article['slug']}.md"
        filepath = self.content_dir / filename

        # Create frontmatter
        frontmatter = f"""---
title: "{article['title']}"
slug: "{article['slug']}"
date: "{article['created_at']}"
category: "{article['category']}"
keyword: "{article['keyword']}"
description: "{article['meta_description']}"
---

"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter + article['content'])

    def get_stats(self) -> Dict:
        """Get content engine statistics."""
        articles = []
        if self.articles_file.exists():
            with open(self.articles_file, 'r') as f:
                articles = json.load(f)

        pending = []
        if self.pending_file.exists():
            with open(self.pending_file, 'r') as f:
                pending = json.load(f)

        return {
            "total_published": len(articles),
            "pending": len(pending),
            "ai_available": self.ai_client is not None,
        }
