import os
import sys
import time
import requests
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.rule import Rule

console = Console()

LINKUP_API_URL = "https://api.linkup.so/v1/search"

QUERIES = [
    {
        "label": "EdTech funding & startups in India",
        "query": "India EdTech startup funding news this week 2026",
        "section_title": "EDTECH FUNDING & STARTUPS",
    },
    {
        "label": "Student learning behavior trends in India",
        "query": "India student learning behavior trends 2026",
        "section_title": "STUDENT BEHAVIOR & TRENDS",
    },
]


def print_header():
    console.print()
    # ASCII logo
    logo = Text("⌁ linkup", style="bold white")
    console.print(logo, justify="left")
    console.print(Text("EdTech Morning Report", style="bold white"), justify="left")
    console.print(
        Text(datetime.now().strftime("%A, %d %B %Y"), style="dim white"),
        justify="left",
    )
    console.print(Rule(style="dim white"))
    console.print()


def fetch_linkup(query: str, label: str, api_key: str) -> Optional[dict]:
    console.print(f"[yellow]→ Calling Linkup API: {label}...[/yellow]")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "depth": "deep",
        "outputType": "sourcedAnswer",
    }

    start = time.time()
    try:
        with console.status("[yellow]  fetching...[/yellow]", spinner="dots"):
            response = requests.post(
                LINKUP_API_URL, json=payload, headers=headers, timeout=25
            )
        response.raise_for_status()
        data = response.json()
        elapsed = time.time() - start

        sources = data.get("sources", [])
        source_count = len(sources)
        console.print(
            f"[green]✓ Done ({source_count} source{'s' if source_count != 1 else ''} found, {elapsed:.1f}s)[/green]"
        )
        console.print()
        return data

    except requests.exceptions.HTTPError as e:
        console.print(f"[red]✗ API error ({response.status_code}): {e}[/red]")
        console.print()
        return None
    except requests.exceptions.Timeout:
        console.print("[red]✗ Request timed out after 25s[/red]")
        console.print()
        return None
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Connection error: {e}[/red]")
        console.print()
        return None


def extract_bullets(data: dict, max_bullets: int = 4) -> list[dict]:
    """Return up to max_bullets items with 'text' and 'url' keys."""
    if not data:
        return []

    answer = data.get("answer", "")
    sources = data.get("sources", [])

    bullets = []

    # Try to split answer into sentences as bullets
    sentences = [s.strip() for s in answer.replace("\n", " ").split(". ") if s.strip()]

    for i, sentence in enumerate(sentences[:max_bullets]):
        if not sentence.endswith("."):
            sentence += "."
        url = sources[i]["url"] if i < len(sources) else ""
        bullets.append({"text": sentence, "url": url})

    # If answer had fewer sentences than sources available, pad isn't needed
    return bullets


def print_section(title: str, bullets: list[dict]):
    console.print(Rule(style="dim white"))
    console.print(Text(title, style="bold white"))
    console.print()

    if not bullets:
        console.print(Text("  No data retrieved for this section.", style="dim white"))
        console.print()
        return

    for bullet in bullets:
        console.print(Text(f"  • {bullet['text']}", style="white"))
        if bullet.get("url"):
            console.print(Text(f"    {bullet['url']}", style="dim"))
        console.print()


def print_so_what(results: list[dict]):
    console.print(Rule(style="dim white"))
    console.print(Text("SO WHAT?", style="bold white"))
    console.print()

    answers = [r.get("answer", "") for r in results if r]
    if not any(answers):
        console.print(
            Text(
                "  Insufficient data to generate synthesis.",
                style="italic dim white",
            )
        )
        console.print()
        return

    # Build a synthesis paragraph from the two answers
    funding_answer = answers[0] if len(answers) > 0 else ""
    behavior_answer = answers[1] if len(answers) > 1 else ""

    # Extract first meaningful sentence from each
    def first_sentence(text: str) -> str:
        for s in text.replace("\n", " ").split(". "):
            s = s.strip()
            if len(s) > 40:
                return s + ("." if not s.endswith(".") else "")
        return text[:200].strip()

    f1 = first_sentence(funding_answer)
    b1 = first_sentence(behavior_answer)

    synthesis = (
        f"{f1} "
        f"At the same time, {b1.lower()} "
        f"For founders building in Indian education, this signals a window where "
        f"capital is flowing toward products that meet learners where they are — "
        f"mobile-first, vernacular, and outcome-driven. "
        f"The founders who will win are those who combine the funding momentum with a "
        f"deep understanding of how Indian students actually learn today."
    )

    console.print(Text(f"  {synthesis}", style="italic white"))
    console.print()


def print_footer():
    console.print(Rule(style="dim white"))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(
        Text(
            f"Powered by Linkup API — linkup.so  ·  {timestamp}",
            style="dim white",
        ),
        justify="center",
    )
    console.print()


def main():
    api_key = os.environ.get("LINKUP_API_KEY", "").strip()
    if not api_key:
        console.print(
            "[red]Error: LINKUP_API_KEY environment variable is not set.[/red]"
        )
        console.print("[dim]Run: export LINKUP_API_KEY=your_key_here[/dim]")
        sys.exit(1)

    print_header()

    results = []
    for item in QUERIES:
        data = fetch_linkup(item["query"], item["label"], api_key)
        results.append(data)

    console.print()

    for i, item in enumerate(QUERIES):
        bullets = extract_bullets(results[i])
        print_section(item["section_title"], bullets)

    print_so_what(results)
    print_footer()


if __name__ == "__main__":
    main()
