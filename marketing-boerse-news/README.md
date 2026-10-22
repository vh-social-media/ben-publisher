# Marketing-Boerse Tages-Zusammenfassung

Mistral Workflow Worker: liest taeglich https://www.marketing-boerse.de/aktuell/list,
fasst jeden neuen Beitrag zusammen (Mistral LLM) und versendet die Zusammenfassung
per E-Mail (GMX SMTP) an mehrfachagentur@gmx.de.

Secrets (im Mistral Workspace Secrets Manager, an das Deployment gebunden):
- SMTP_USER: GMX-Absendeadresse
- SMTP_PASS: GMX-App-Passwort
- SMTP_HOST (optional, Standard: mail.gmx.net)

Workflow-Name: marketing-boerse-news
Geplanter Lauf: taeglich 08:00 Europe/Berlin
