#!/usr/bin/env python3
"""
One-Time Setup Script
=====================
Run this once to initialize the autonomous content machine.
After setup, the system runs autonomously via GitHub Actions.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║        AUTONOMOUS CONTENT MACHINE - SETUP WIZARD              ║
║                                                               ║
║  This will set up your $100 → $1000 content machine           ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def check_python():
    """Verify Python version."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required. You have:", sys.version)
        sys.exit(1)
    print("✅ Python version:", sys.version.split()[0])


def install_dependencies():
    """Install required packages."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)


def setup_directories():
    """Create required directories."""
    print("\n📁 Setting up directories...")
    dirs = [
        "data",
        "site/content",
        "site/templates",
        "site/static/css",
        "site/public",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")


def check_api_keys():
    """Check for required API keys."""
    print("\n🔑 Checking API keys...")

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if openai_key:
        print("✅ OpenAI API key found")
        return True
    elif anthropic_key:
        print("✅ Anthropic API key found")
        return True
    else:
        print("⚠️  No AI API key found!")
        print("   The system will use fallback templates (lower quality)")
        print("")
        print("   To add an API key, set one of these environment variables:")
        print("   - OPENAI_API_KEY (for GPT-4)")
        print("   - ANTHROPIC_API_KEY (for Claude)")
        print("")
        return False


def initialize_data():
    """Initialize data files."""
    print("\n💾 Initializing data files...")

    data_dir = Path("data")

    # Initialize empty data files
    files = {
        "articles.json": [],
        "pending_articles.json": [],
        "used_keywords.json": [],
        "metrics.json": {"total_pageviews": 0, "total_clicks": 0, "events": []},
        "agent_state.json": {
            "total_articles": 0,
            "total_revenue": 0.0,
            "last_run": None,
            "keywords_used": [],
            "performance_history": [],
            "decisions_log": []
        }
    }

    for filename, initial_data in files.items():
        filepath = data_dir / filename
        if not filepath.exists():
            with open(filepath, 'w') as f:
                json.dump(initial_data, f, indent=2)

    print("✅ Data files initialized")


def run_initial_cycle():
    """Run the first content generation cycle."""
    print("\n🚀 Running initial content generation cycle...")
    print("   This will generate your first batch of articles.\n")

    try:
        # Change to agent directory
        os.chdir("agent")

        # Import and run the orchestrator
        sys.path.insert(0, '.')
        from orchestrator import OrchestratorAgent
        import asyncio

        agent = OrchestratorAgent(config_path="../config.yaml")
        asyncio.run(agent.run_daily_cycle())

        os.chdir("..")
        print("\n✅ Initial cycle completed!")

    except Exception as e:
        print(f"\n⚠️  Initial cycle had issues: {e}")
        print("   This is often due to missing API keys.")
        print("   The system will still work, just with template content.")
        os.chdir("..")


def print_next_steps():
    """Print what to do next."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                     SETUP COMPLETE! 🎉                        ║
╚═══════════════════════════════════════════════════════════════╝

📋 NEXT STEPS (One-time, ~30 min total):

1. CREATE GITHUB REPOSITORY
   - Go to github.com/new
   - Create a new repository
   - Push this code to it

2. SET UP GITHUB SECRETS
   Go to: Repository → Settings → Secrets → Actions
   Add these secrets:
   - OPENAI_API_KEY (or ANTHROPIC_API_KEY)

3. ENABLE GITHUB PAGES
   Go to: Repository → Settings → Pages
   - Source: Deploy from a branch
   - Branch: gh-pages / root

4. GET YOUR DOMAIN ($12)
   - Buy a domain from Namecheap, Cloudflare, etc.
   - Or use free: yourusername.github.io/repo-name

5. SET UP AMAZON ASSOCIATES ($0)
   - Sign up at affiliate-program.amazon.com
   - Get your Associate tag
   - Update config.yaml with your tag

6. (OPTIONAL) ADD GOOGLE ANALYTICS
   - Create account at analytics.google.com
   - Add your measurement ID to templates

═══════════════════════════════════════════════════════════════

💰 COST BREAKDOWN:
   - Domain: ~$12/year
   - Hosting: $0 (GitHub Pages)
   - AI API: ~$10-20/month (for good content)
   - Total: ~$50 to start, $10-20/month ongoing

📈 EXPECTED TIMELINE:
   - Week 1-2: System generates 20-40 articles
   - Week 3-4: Google starts indexing
   - Month 2-3: Traffic begins, first commissions
   - Month 4+: Compound growth, scale what works

🤖 The agent will run AUTOMATICALLY every day at 8 AM UTC.
   Check back weekly to see progress!

═══════════════════════════════════════════════════════════════

To manually run the agent:
   cd agent && python orchestrator.py

To build the site locally:
   cd agent && python -c "
import asyncio
from publisher import SitePublisher
import yaml
with open('../config.yaml') as f:
    config = yaml.safe_load(f)
publisher = SitePublisher(config)
asyncio.run(publisher.rebuild_site())
"

Site will be in: site/public/
    """)


def main():
    print_banner()

    print("Starting setup...\n")

    check_python()
    install_dependencies()
    setup_directories()
    has_api = check_api_keys()
    initialize_data()

    # Ask about running initial cycle
    print("\n" + "="*60)
    if has_api:
        response = input("Run initial content generation? (y/n): ").strip().lower()
        if response == 'y':
            run_initial_cycle()
    else:
        print("Skipping initial generation (no API key)")

    print_next_steps()


if __name__ == "__main__":
    main()
