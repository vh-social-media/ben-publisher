"""Startet den Workflow-Worker fuer die Marketing-Boerse-Zusammenfassung."""

import asyncio

import mistralai.workflows as workflows

from src.workflows.news import MarketingBoerseNewsWorkflow


if __name__ == "__main__":
    asyncio.run(workflows.run_worker([MarketingBoerseNewsWorkflow]))
