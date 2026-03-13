"""
GitHub Issue Creator for sumans-19/Labyrinth
=============================================
Creates issues on the Labyrinth repository using the GitHub REST API.

Usage:
  1. Set your GitHub token as an environment variable:
       set GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx     (Windows CMD)
       $env:GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxx"  (PowerShell)

  2. Run the script:
       python create_github_issue.py

  Or pass the token directly (not recommended for production):
       python create_github_issue.py --token ghp_xxxxxxxxxxxxxxxxxxxxx
"""

import requests
import argparse
import os
import sys


# ── Configuration ──────────────────────────────────────────────────────────
OWNER = "sumans-19"
REPO = "Labyrinth"
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"


def get_token(cli_token=None):
    """Retrieve the GitHub token from CLI arg or environment variable."""
    token = cli_token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Error: No GitHub token provided.")
        print("   Set GITHUB_TOKEN env var or pass --token <your_token>")
        sys.exit(1)
    return token


def create_issue(token, title, body="", labels=None, assignees=None):
    """
    Create a GitHub issue.

    Args:
        token:     GitHub Personal Access Token
        title:     Issue title (required)
        body:      Issue description / body (optional)
        labels:    List of label names, e.g. ["bug", "urgent"]
        assignees: List of GitHub usernames, e.g. ["sumans-19"]

    Returns:
        dict with 'success', 'number', 'url', and 'title' on success,
        or 'success' False with 'error' on failure.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    payload = {"title": title}
    if body:
        payload["body"] = body
    if labels:
        payload["labels"] = labels
    if assignees:
        payload["assignees"] = assignees

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 201:
        data = response.json()
        return {
            "success": True,
            "number": data["number"],
            "url": data["html_url"],
            "title": data["title"],
        }
    else:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.json().get("message", response.text),
        }


def interactive_mode(token):
    """Prompt the user to enter issue details interactively."""
    print("\n🔧 GitHub Issue Creator — sumans-19/Labyrinth")
    print("=" * 50)

    title = input("\n📌 Issue Title: ").strip()
    if not title:
        print("❌ Title is required.")
        return

    body = input("📝 Description (press Enter to skip): ").strip()

    labels_input = input("🏷️  Labels (comma-separated, e.g. bug,urgent — Enter to skip): ").strip()
    labels = [l.strip() for l in labels_input.split(",") if l.strip()] if labels_input else None

    assignees_input = input("👤 Assignees (comma-separated usernames — Enter to skip): ").strip()
    assignees = [a.strip() for a in assignees_input.split(",") if a.strip()] if assignees_input else None

    print("\n⏳ Creating issue...")
    result = create_issue(token, title, body, labels, assignees)

    if result["success"]:
        print(f"\n✅ Issue #{result['number']} created successfully!")
        print(f"   Title: {result['title']}")
        print(f"   URL:   {result['url']}")
    else:
        print(f"\n❌ Failed to create issue (HTTP {result['status_code']})")
        print(f"   Error: {result['error']}")


def main():
    parser = argparse.ArgumentParser(description="Create GitHub issues for sumans-19/Labyrinth")
    parser.add_argument("--token", help="GitHub Personal Access Token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--title", help="Issue title (skips interactive mode)")
    parser.add_argument("--body", default="", help="Issue body/description")
    parser.add_argument("--labels", default="", help="Comma-separated labels")
    parser.add_argument("--assignees", default="", help="Comma-separated assignees")

    args = parser.parse_args()
    token = get_token(args.token)

    if args.title:
        # ── CLI mode ──
        labels = [l.strip() for l in args.labels.split(",") if l.strip()] if args.labels else None
        assignees = [a.strip() for a in args.assignees.split(",") if a.strip()] if args.assignees else None

        result = create_issue(token, args.title, args.body, labels, assignees)

        if result["success"]:
            print(f"✅ Issue #{result['number']} created: {result['url']}")
        else:
            print(f"❌ Failed (HTTP {result['status_code']}): {result['error']}")
            sys.exit(1)
    else:
        # ── Interactive mode ──
        interactive_mode(token)


if __name__ == "__main__":
    main()
