"""Taegliche Zusammenfassung der Marketing-Boerse-News per E-Mail."""

from pydantic import BaseModel

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai

NEWS_URL = "https://www.marketing-boerse.de/aktuell/list"


class NewsInput(BaseModel):
    recipient: str = "mehrfachagentur@gmx.de"
    max_items: int = 20


@workflows.activity()
async def fetch_page_text(url: str) -> str:
    """Laedt die Seite und gibt den sichtbaren Text zurueck."""
    from bs4 import BeautifulSoup
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)[:60000]


@workflows.activity()
async def send_email(subject: str, body: str, recipient: str) -> dict:
    """Versendet die E-Mail ueber den konfigurierten SMTP-Server (GMX)."""
    import asyncio
    import os
    import smtplib
    from email.message import EmailMessage

    smtp_host = os.environ.get("SMTP_HOST", "mail.gmx.net")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    if not smtp_user or not smtp_pass:
        raise RuntimeError("SMTP_USER und SMTP_PASS muessen als Umgebungsvariablen gesetzt sein.")

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    def _send() -> None:
        with smtplib.SMTP(smtp_host, 587, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

    await asyncio.to_thread(_send)
    return {"sent": True, "to": recipient}


@workflows.workflow.define(
    name="marketing-boerse-news",
    workflow_display_name="Marketing-Boerse Tages-Zusammenfassung",
    workflow_description="Liest marketing-boerse.de/aktuell/list, fasst jeden neuen Beitrag zusammen und sendet die Zusammenfassung per E-Mail.",
)
class MarketingBoerseNewsWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: NewsInput) -> dict:
        page_text = await fetch_page_text(NEWS_URL)

        agent = workflows_mistralai.Agent(
            model="mistral-medium-latest",
            name="marketing-news-summarizer",
            description="Erstellt die taegliche Marketing-News-Zusammenfassung auf Deutsch.",
            instructions=(
                "Du erhaeltst den Text der News-Uebersicht von marketing-boerse.de. "
                "Erstelle eine kurze deutsche Zusammenfassung fuer jeden gelisteten Beitrag: "
                "Titel als fette Ueberschrift, gefolgt von 1-2 Saetzen Zusammenfassung, "
                "inklusive Datum und Quelle, wenn angegeben. Liste nur die neuesten, "
                "hoechstens so viele Beitraege wie angegeben. Nutze Markdown-Aufzaehlung "
                "('- **Titel**: Zusammenfassung'). Keine Einleitung, nur die Liste."
            ),
        )

        outputs = await workflows_mistralai.Runner.run(
            agent=agent,
            inputs=(
                "Erstelle die Zusammenfassung der neuesten Beitraege "
                f"(maximal {input.max_items}) von der folgenden Seite:\n\n{page_text}"
            ),
            session=workflows_mistralai.RemoteSession(),
            max_turns=5,
        )

        summary = "\n".join(
            getattr(output, "text", "") for output in outputs if getattr(output, "text", None)
        ).strip()

        subject = "Marketing-Boerse – Tages-Zusammenfassung"
        await send_email(subject, summary, input.recipient)
        return {"summary": summary, "recipient": input.recipient}
