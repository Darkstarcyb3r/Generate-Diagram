#!/usr/bin/env python3.10
"""
Claude → style-enriched prompt → PaperBanana → upscaled output → outputs/

1. Claude API merges the raw diagram description with the locked style
   template into a single, coherent PaperBanana prompt.
2. The enriched prompt is written to method.txt.
3. PaperBanana runs and drops its output into outputs/.
4. Output is upscaled 3x via Lanczos for print-quality resolution.

The MCP tool returns paths to the original and upscaled PNGs.
"""

import os
import re
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(Path.home() / "Desktop/paperBanana/.env")

PAPERBANANA_DIR = Path.home() / "Desktop/paperBanana"  # set to your own directory
STYLE_FILE      = PAPERBANANA_DIR / "diagram_style_template.txt"  # do not append, integrate
OUTPUTS_DIR     = PAPERBANANA_DIR / "outputs"  # set to your own directory

CLAUDE_MODEL  = "claude-opus-4-7"  # select your own model
MAX_TOKENS    = 4096
UPSCALE_FACTOR = 3  # 1344×768 → 4032×2304


mcp = FastMCP("diagram-generator")


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_style() -> str:
    if STYLE_FILE.exists():
        return STYLE_FILE.read_text().strip()
    return ""


def enrich_prompt(raw_prompt: str, style: str) -> str:
    """
    Send the raw diagram description + style template to Claude.
    Claude returns a single, unified PaperBanana prompt with style woven in.
    Content is locked — no additions, no omissions.
    """
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env var is not set")

    client = anthropic.Anthropic(api_key=api_key)

    instruction = f"""You are writing a prompt for PaperBanana, an AI diagramming tool.

Rewrite the DIAGRAM CONTENT below as a single unified PaperBanana prompt that
fully integrates the STYLE REQUIREMENTS. Weave style into the description —
exact colors, font sizes, shadow depth, icon style, spacing — so PaperBanana
receives one coherent, specific, style-aware prompt.

CRITICAL CONTENT RULES:
- Render ONLY what is explicitly listed in DIAGRAM CONTENT. Nothing else.
- Do NOT invent, add, or infer any nodes, labels, modules, connections, or
  concepts not present in the original description.
- Do NOT rename or reinterpret any element.
- Every element listed must appear. No omissions.
- Scientific and structural accuracy is non-negotiable.

DIAGRAM CONTENT
---
{raw_prompt}
---

STYLE REQUIREMENTS
---
{style}
---

Output only the enriched prompt. No commentary, no headers, no markdown.
"""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": instruction}],
    )

    return message.content[0].text.strip()


def upscale_png(src: Path, scale: int = UPSCALE_FACTOR) -> Path:
    """Upscale a PNG by `scale`x using Lanczos resampling. Returns the new path."""
    from PIL import Image

    img = Image.open(src)
    new_size = (img.width * scale, img.height * scale)
    upscaled = img.resize(new_size, Image.LANCZOS)
    dest = src.parent / f"{src.stem}_4k{src.suffix}"
    upscaled.save(dest, dpi=(300, 300))
    return dest


def find_pb_output(caption: str) -> Path | None:
    """Locate the most recent PaperBanana final_output.png."""
    folder = OUTPUTS_DIR / caption
    if folder.exists():
        png = folder / "final_output.png"
        if png.exists():
            return png
    pngs = sorted(
        OUTPUTS_DIR.rglob("final_output.png"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return pngs[0] if pngs else None


def safe_filename(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", s).strip().replace(" ", "_") or "diagram"


# ── MCP tool ───────────────────────────────────────────────────────────────────

@mcp.tool()
def generate_diagram(text: str, caption: str = "Diagram") -> str:
    """
    Generate a diagram via: Claude enrichment → PaperBanana → 4K upscale → outputs/

    Pass the raw diagram content. Claude integrates the locked style template
    into a single unified prompt for PaperBanana, then the output is upscaled 3x.

    Returns paths to the original and upscaled PNGs.
    """
    style = load_style()

    # Step 1 — Claude merges prompt + style into one enriched prompt
    if style:
        try:
            enriched = enrich_prompt(text, style)
        except Exception as e:
            return f"❌ Claude enrichment step failed: {e}"
    else:
        enriched = text

    # Step 2 — Write enriched prompt to method.txt
    method_file = PAPERBANANA_DIR / "method.txt"
    method_file.write_text(enriched)

    # Step 3 — Run PaperBanana
    pb = subprocess.run(
        [
            "paperbanana", "generate",
            "--input",   str(method_file),
            "--caption", caption,
            "--config",  str(PAPERBANANA_DIR / "free_config.yaml"),
        ],
        capture_output=True,
        text=True,
        cwd=str(PAPERBANANA_DIR),
    )

    if pb.returncode != 0:
        return f"❌ PaperBanana error:\n{pb.stderr}"

    # Step 4 — Locate output
    png = find_pb_output(caption)
    if not png:
        return "❌ Could not locate PaperBanana output PNG"

    # Step 5 — Upscale 3x for print quality
    try:
        upscaled = upscale_png(png)
        return f"✅ Done\n  PNG:     {png}\n  4K PNG:  {upscaled}"
    except Exception as e:
        return f"✅ Done (upscale failed: {e})\n  PNG: {png}"


if __name__ == "__main__":
    mcp.run()
