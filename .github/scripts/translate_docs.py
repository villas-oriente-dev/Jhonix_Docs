#!/usr/bin/env python3
"""
translate_docs.py
-----------------
Translates Markdown / MDX documentation files from Spanish to English
using the Google Gemini API (gemini-2.0-flash).

Usage:
    python .github/scripts/translate_docs.py <changed_files.txt>

Environment:
    GEMINI_API_KEY  — required, set as a GitHub Actions secret.
"""

import os
import sys
import time
import textwrap
from google import genai
from google.genai import types

# ── Settings ──────────────────────────────────────────────────────────────────
GEMINI_MODEL   = "gemini-2.0-flash"
SOURCE_ROOT    = "src/content/docs"
DEST_ROOT      = "src/content/docs/en"
DELAY_SECONDS  = 4          # pause between API calls (free tier: 15 req/min)
MAX_RETRIES    = 3          # retries per file on transient errors

# ── Translation prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""\
    You are a professional technical documentation translator.
    Translate Markdown / MDX content from Spanish to English.

    ══ TRANSLATE ════════════════════════════════════════════════════════
    • Plain prose, descriptions, explanations
    • Frontmatter VALUES that are human-readable text
        title: "Mi aplicación"  →  title: "My application"
    • Text inside MDX / Starlight component props that are clearly labels
        <Card title="Configuración">  →  <Card title="Configuration">
    • Headings, list items, table cells, captions
    • Body text of admonitions  (:::note … :::  /  :::tip … :::  etc.)

    ══ DO NOT TRANSLATE ══════════════════════════════════════════════════
    • Fenced code blocks  (``` … ```)  — copy them byte-for-byte
    • Inline code  (`…`)
    • Frontmatter KEYS  (title:, description:, sidebar:, template:, …)
    • MDX import / export statements
    • Component / tag NAMES  (<Card>, <CardGrid>, <Steps>, <Tabs>, …)
    • Component PROP NAMES  (title=, icon=, label=, href=, variant=, …)
    • URLs, file paths, anchor links  (#…)
    • API keys, secret names, environment variable identifiers
    • Package names, CLI commands  (npm, pnpm, astro, firebase, …)
    • Admonition TYPE keywords  (note, tip, caution, danger, aside)
    • Anything that looks like code, a command, or a technical identifier

    ══ FORMATTING ════════════════════════════════════════════════════════
    • Preserve ALL blank lines, indentation, and document structure exactly.
    • Preserve ALL Markdown syntax: #, **, *, >, -, 1., |, etc.
    • Return ONLY the translated document — no explanations, no preamble,
      no surrounding code fences.
""")


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("ERROR: GEMINI_API_KEY environment variable is not set.")
    return genai.Client(api_key=api_key)


def translate_content(client: genai.Client, content: str) -> str:
    """Send content to Gemini and return the translated text."""
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=content,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,     # low temperature → consistent, literal output
            max_output_tokens=8192,
        ),
    )

    translated = response.text.strip()

    # Safety net: sometimes the model wraps output in ``` fences despite
    # being told not to — strip them if present.
    if translated.startswith("```"):
        lines = translated.splitlines()
        lines = lines[1:]                                # drop opening fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]                           # drop closing fence
        translated = "\n".join(lines).strip()

    return translated


def dest_path_for(source_path: str) -> str:
    """Compute the destination path in the /en/ subtree."""
    rel = os.path.relpath(source_path, SOURCE_ROOT)
    return os.path.join(DEST_ROOT, rel)


def translate_file(client: genai.Client, source_path: str) -> bool:
    """
    Translate a single file.  Returns True on success, False on failure.
    """
    if not os.path.isfile(source_path):
        print(f"  [SKIP] not found / deleted: {source_path}")
        return True

    content = open(source_path, encoding="utf-8").read()

    if not content.strip():
        print(f"  [SKIP] empty file: {source_path}")
        return True

    dest = dest_path_for(source_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  [→] Translating ({attempt}/{MAX_RETRIES}): {source_path}")
            translated = translate_content(client, content)
            break
        except Exception as exc:  # noqa: BLE001
            print(f"  [!] Error on attempt {attempt}: {exc}")
            if attempt == MAX_RETRIES:
                print(f"  [✗] Giving up on: {source_path}")
                return False
            wait = DELAY_SECONDS * attempt
            print(f"  [~] Waiting {wait}s before retry …")
            time.sleep(wait)

    with open(dest, "w", encoding="utf-8") as f:
        f.write(translated)
        if not translated.endswith("\n"):
            f.write("\n")

    print(f"  [✓] Written: {dest}")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: translate_docs.py <changed_files.txt>")

    list_path = sys.argv[1]
    if not os.path.isfile(list_path):
        sys.exit(f"File not found: {list_path}")

    files = [
        line.strip()
        for line in open(list_path, encoding="utf-8")
        if line.strip()
    ]

    if not files:
        print("No files to translate — nothing to do.")
        return

    client = build_client()
    ok_count = 0
    fail_count = 0

    print(f"\nFiles to translate: {len(files)}")
    print("─" * 50)

    for i, file_path in enumerate(files):
        success = translate_file(client, file_path)
        if success:
            ok_count += 1
        else:
            fail_count += 1

        # Pause between requests to respect API rate limits
        if i < len(files) - 1:
            time.sleep(DELAY_SECONDS)

    print("─" * 50)
    print(f"Done.  ✓ {ok_count} translated  |  ✗ {fail_count} failed")

    if fail_count:
        sys.exit(1)   # fail the Action step if any file couldn't be translated


if __name__ == "__main__":
    main()
