#!/usr/bin/env python3
"""
Manual Run Script
=================
Use this to manually trigger the autonomous agent.
Normally, GitHub Actions runs this automatically.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add agent directory to path
agent_dir = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_dir))

os.chdir(agent_dir)

from orchestrator import OrchestratorAgent


async def main():
    print("Starting manual agent run...\n")

    agent = OrchestratorAgent(config_path="../config.yaml")

    # Run a full cycle
    await agent.run_daily_cycle()

    # Print status
    status = agent.get_status()
    print("\n" + "="*50)
    print("AGENT STATUS")
    print("="*50)
    print(f"Total articles: {status['state']['total_articles']}")
    print(f"Keywords used: {len(status['state']['keywords_used'])}")
    print(f"Last run: {status['state']['last_run']}")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
