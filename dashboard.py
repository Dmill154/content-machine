#!/usr/bin/env python3
"""
Agent Dashboard
===============
View the status and performance of your autonomous content machine.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def load_json(filepath):
    """Load JSON file safely."""
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}


def format_date(iso_string):
    """Format ISO date string."""
    if not iso_string:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_string


def print_dashboard():
    """Print the dashboard."""
    data_dir = Path("data")

    # Load data
    state = load_json(data_dir / "agent_state.json")
    articles = load_json(data_dir / "articles.json") or []
    pending = load_json(data_dir / "pending_articles.json") or []
    metrics = load_json(data_dir / "metrics.json")
    keywords = load_json(data_dir / "used_keywords.json") or []

    if HAS_RICH:
        console = Console()

        # Header
        console.print(Panel.fit(
            "[bold cyan]AUTONOMOUS CONTENT MACHINE[/bold cyan]\n"
            "[dim]Dashboard & Status Monitor[/dim]",
            border_style="cyan"
        ))

        # Status Table
        status_table = Table(title="Agent Status", box=box.ROUNDED)
        status_table.add_column("Metric", style="cyan")
        status_table.add_column("Value", style="green")

        status_table.add_row("Last Run", format_date(state.get("last_run")))
        status_table.add_row("Total Articles", str(state.get("total_articles", 0)))
        status_table.add_row("Published", str(len(articles)))
        status_table.add_row("Pending", str(len(pending)))
        status_table.add_row("Keywords Used", str(len(keywords)))
        status_table.add_row("Est. Revenue", f"${state.get('total_revenue', 0):.2f}")

        console.print(status_table)

        # Traffic Table
        if metrics:
            traffic_table = Table(title="Traffic & Performance", box=box.ROUNDED)
            traffic_table.add_column("Metric", style="cyan")
            traffic_table.add_column("Value", style="yellow")

            traffic_table.add_row("Page Views", str(metrics.get("total_pageviews", 0)))
            traffic_table.add_row("Clicks", str(metrics.get("total_clicks", 0)))
            traffic_table.add_row("Events Tracked", str(len(metrics.get("events", []))))

            console.print(traffic_table)

        # Recent Articles
        if articles:
            articles_table = Table(title="Recent Articles", box=box.ROUNDED)
            articles_table.add_column("Title", style="white", max_width=50)
            articles_table.add_column("Category", style="cyan")
            articles_table.add_column("Published", style="dim")

            for article in articles[-5:]:
                articles_table.add_row(
                    article.get("title", "Unknown")[:50],
                    article.get("category", "general"),
                    format_date(article.get("published_at"))
                )

            console.print(articles_table)

        # Recent Decisions
        decisions = state.get("decisions_log", [])
        if decisions:
            decisions_table = Table(title="Recent Agent Decisions", box=box.ROUNDED)
            decisions_table.add_column("Time", style="dim", max_width=20)
            decisions_table.add_column("Decision", style="yellow")
            decisions_table.add_column("Reasoning", style="white", max_width=40)

            for decision in decisions[-5:]:
                decisions_table.add_row(
                    format_date(decision.get("timestamp")),
                    decision.get("decision", ""),
                    decision.get("reasoning", "")[:40]
                )

            console.print(decisions_table)

    else:
        # Fallback plain text output
        print("="*60)
        print("AUTONOMOUS CONTENT MACHINE - DASHBOARD")
        print("="*60)
        print()
        print("AGENT STATUS:")
        print(f"  Last Run: {format_date(state.get('last_run'))}")
        print(f"  Total Articles: {state.get('total_articles', 0)}")
        print(f"  Published: {len(articles)}")
        print(f"  Pending: {len(pending)}")
        print(f"  Keywords Used: {len(keywords)}")
        print(f"  Est. Revenue: ${state.get('total_revenue', 0):.2f}")
        print()
        print("TRAFFIC:")
        print(f"  Page Views: {metrics.get('total_pageviews', 0)}")
        print(f"  Clicks: {metrics.get('total_clicks', 0)}")
        print()
        if articles:
            print("RECENT ARTICLES:")
            for article in articles[-5:]:
                print(f"  - {article.get('title', 'Unknown')[:50]}")
        print()
        print("="*60)


def main():
    print_dashboard()


if __name__ == "__main__":
    main()
