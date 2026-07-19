# main.py
import os
import requests
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
from gitgaze import GitGazeAnalyzer

app = FastAPI(title="GitGaze Webhook Portal")
analyzer = GitGazeAnalyzer()

# Retrieve GitHub Token from environment variables for secure API access
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

@app.get("/")
def health_check():
    return {"status": "active", "engine": "GitGaze Core Ready"}

@app.post("/webhook")
async def handle_github_webhook(request: Request, x_github_event: str = Header(None)):
    """
    Listens for live GitHub Webhook events. When a pull request is opened or updated,
    it downloads the code changes, runs the analysis, and comments back to GitHub.
    """
    # We only care about pull request activities
    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": "Not a pull request event"}

    payload = await request.json()
    action = payload.get("action")
    
    # Trigger only when PR is opened or new code is pushed (synchronize)
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"Action '{action}' not analyzed"}

    pull_request_data = payload["pull_request"]
    diff_url = pull_request_data.get("diff_url")
    comments_url = pull_request_data.get("comments_url") # API endpoint to leave comments

    if not diff_url or not comments_url:
        raise HTTPException(status_code=400, detail="Missing required payload metadata")

    # 1. Fetch the raw git diff text from GitHub
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    diff_response = requests.get(diff_url, headers=headers)
    if diff_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to retrieve diff payload from GitHub")

    raw_diff = diff_response.text

    # 2. Run the GitGaze Core Architectural Analysis
    analysis_report = analyzer.analyze_diff(raw_diff)

    # 3. Format a clean, highly professional Markdown comment for the PR
    metrics = analysis_report["metrics"]
    comment_body = f"""### 👁️ GitGaze Architectural Risk Assessment Report

* **Analysis Status:** `{analysis_report['status']}`
* **Calculated Code Risk Score:** `{metrics['calculated_risk_score']}`

| Metric Metric | Value |
| :--- | :--- |
| 🟢 Lines Added | {metrics['lines_added']} |
| 🔴 Lines Removed | {metrics['lines_removed']} |
| 🔄 Code Churn Ratio | {metrics['churn_ratio']} |

#### ⚠️ Behavioral Triggers Flagged:
"""
    if analysis_report["system_triggers"]:
        for trigger in analysis_report["system_triggers"]:
            comment_body += f"\n- {trigger}"
    else:
        comment_body += "\n- *None. Code changes conform to standard risk thresholds.*"

    # 4. Post the generated analysis back into the GitHub Pull Request interface
    if GITHUB_TOKEN:
        post_headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.post(comments_url, json={"body": comment_body}, headers=post_headers)
        return {"status": "success", "github_notified": response.status_code == 201}
    
    # Fallback to local printing if token isn't configured yet
    print(f"--- SIMULATED GITHUB PR COMMENT OUTCOMES ---\n{comment_body}")
    return {"status": "processed_locally", "message": "Configure GITHUB_TOKEN env variable to post to live PRs."}
