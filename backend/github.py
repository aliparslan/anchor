from datetime import datetime, timezone

import httpx

from db import get_setting
from db.github import save_github_contributions


GITHUB_GRAPHQL = "https://api.github.com/graphql"

CONTRIBUTIONS_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""


async def fetch_github_activity() -> dict:
    username = await get_setting("github_username")
    token = await get_setting("github_token")
    if not username or not token:
        return {}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            GITHUB_GRAPHQL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"query": CONTRIBUTIONS_QUERY, "variables": {"username": username}},
        )
        resp.raise_for_status()
        data = resp.json()

    user = data.get("data", {}).get("user")
    if not user:
        return {}

    calendar = user["contributionsCollection"]["contributionCalendar"]
    total = calendar["totalContributions"]
    days = []
    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            days.append({
                "date": day["date"],
                "count": day["contributionCount"],
            })

    result = {"total": total, "days": days, "fetched_at": datetime.now(timezone.utc).isoformat()}
    await save_github_contributions(result)
    print(f"[GitHub] Saved {len(days)} contribution days ({total} total)")
    return result
