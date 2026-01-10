"""
Analytics Engine
================
Tracks performance and provides insights for autonomous decision making.
Monitors traffic, conversions, and content performance.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp


class AnalyticsEngine:
    """
    Autonomous analytics engine.
    Tracks performance metrics and identifies optimization opportunities.
    """

    def __init__(self, config: dict):
        self.config = config
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        self.metrics_file = self.data_dir / "metrics.json"
        self.performance_file = self.data_dir / "performance.json"

    async def get_metrics(self) -> Dict:
        """
        Get current performance metrics.
        In production, this would pull from Google Analytics, Search Console, etc.
        """
        metrics = self._load_metrics()

        return {
            "total_pageviews": metrics.get("total_pageviews", 0),
            "total_clicks": metrics.get("total_clicks", 0),
            "estimated_revenue": metrics.get("estimated_revenue", 0.0),
            "top_performers": metrics.get("top_performers", []),
            "avg_time_on_page": metrics.get("avg_time_on_page", 0),
            "bounce_rate": metrics.get("bounce_rate", 0),
        }

    def _load_metrics(self) -> Dict:
        """Load metrics from disk."""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_metrics(self, metrics: Dict):
        """Save metrics to disk."""
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

    async def track_event(self, event_type: str, data: Dict):
        """Track an analytics event."""
        metrics = self._load_metrics()

        if "events" not in metrics:
            metrics["events"] = []

        metrics["events"].append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        # Update aggregate metrics
        if event_type == "pageview":
            metrics["total_pageviews"] = metrics.get("total_pageviews", 0) + 1
        elif event_type == "click":
            metrics["total_clicks"] = metrics.get("total_clicks", 0) + 1
        elif event_type == "conversion":
            metrics["total_conversions"] = metrics.get("total_conversions", 0) + 1
            metrics["estimated_revenue"] = metrics.get("estimated_revenue", 0) + data.get("value", 0)

        self._save_metrics(metrics)

    async def find_underperformers(self) -> List[Dict]:
        """
        Find articles that are underperforming and could be optimized.
        Returns list of articles with optimization suggestions.
        """
        performance = self._load_performance()

        underperformers = []

        for article_id, data in performance.items():
            score = self._calculate_performance_score(data)

            if score < 30:  # Below threshold
                underperformers.append({
                    "article_id": article_id,
                    "score": score,
                    "issues": self._identify_issues(data),
                    "suggestions": self._generate_suggestions(data)
                })

        return sorted(underperformers, key=lambda x: x["score"])

    def _load_performance(self) -> Dict:
        """Load article performance data."""
        if self.performance_file.exists():
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        return {}

    def _calculate_performance_score(self, data: Dict) -> float:
        """
        Calculate a performance score (0-100) for an article.
        Higher = better performing.
        """
        score = 50.0  # Base score

        # Factor in pageviews (normalized)
        pageviews = data.get("pageviews", 0)
        if pageviews > 100:
            score += 20
        elif pageviews > 50:
            score += 10
        elif pageviews < 10:
            score -= 15

        # Factor in click-through rate
        ctr = data.get("ctr", 0)
        if ctr > 5:
            score += 15
        elif ctr > 2:
            score += 5
        elif ctr < 1:
            score -= 10

        # Factor in time on page
        time_on_page = data.get("avg_time_seconds", 0)
        if time_on_page > 180:  # 3+ minutes
            score += 10
        elif time_on_page < 30:
            score -= 10

        # Factor in bounce rate
        bounce = data.get("bounce_rate", 50)
        if bounce > 80:
            score -= 15
        elif bounce < 40:
            score += 10

        return max(0, min(100, score))

    def _identify_issues(self, data: Dict) -> List[str]:
        """Identify specific issues with an article."""
        issues = []

        if data.get("pageviews", 0) < 10:
            issues.append("low_traffic")
        if data.get("ctr", 0) < 1:
            issues.append("low_ctr")
        if data.get("bounce_rate", 50) > 80:
            issues.append("high_bounce_rate")
        if data.get("avg_time_seconds", 0) < 30:
            issues.append("low_engagement")

        return issues

    def _generate_suggestions(self, data: Dict) -> List[str]:
        """Generate optimization suggestions based on data."""
        suggestions = []

        issues = self._identify_issues(data)

        if "low_traffic" in issues:
            suggestions.append("Improve title for better CTR in search")
            suggestions.append("Add more internal links from other articles")
            suggestions.append("Update content with more relevant keywords")

        if "low_ctr" in issues:
            suggestions.append("Rewrite meta description to be more compelling")
            suggestions.append("Add numbers or power words to title")

        if "high_bounce_rate" in issues:
            suggestions.append("Improve introduction to hook readers")
            suggestions.append("Add table of contents for easier navigation")
            suggestions.append("Break up text with more subheadings")

        if "low_engagement" in issues:
            suggestions.append("Add more detailed product comparisons")
            suggestions.append("Include more images or comparison tables")
            suggestions.append("Add FAQ section")

        return suggestions

    async def get_category_performance(self) -> Dict:
        """Get aggregated performance by category."""
        performance = self._load_performance()

        category_stats = {}

        for article_id, data in performance.items():
            category = data.get("category", "unknown")

            if category not in category_stats:
                category_stats[category] = {
                    "articles": 0,
                    "total_pageviews": 0,
                    "total_clicks": 0,
                    "avg_ctr": 0,
                }

            stats = category_stats[category]
            stats["articles"] += 1
            stats["total_pageviews"] += data.get("pageviews", 0)
            stats["total_clicks"] += data.get("clicks", 0)

        # Calculate averages
        for category, stats in category_stats.items():
            if stats["total_pageviews"] > 0:
                stats["avg_ctr"] = (stats["total_clicks"] / stats["total_pageviews"]) * 100

        return category_stats

    async def estimate_revenue(self) -> Dict:
        """
        Estimate revenue based on traffic and industry averages.
        This is an approximation - real revenue comes from affiliate dashboards.
        """
        metrics = self._load_metrics()

        clicks = metrics.get("total_clicks", 0)

        # Industry averages for affiliate sites
        conversion_rate = 0.03  # 3% of clicks convert
        avg_commission = 5.00  # $5 average commission

        estimated_conversions = clicks * conversion_rate
        estimated_revenue = estimated_conversions * avg_commission

        return {
            "total_clicks": clicks,
            "estimated_conversions": int(estimated_conversions),
            "estimated_revenue": round(estimated_revenue, 2),
            "note": "Estimates based on industry averages. Check affiliate dashboards for actual revenue."
        }

    async def get_growth_trend(self, days: int = 30) -> Dict:
        """Calculate growth trends over time."""
        metrics = self._load_metrics()
        events = metrics.get("events", [])

        if not events:
            return {"trend": "unknown", "change_percent": 0}

        # Filter to date range
        cutoff = datetime.now() - timedelta(days=days)
        midpoint = datetime.now() - timedelta(days=days // 2)

        first_half = 0
        second_half = 0

        for event in events:
            event_time = datetime.fromisoformat(event["timestamp"])
            if event_time > cutoff:
                if event_time < midpoint:
                    first_half += 1
                else:
                    second_half += 1

        if first_half == 0:
            change_percent = 100 if second_half > 0 else 0
        else:
            change_percent = ((second_half - first_half) / first_half) * 100

        if change_percent > 10:
            trend = "growing"
        elif change_percent < -10:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "change_percent": round(change_percent, 1),
            "first_half_events": first_half,
            "second_half_events": second_half,
        }

    def get_stats(self) -> Dict:
        """Get analytics engine stats."""
        metrics = self._load_metrics()
        performance = self._load_performance()

        return {
            "tracked_articles": len(performance),
            "total_events": len(metrics.get("events", [])),
            "total_pageviews": metrics.get("total_pageviews", 0),
            "estimated_revenue": metrics.get("estimated_revenue", 0),
        }
