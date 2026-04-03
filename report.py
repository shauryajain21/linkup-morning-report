import os
import sys
import time
import json
import argparse
import concurrent.futures
import requests
from datetime import datetime
from typing import Optional

try:
    from rich.console import Console
    from rich.text import Text
    from rich.rule import Rule
    from rich.table import Table
    from rich.panel import Panel

    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

LINKUP_API_URL = "https://api.linkup.so/v1/search"

DEFAULT_QUERIES = [
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
    {
        "label": "Government policy & regulation",
        "query": "India education policy NEP regulation updates 2026",
        "section_title": "GOVERNMENT POLICY & REGULATION",
    },
    {
        "label": "AI in education",
        "query": "AI tutoring personalized learning India EdTech 2026",
        "section_title": "AI IN EDUCATION",
    },
]


def print_header():
    if not HAS_RICH:
        print(f"\n{'='*60}")
        print(f"  linkup  |  EdTech Morning Report")
        print(f"  {datetime.now().strftime('%A, %d %B %Y')}")
        print(f"{'='*60}\n")
        return
    console.print()
    logo = Text("\u26A1 linkup", style="bold white")
    console.print(logo, justify="left")
    console.print(Text("EdTech Morning Report", style="bold white"), justify="left")
    console.print(
        Text(datetime.now().strftime("%A, %d %B %Y"), style="dim white"),
        justify="left",
    )
    console.print(Rule(style="dim white"))
    console.print()


def fetch_linkup(
    query: str, label: str, api_key: str, depth: str = "deep", timeout: int = 60
) -> Optional[dict]:
    if HAS_RICH:
        console.print(f"[yellow]\u2192 Calling Linkup API: {label}...[/yellow]")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "depth": depth,
        "outputType": "sourcedAnswer",
    }

    start = time.time()
    try:
        if HAS_RICH:
            with console.status("[yellow]  fetching...[/yellow]", spinner="dots"):
                response = requests.post(
                    LINKUP_API_URL, json=payload, headers=headers, timeout=timeout
                )
        else:
            print(f"  -> Fetching: {label}...")
            response = requests.post(
                LINKUP_API_URL, json=payload, headers=headers, timeout=timeout
            )

        response.raise_for_status()
        data = response.json()
        elapsed = time.time() - start

        sources = data.get("sources", [])
        source_count = len(sources)
        if HAS_RICH:
            console.print(
                f"[green]\u2713 Done ({source_count} source{'s' if source_count != 1 else ''} found, {elapsed:.1f}s)[/green]"
            )
            console.print()
        else:
            print(
                f"  \u2713 Done ({source_count} source{'s' if source_count != 1 else ''}, {elapsed:.1f}s)"
            )
        return data

    except requests.exceptions.HTTPError as e:
        msg = f"API error ({response.status_code})"
        try:
            err_data = response.json()
            detail = (
                err_data.get("message")
                or (err_data.get("error", {}) if isinstance(err_data.get("error"), dict) else err_data.get("error"))
                or err_data.get("detail")
                or str(e)
            )
            if isinstance(detail, dict):
                detail = detail.get("message", str(e))
            msg = f"API error ({response.status_code}): {detail}"
        except Exception:
            msg = f"API error ({response.status_code}): {e}"

        if HAS_RICH:
            console.print(f"[red]\u2717 {msg}[/red]")
            console.print()
        else:
            print(f"  \u2717 {msg}")
        return None
    except requests.exceptions.Timeout:
        if HAS_RICH:
            console.print(f"[red]\u2717 Request timed out after {timeout}s[/red]")
            console.print()
        else:
            print(f"  \u2717 Timeout after {timeout}s")
        return None
    except requests.exceptions.ConnectionError as e:
        if HAS_RICH:
            console.print(f"[red]\u2717 Connection error: {e}[/red]")
            console.print()
        else:
            print(f"  \u2717 Connection error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        if HAS_RICH:
            console.print(f"[red]\u2717 Request error: {e}[/red]")
            console.print()
        else:
            print(f"  \u2717 Error: {e}")
        return None


def extract_bullets(data: dict, max_bullets: int = 5) -> list[dict]:
    """Return up to max_bullets items with 'text' and 'url' keys."""
    if not data:
        return []

    answer = data.get("answer", "")
    sources = data.get("sources", [])

    if not answer:
        return []

    bullets = []
    # Split on sentence boundaries more carefully
    import re
    sentences = re.split(r'(?<=[.!?])\s+', answer.replace("\n", " "))
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    for i, sentence in enumerate(sentences[:max_bullets]):
        if not sentence[-1] in ".!?":
            sentence += "."
        url = sources[i]["url"] if i < len(sources) else ""
        bullets.append({"text": sentence, "url": url})

    return bullets


def print_section(title: str, bullets: list[dict]):
    if not HAS_RICH:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        if not bullets:
            print("  No data retrieved.")
            return
        for b in bullets:
            print(f"\n  \u2022 {b['text']}")
            if b.get("url"):
                print(f"    {b['url']}")
        print()
        return

    console.print(Rule(style="dim white"))
    console.print(Text(title, style="bold white"))
    console.print()

    if not bullets:
        console.print(Text("  No data retrieved for this section.", style="dim white"))
        console.print()
        return

    for bullet in bullets:
        console.print(Text(f"  \u2022 {bullet['text']}", style="white"))
        if bullet.get("url"):
            console.print(Text(f"    {bullet['url']}", style="dim"))
        console.print()


def print_so_what(results: list[dict]):
    answers = [r.get("answer", "") for r in results if r]
    if not HAS_RICH:
        print(f"\n{'='*60}")
        print("  SO WHAT?")
        print(f"{'='*60}")
        if not any(answers):
            print("  Insufficient data to generate synthesis.")
            print()
            return
    else:
        console.print(Rule(style="dim white"))
        console.print(Text("SO WHAT?", style="bold white"))
        console.print()
        if not any(answers):
            console.print(
                Text(
                    "  Insufficient data to generate synthesis.",
                    style="italic dim white",
                )
            )
            console.print()
            return

    def first_sentence(text: str) -> str:
        import re
        for s in re.split(r'(?<=[.!?])\s+', text.replace("\n", " ")):
            s = s.strip()
            if len(s) > 40:
                return s + ("" if s[-1] in ".!?" else ".")
        return text[:200].strip()

    parts = [first_sentence(a) for a in answers[:3] if a]

    synthesis = parts[0] + " " if parts else ""
    if len(parts) >= 2:
        synthesis += f"At the same time, {parts[1][0].lower()}{parts[1][1:]} "
    if len(parts) >= 3:
        synthesis += f"Meanwhile, {parts[2][0].lower()}{parts[2][1:]} "
    synthesis += (
        "For founders building in Indian education, this signals a window where "
        "capital is flowing toward products that meet learners where they are \u2014 "
        "mobile-first, vernacular, and outcome-driven."
    )

    if HAS_RICH:
        console.print(Text(f"  {synthesis}", style="italic white"))
        console.print()
    else:
        print(f"\n  {synthesis}\n")


def print_footer(total_time: float, total_sources: int):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not HAS_RICH:
        print(f"{'='*60}")
        print(f"  Powered by Linkup API \u2014 linkup.so  |  {timestamp}")
        print(f"  {total_sources} sources  |  {total_time:.1f}s total")
        print(f"{'='*60}\n")
        return

    console.print(Rule(style="dim white"))
    console.print(
        Text(
            f"Powered by Linkup API \u2014 linkup.so  \u00B7  {timestamp}  \u00B7  {total_sources} sources  \u00B7  {total_time:.1f}s",
            style="dim white",
        ),
        justify="center",
    )
    console.print()


def export_json(results: list[dict], queries: list[dict], output_file: str):
    """Export report data as JSON."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "sections": [],
    }
    for i, item in enumerate(queries):
        section = {
            "title": item["section_title"],
            "query": item["query"],
            "bullets": extract_bullets(results[i]) if results[i] else [],
            "raw_answer": results[i].get("answer", "") if results[i] else "",
            "sources": results[i].get("sources", []) if results[i] else [],
        }
        report["sections"].append(section)

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report exported to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Linkup EdTech Morning Report \u2014 real-time intelligence for Indian EdTech"
    )
    parser.add_argument(
        "--depth",
        choices=["fast", "standard", "deep"],
        default="deep",
        help="Search depth (default: deep)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Request timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run queries in parallel for faster results",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        metavar="FILE",
        help="Export report as JSON to FILE",
    )
    parser.add_argument(
        "--query",
        action="append",
        help="Add a custom query (can be repeated)",
    )

    args = parser.parse_args()

    api_key = os.environ.get("LINKUP_API_KEY", "").strip()
    if not api_key:
        if HAS_RICH:
            console.print(
                "[red]Error: LINKUP_API_KEY environment variable is not set.[/red]"
            )
            console.print("[dim]Run: export LINKUP_API_KEY=your_key_here[/dim]")
        else:
            print("Error: LINKUP_API_KEY environment variable is not set.")
            print("Run: export LINKUP_API_KEY=your_key_here")
        sys.exit(1)

    # Build query list
    query_list = list(DEFAULT_QUERIES)
    if args.query:
        for q in args.query:
            label = q[:40] + "..." if len(q) > 40 else q
            query_list.append(
                {"label": label, "query": q, "section_title": label.upper()}
            )

    print_header()

    start_time = time.time()
    total_sources = 0

    if args.parallel:
        # Parallel execution
        if HAS_RICH:
            console.print("[yellow]Running queries in parallel...[/yellow]\n")
        else:
            print("Running queries in parallel...\n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    fetch_linkup, item["query"], item["label"], api_key, args.depth, args.timeout
                ): i
                for i, item in enumerate(query_list)
            }
            results = [None] * len(query_list)
            for future in concurrent.futures.as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    if HAS_RICH:
                        console.print(f"[red]\u2717 Query {idx + 1} failed: {e}[/red]")
                    else:
                        print(f"  \u2717 Query {idx + 1} failed: {e}")
                    results[idx] = None
    else:
        # Sequential execution
        results = []
        for item in query_list:
            data = fetch_linkup(item["query"], item["label"], api_key, args.depth, args.timeout)
            results.append(data)

    if HAS_RICH:
        console.print()

    for i, item in enumerate(query_list):
        bullets = extract_bullets(results[i])
        print_section(item["section_title"], bullets)
        if results[i]:
            total_sources += len(results[i].get("sources", []))

    print_so_what(results)

    total_time = time.time() - start_time
    print_footer(total_time, total_sources)

    # Export if requested
    if args.export_json:
        export_json(results, query_list, args.export_json)


if __name__ == "__main__":
    main()
