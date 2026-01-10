"""
Keyword Scanner Module
======================
Finds low-competition, high-opportunity keywords for content generation.
Uses multiple data sources to identify gaps in the market.
"""

import json
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import random


class KeywordScanner:
    """
    Autonomous keyword research engine.
    Finds profitable content opportunities without human input.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path("data")
        self.keywords_file = self.data_dir / "keywords.json"
        self.used_keywords_file = self.data_dir / "used_keywords.json"

        # Variable values for template filling
        self.variables = {
            "adj": ["budget", "cheap", "affordable", "best", "top", "quality", "compact", "minimalist", "modern", "professional"],
            "price": ["50", "100", "150", "200", "250", "300", "75", "125", "175"],
            "use_case": ["programming", "gaming", "writing", "video calls", "graphic design", "trading", "studying", "remote work", "content creation"],
            "space": ["small room", "apartment", "bedroom", "closet office", "studio", "shared space"],
            "material": ["wood", "glass", "metal", "bamboo", "walnut"],
            "persona": ["programmers", "students", "remote workers", "gamers", "writers", "artists", "traders", "teachers"],
            "pain_point": ["back pain", "neck pain", "wrist pain", "eye strain", "long hours", "poor posture", "carpal tunnel"],
            "brand": ["ikea", "flexispot", "autonomous", "secretlab", "herman miller dupe", "amazon basics"],
            "year": ["2024", "2025"],
            "duration": ["8 hour", "10 hour", "all day", "long"],
            "feature": ["lumbar support", "usb ports", "adjustable arms", "headrest", "wireless charging", "storage"],
            "size": ["24", "27", "32", "34", "ultrawide"],
            "resolution": ["4k", "1440p", "1080p"],
            "type": ["mechanical", "membrane", "ergonomic", "split", "compact"],
            "item": ["mousepad", "webcam", "microphone", "headphones", "speaker", "charger"],
            "setup": ["macbook", "laptop", "dual monitor", "standing desk"],
        }

        # Seed keyword templates for the home office niche
        self.keyword_templates = self._load_keyword_templates()

    def _load_keyword_templates(self) -> dict:
        """
        Load keyword templates - these are patterns that generate many keywords.
        This is the "brain" for finding content opportunities.
        """
        return {
            "desks": [
                "best {adj} desk under ${price}",
                "best desk for {use_case}",
                "{adj} standing desk review",
                "small desk for {space}",
                "{material} desk for home office",
                "best {adj} desk for {persona}",
                "desk setup for {use_case}",
                "{brand} desk review {year}",
                "adjustable desk under ${price}",
                "corner desk for {space}",
                "l-shaped desk under ${price}",
                "best desk for {pain_point}",
            ],
            "chairs": [
                "best {adj} office chair under ${price}",
                "office chair for {pain_point}",
                "{adj} ergonomic chair review",
                "best chair for {use_case}",
                "comfortable chair for {duration} sitting",
                "{brand} chair review {year}",
                "mesh vs {material} office chair",
                "best chair for {persona}",
                "office chair with {feature}",
                "budget ergonomic chair {year}",
            ],
            "monitors": [
                "best {adj} monitor under ${price}",
                "monitor for {use_case}",
                "{size} inch monitor review",
                "best monitor for {persona}",
                "dual monitor setup under ${price}",
                "curved vs flat monitor for {use_case}",
                "{resolution} monitor for home office",
                "best {adj} monitor {year}",
                "portable monitor for {use_case}",
                "monitor with {feature}",
            ],
            "keyboards": [
                "best {adj} keyboard under ${price}",
                "{type} keyboard for {use_case}",
                "ergonomic keyboard for {pain_point}",
                "best keyboard for {persona}",
                "wireless vs wired keyboard {year}",
                "{brand} keyboard review",
                "quiet keyboard for {space}",
                "mechanical keyboard under ${price}",
                "split keyboard review {year}",
                "keyboard with {feature}",
            ],
            "lighting": [
                "best desk lamp for {use_case}",
                "led desk light under ${price}",
                "monitor light bar review",
                "lighting setup for {use_case}",
                "eye strain reducing lights",
                "best {adj} desk lamp {year}",
                "natural light lamp for office",
                "bias lighting for monitor",
                "ring light for {use_case}",
                "smart desk lamp review",
            ],
            "organization": [
                "desk organization ideas {year}",
                "cable management under ${price}",
                "best desk organizer for {persona}",
                "small space office organization",
                "desk drawer organizer review",
                "monitor stand with {feature}",
                "desk shelf for {use_case}",
                "pegboard desk setup",
                "filing system for home office",
                "desk accessories under ${price}",
            ],
            "ergonomics": [
                "ergonomic setup for {pain_point}",
                "wrist rest for {use_case}",
                "footrest for desk review",
                "monitor arm under ${price}",
                "laptop stand for {use_case}",
                "keyboard tray review {year}",
                "ergonomic mouse for {pain_point}",
                "standing mat review",
                "posture corrector for office",
                "ergonomic accessories under ${price}",
            ],
            "accessories": [
                "best {item} for home office",
                "work from home essentials {year}",
                "desk accessories under ${price}",
                "webcam for {use_case}",
                "headset for {use_case}",
                "usb hub for {setup}",
                "desk pad review {year}",
                "coffee warmer for desk",
                "white noise machine for office",
                "plants for home office",
            ],
        }

    def _generate_keyword(self, template: str) -> str:
        """Fill in a keyword template with random variables."""
        result = template

        for var_name, var_values in self.variables.items():
            placeholder = "{" + var_name + "}"
            if placeholder in result:
                result = result.replace(placeholder, random.choice(var_values))

        return result

    async def find_opportunities(
        self,
        categories: Optional[List[str]] = None,
        count: int = 10
    ) -> List[str]:
        """
        Find keyword opportunities for content creation.
        Returns a list of keywords sorted by estimated opportunity.
        """
        if categories is None:
            categories = list(self.keyword_templates.keys())

        # Load already used keywords
        used = self._load_used_keywords()

        opportunities = []

        for category in categories:
            if category not in self.keyword_templates:
                continue

            templates = self.keyword_templates[category]

            # Generate multiple keywords from templates
            for _ in range(count * 2):  # Generate extras to filter
                template = random.choice(templates)
                keyword = self._generate_keyword(template)

                if keyword not in used and keyword not in opportunities:
                    # Score the keyword (simplified - in production use real data)
                    score = self._estimate_opportunity_score(keyword)
                    opportunities.append((keyword, score))

        # Sort by score and return top keywords
        opportunities.sort(key=lambda x: x[1], reverse=True)
        return [kw for kw, score in opportunities[:count]]

    def _estimate_opportunity_score(self, keyword: str) -> float:
        """
        Estimate the opportunity score for a keyword.
        Higher score = better opportunity.

        In production, this would use real search volume and competition data.
        For now, we use heuristics based on keyword characteristics.
        """
        score = 50.0  # Base score

        # Boost for price mentions (buyer intent)
        if "$" in keyword or "under" in keyword:
            score += 20

        # Boost for current year (fresh content)
        if "2024" in keyword or "2025" in keyword:
            score += 15

        # Boost for specific use cases (targeted)
        specific_terms = ["programming", "gaming", "back pain", "small", "budget"]
        if any(term in keyword for term in specific_terms):
            score += 10

        # Boost for comparison/review keywords
        if "vs" in keyword or "review" in keyword or "best" in keyword:
            score += 15

        # Penalty for very generic terms
        if len(keyword.split()) < 3:
            score -= 10

        # Penalty for overly long keywords
        if len(keyword.split()) > 8:
            score -= 5

        # Add some randomness to avoid always picking the same patterns
        score += random.uniform(-5, 5)

        return score

    def _load_used_keywords(self) -> set:
        """Load the set of already used keywords."""
        if self.used_keywords_file.exists():
            with open(self.used_keywords_file, 'r') as f:
                return set(json.load(f))
        return set()

    def save_used_keyword(self, keyword: str):
        """Mark a keyword as used."""
        used = self._load_used_keywords()
        used.add(keyword)
        with open(self.used_keywords_file, 'w') as f:
            json.dump(list(used), f)

    async def get_trending_topics(self) -> List[str]:
        """
        Get currently trending topics in the niche.
        Could integrate with Google Trends API or similar.
        """
        # Placeholder - in production, fetch real trending data
        trending_modifiers = [
            "2025",
            "ai powered",
            "smart",
            "sustainable",
            "minimalist",
            "ergonomic",
            "wireless",
            "portable",
        ]

        base_topics = [
            "home office setup",
            "remote work essentials",
            "desk organization",
            "ergonomic workspace",
        ]

        trending = []
        for topic in base_topics:
            modifier = random.choice(trending_modifiers)
            trending.append(f"{modifier} {topic}")

        return trending

    def get_stats(self) -> dict:
        """Get keyword scanner statistics."""
        used = self._load_used_keywords()
        total_templates = sum(len(t) for t in self.keyword_templates.values())

        return {
            "total_templates": total_templates,
            "keywords_used": len(used),
            "categories": list(self.keyword_templates.keys()),
            "potential_keywords": total_templates * 100,  # Rough estimate
        }
