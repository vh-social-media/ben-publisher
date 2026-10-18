"""
Ben – Facebook-Publisher-Workflow fuer die VerbraucherHilfe e.V.

Published freigegebene Posts auf der Facebook-Seite.
Der Seiten-Token wird als Workspace-Secret FACEBOOK_PAGE_TOKEN injiziert.
"""

import json
import urllib.request

import pydantic
import mistralai.workflows as workflows

PAGE_ID = "146105108836523"
GRAPH_URL = f"https://graph.facebook.com/v21.0/{PAGE_ID}/photos"


class PostPrompt(pydantic.BaseModel):
    message: str
    image_url: str
    dry_run: bool = True


def _publish_photo(message: str, image_url: str, token: str, dry_run: bool) -> dict:
    payload = json.dumps({
        "url": image_url,
        "caption": message,
        "access_token": token,
    }).encode("utf-8")

    if dry_run:
        return {
            "status": "dry_run_ok",
            "would_post": {"page": PAGE_ID, "caption_len": len(message)},
        }

    request = urllib.request.Request(
        GRAPH_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
    return {"status": "published", "post_id": body.get("id")}


@workflows.activity(name="publish-facebook-post")
async def publish_facebook_post(message: str, image_url: str, dry_run: bool) -> dict:
    import os
    token = os.environ["FACEBOOK_PAGE_TOKEN"]
    return _publish_photo(message, image_url, token, dry_run)


@workflows.workflow.define(name="ben-facebook-publisher")
class BenFacebookPublisherWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, prompt: PostPrompt) -> dict:
        return await publish_facebook_post(
            prompt.message, prompt.image_url, prompt.dry_run
        )
