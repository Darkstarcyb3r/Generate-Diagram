# PaperBanana Diagram Generator

An MCP server that turns a plain-text diagram description into a styled, print-quality figure — automatically.

**Pipeline:** Claude enriches your prompt with the style template → PaperBanana generates the image → output is upscaled 3x to 4K at 300 DPI.

---

## How It Works

```
Your prompt
    ↓
Claude (claude-opus-4-7)
  reads prompt + diagram_style_template.txt
  writes one unified, style-aware prompt
    ↓
PaperBanana
  generates diagram via Gemini VLM + image model
    ↓
outputs/ folder
  final_output.png       (native resolution)
  final_output_4k.png    (3x upscaled, 300 DPI)
```

---

## Requirements

- Python 3.10+
- [PaperBanana](https://github.com/paperbanana/paperbanana) installed and on your PATH
- An Anthropic API key
- A Google API key (for Gemini VLM + image generation)

Install Python dependencies:

```bash
pip install anthropic python-dotenv pillow
```

---

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**2. Add your API keys**

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```
GOOGLE_API_KEY=your-google-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**3. Configure the MCP server in Claude Code**

Add the server to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "diagram-generator": {
      "command": "python3",
      "args": ["/path/to/mcp_diagram_server.py"]
    }
  }
}
```

Restart Claude Code. The `generate_diagram` tool will appear automatically.

---

## Usage

In Claude Code, call the tool with a plain-text description of your diagram:

```
generate_diagram(
  text="Your diagram description here...",
  caption="MyDiagram"
)
```

**Tips for good results:**
- List every element explicitly — nodes, labels, connections, sections
- Describe the layout (top-to-bottom, left-to-right, two sections, etc.)
- Do not leave anything implicit — PaperBanana will invent content to fill gaps
- The style template handles all visual decisions; focus your prompt on structure and content

Output lands in `outputs/` as a timestamped run folder containing the PNG and 4K upscale.

---

## Customizing the Style

Edit `diagram_style_template.txt` to change the visual language. The current template produces:

- White background, minimal academic style
- Color palette: sky-blue→deep-purple gradient, neon green accent, mint→pale-green gradient
- Helvetica Light, 14pt titles on `#0F1226` pill backgrounds, 10pt grey body text
- 2px stroke icons, soft drop shadows, 25px grid spacing

The style is **integrated** into every prompt by Claude — not appended. Claude reads both your description and the style file and writes a single unified prompt for PaperBanana.

---

## Files

| File | Purpose |
|------|---------|
| `mcp_diagram_server.py` | MCP server — the full pipeline |
| `diagram_style_template.txt` | Visual style rules |
| `free_config.yaml` | PaperBanana model + pipeline config |
| `.env.example` | API key template |

---

## Models Used

| Step | Provider | Model |
|------|----------|-------|
| Prompt enrichment | Anthropic | claude-opus-4-7 |
| VLM / planning | Google | gemini-2.5-flash |
| Image generation | Google | gemini-2.5-flash-image |

Models can be swapped in `mcp_diagram_server.py` (Claude) and `free_config.yaml` (PaperBanana).
