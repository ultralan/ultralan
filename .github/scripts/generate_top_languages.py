"""从公开仓库生成 README 使用的语言统计 SVG。"""

from __future__ import annotations

import html
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen


USERNAME = "ultralan"
OUTPUT_PATH = Path("assets/top-languages.svg")
LANGUAGE_COLORS = {
    "Java": "#b07219",
    "Kotlin": "#A97BFF",
    "Python": "#3572A5",
    "C++": "#F34B7D",
    "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6",
    "Shell": "#89E051",
    "C": "#555555",
    "Rust": "#DEA584",
    "Go": "#00ADD8",
    "Lua": "#000080",
    "TeX": "#3D6117",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
}
FALLBACK_COLORS = ("#E93F73", "#6E40C9", "#2F81F7", "#D29922", "#1F883D")


def fetch_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ultralan-profile-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def collect_languages() -> dict[str, int]:
    repos = fetch_json(
        f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100"
    )
    totals: dict[str, int] = {}
    for repo in repos:
        if repo["fork"]:
            continue
        for language, bytes_count in fetch_json(repo["languages_url"]).items():
            totals[language] = totals.get(language, 0) + bytes_count
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True)[:10])


def color_for(language: str, index: int) -> str:
    return LANGUAGE_COLORS.get(language, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def render_card(languages: dict[str, int]) -> str:
    width = 760
    items = list(languages.items())
    rows = max(1, math.ceil(len(items) / 2))
    height = 190 + rows * 56
    total = sum(value for _, value in items)
    bar_x, bar_y, bar_width, bar_height = 80, 126, 600, 16

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">',
        '<title id="title">Most Used Languages</title>',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="#ffffff" stroke="#d0d7de" stroke-width="2"/>',
        '<text x="80" y="80" fill="#2f81f7" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="36" font-weight="700">Most Used Languages</text>',
        f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" rx="8"/></clipPath>',
        '<g clip-path="url(#bar)">',
    ]

    offset = bar_x
    for index, (_, bytes_count) in enumerate(items):
        segment_width = bar_width * bytes_count / total if total else 0
        parts.append(
            f'<rect x="{offset:.2f}" y="{bar_y}" width="{segment_width:.2f}" height="{bar_height}" fill="{color_for(items[index][0], index)}"/>'
        )
        offset += segment_width
    parts.append("</g>")

    if not items:
        parts.append('<text x="80" y="190" fill="#57606a" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="20">No public language data yet</text>')

    for index, (language, bytes_count) in enumerate(items):
        column = index % 2
        row = index // 2
        x = 80 + column * 330
        y = 198 + row * 56
        color = color_for(language, index)
        percentage = bytes_count / total * 100 if total else 0
        safe_language = html.escape(language)
        parts.extend(
            [
                f'<circle cx="{x + 10}" cy="{y - 7}" r="10" fill="{color}"/>',
                f'<text x="{x + 30}" y="{y}" fill="#3b4758" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="22">{safe_language} {percentage:.2f}%</text>',
            ]
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_card(collect_languages()), encoding="utf-8")
