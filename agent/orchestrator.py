"""
Autonomous Orchestrator Agent
=============================
The brain of the content money machine. This agent makes all decisions
autonomously about what content to create, when to publish, and how to optimize.
"""

import os
import json
import yaml
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

# Import our modules
from keyword_scanner import KeywordScanner
from content_engine import ContentEngine
from publisher import SitePublisher
from analytics import AnalyticsEngine

console = Console()

class OrchestratorAgent:
    """
    Autonomous agent that controls the entire content generation pipeline.
    Makes decisions without human intervention.
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Initialize all subsystems
        self.keyword_scanner = KeywordScanner(self.config)
        self.content_engine = ContentEngine(self.config)
        self.publisher = SitePublisher(self.config)
        self.analytics = AnalyticsEngine(self.config)

        # Agent state
        self.state_file = self.data_dir / "agent_state.json"
        self.state = self._load_state()

        console.print(Panel.fit(
            "[bold green]Autonomous Orchestrator Agent Initialized[/bold green]\n"
            f"Mode: {self.config['agent']['decision_mode']}\n"
            f"Niche: {self.config['niche']['primary']}\n"
            f"Articles/day: {self.config['content']['articles_per_day']}"
        ))

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Substitute environment variables
        self._substitute_env_vars(config)
        return config

    def _substitute_env_vars(self, obj):
        """Recursively substitute ${VAR} patterns with environment variables."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    obj[key] = os.getenv(env_var, "")
                elif isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
        elif isinstance(obj, list):
            for item in obj:
                self._substitute_env_vars(item)

    def _load_state(self) -> dict:
        """Load agent state from disk."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "total_articles": 0,
            "total_revenue": 0.0,
            "last_run": None,
            "keywords_used": [],
            "performance_history": [],
            "decisions_log": []
        }

    def _save_state(self):
        """Persist agent state to disk."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)

    def _log_decision(self, decision: str, reasoning: str, outcome: Optional[str] = None):
        """Log autonomous decisions for transparency."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "reasoning": reasoning,
            "outcome": outcome
        }
        self.state["decisions_log"].append(entry)
        console.print(f"[yellow]DECISION:[/yellow] {decision}")
        console.print(f"[dim]Reasoning: {reasoning}[/dim]")
        self._save_state()

    async def run_daily_cycle(self):
        """
        Execute one full autonomous cycle. This is the main loop.
        Called daily by the scheduler.
        """
        console.print("\n" + "="*60)
        console.print("[bold cyan]AUTONOMOUS CYCLE STARTED[/bold cyan]")
        console.print(f"Time: {datetime.now().isoformat()}")
        console.print("="*60 + "\n")

        try:
            # Phase 1: Analyze current performance
            await self._phase_analyze()

            # Phase 2: Make strategic decisions
            strategy = await self._phase_strategize()

            # Phase 3: Generate content based on strategy
            await self._phase_generate(strategy)

            # Phase 4: Publish content
            await self._phase_publish()

            # Phase 5: Optimize existing content
            await self._phase_optimize()

            # Update state
            self.state["last_run"] = datetime.now().isoformat()
            self._save_state()

            console.print("\n[bold green]AUTONOMOUS CYCLE COMPLETED[/bold green]\n")

        except Exception as e:
            console.print(f"[bold red]ERROR IN CYCLE: {e}[/bold red]")
            self._log_decision(
                "cycle_error",
                f"Cycle failed with error: {str(e)}",
                "will_retry_next_cycle"
            )

    async def _phase_analyze(self):
        """Phase 1: Analyze current performance and market."""
        console.print("[bold]Phase 1: ANALYZE[/bold]")

        # Get current performance metrics
        metrics = await self.analytics.get_metrics()

        console.print(f"  Total articles: {self.state['total_articles']}")
        console.print(f"  Estimated revenue: ${self.state['total_revenue']:.2f}")

        # Analyze what's working
        if metrics.get("top_performers"):
            console.print(f"  Top performing categories: {metrics['top_performers']}")

    async def _phase_strategize(self) -> dict:
        """Phase 2: Make autonomous strategic decisions."""
        console.print("\n[bold]Phase 2: STRATEGIZE[/bold]")

        strategy = {
            "content_focus": [],
            "keywords_to_target": [],
            "optimization_targets": []
        }

        # Decision: What categories to focus on
        categories = self.config["niche"]["categories"]
        articles_per_category = await self._count_articles_per_category()

        # Find underserved categories
        min_articles = min(articles_per_category.values()) if articles_per_category else 0
        underserved = [cat for cat, count in articles_per_category.items()
                       if count <= min_articles + 2]

        if underserved:
            strategy["content_focus"] = underserved[:2]
            self._log_decision(
                "focus_on_categories",
                f"Categories {underserved[:2]} have fewer articles, focusing there for balance",
                None
            )
        else:
            # Focus on highest converting if we have data
            strategy["content_focus"] = categories[:2]
            self._log_decision(
                "default_category_focus",
                "No clear underserved category, using default rotation",
                None
            )

        # Decision: What keywords to target
        keywords = await self.keyword_scanner.find_opportunities(
            categories=strategy["content_focus"],
            count=self.config["content"]["articles_per_day"] * 2
        )

        # Filter out already used keywords
        new_keywords = [kw for kw in keywords if kw not in self.state["keywords_used"]]
        strategy["keywords_to_target"] = new_keywords[:self.config["content"]["articles_per_day"]]

        self._log_decision(
            "keyword_selection",
            f"Selected {len(strategy['keywords_to_target'])} keywords based on search volume and competition",
            f"Keywords: {strategy['keywords_to_target']}"
        )

        console.print(f"  Strategy: Focus on {strategy['content_focus']}")
        console.print(f"  Target keywords: {len(strategy['keywords_to_target'])}")

        return strategy

    async def _phase_generate(self, strategy: dict):
        """Phase 3: Generate content based on strategy."""
        console.print("\n[bold]Phase 3: GENERATE[/bold]")

        articles_created = 0

        for keyword in strategy["keywords_to_target"]:
            console.print(f"  Generating article for: '{keyword}'")

            try:
                article = await self.content_engine.generate_article(
                    keyword=keyword,
                    category=strategy["content_focus"][0] if strategy["content_focus"] else "general"
                )

                if article:
                    articles_created += 1
                    self.state["keywords_used"].append(keyword)
                    console.print(f"    [green]OK[/green] Created: {article['title']}")

            except Exception as e:
                console.print(f"    [red]FAIL[/red] Failed: {e}")

        self.state["total_articles"] += articles_created
        self._log_decision(
            "content_generation",
            f"Generated {articles_created} articles this cycle",
            f"Total articles now: {self.state['total_articles']}"
        )

    async def _phase_publish(self):
        """Phase 4: Publish generated content to the site."""
        console.print("\n[bold]Phase 4: PUBLISH[/bold]")

        published = await self.publisher.publish_pending()
        console.print(f"  Published {published} articles")

        # Rebuild site
        await self.publisher.rebuild_site()
        console.print("  [green]OK[/green] Site rebuilt")

    async def _phase_optimize(self):
        """Phase 5: Optimize existing content based on performance."""
        console.print("\n[bold]Phase 5: OPTIMIZE[/bold]")

        # Check if we should optimize (not every cycle)
        if self.state["total_articles"] < 10:
            console.print("  [dim]Skipping optimization (need more articles first)[/dim]")
            return

        # Find underperforming content
        underperformers = await self.analytics.find_underperformers()

        if underperformers:
            self._log_decision(
                "optimization_targets",
                f"Found {len(underperformers)} articles to potentially optimize",
                None
            )
            # Could trigger rewrites or improvements here

    async def _count_articles_per_category(self) -> dict:
        """Count how many articles exist per category."""
        articles_file = self.data_dir / "articles.json"
        if not articles_file.exists():
            return {cat: 0 for cat in self.config["niche"]["categories"]}

        with open(articles_file, 'r') as f:
            articles = json.load(f)

        counts = {cat: 0 for cat in self.config["niche"]["categories"]}
        for article in articles:
            cat = article.get("category", "general")
            if cat in counts:
                counts[cat] += 1

        return counts

    def get_status(self) -> dict:
        """Get current agent status for monitoring."""
        return {
            "state": self.state,
            "config": {
                "niche": self.config["niche"]["primary"],
                "mode": self.config["agent"]["decision_mode"],
                "articles_per_day": self.config["content"]["articles_per_day"]
            },
            "health": "operational"
        }


async def main():
    """Main entry point for the autonomous agent."""
    agent = OrchestratorAgent()
    await agent.run_daily_cycle()


if __name__ == "__main__":
    asyncio.run(main())
