#!/usr/bin/env python3
"""Slideshow Maker — generates standalone HTML presentations with Reveal.js."""

import click
import yaml
from pathlib import Path
from jinja2 import Template

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_BRANDING = SKILL_DIR / "config" / "default-branding.yaml"
DEFAULT_OUTPUT = SKILL_DIR / "output" / "presentation.html"

HTML_TEMPLATE = Template('''\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>

<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={{ title_font | urlencode }}:wght@300;400;500;600;700;800;900&family={{ body_font | urlencode }}:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<!-- Reveal.js -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css" id="theme">

<style>
  /* ===== RESET & BASE ===== */
  :root {
    --bg: {{ background }};
    --text-primary: {{ text_primary }};
    --text-secondary: {{ text_secondary }};
    --text-muted: {{ text_muted }};
    --accent: {{ accent }};
    --deep-blue: {{ deep_blue }};
    --medium-blue: {{ medium_blue }};
    --bright-blue: {{ bright_blue }};
    --heading-gradient: {{ heading_gradient }};
    --button-gradient: {{ button_gradient }};
    --button-gradient-hover: {{ button_gradient_hover }};
    --card-bg: {{ card_bg }};
    --card-border: {{ card_border }};
    --card-border-hover: {{ card_border_hover }};
    --card-radius: {{ card_radius }};
    --card-shadow-hover: {{ card_shadow_hover }};
    --card-backdrop-blur: {{ card_backdrop_blur }};
    --button-border: {{ button_border }};
    --button-shadow: {{ button_shadow }};
    --button-shadow-hover: {{ button_shadow_hover }};
    --glow-shadow: {{ glow_shadow }};
    --text-glow: {{ text_glow }};
    --font-heading: '{{ title_font }}', Arial, sans-serif;
    --font-body: '{{ body_font }}', Arial, sans-serif;
  }

  .reveal-viewport {
    background: var(--bg) !important;
  }

  .reveal {
    font-family: var(--font-body);
    color: var(--text-primary);
  }

  /* ===== TYPOGRAPHY ===== */
  .reveal h1, .reveal h2, .reveal h3, .reveal h4 {
    font-family: var(--font-heading);
    font-weight: 700;
    text-transform: none;
    letter-spacing: -0.02em;
  }

  .reveal h1 {
    font-size: 1.8em;
    font-weight: 800;
    background: var(--heading-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin-bottom: 0.3em;
  }

  .reveal h2 {
    font-size: 1.3em;
    font-weight: 700;
    background: var(--heading-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5em;
  }

  .reveal h3 {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--accent);
  }

  .reveal p, .reveal li {
    font-size: 0.7em;
    line-height: 1.6;
    color: var(--text-secondary);
  }

  .reveal .subtitle {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.3em;
  }

  .reveal .tagline {
    font-size: 0.75em;
    font-style: italic;
    color: var(--text-muted);
  }

  .reveal .highlight {
    color: var(--accent);
    font-weight: 600;
  }

  .reveal strong {
    color: var(--text-primary);
    font-weight: 700;
  }

  .reveal em {
    color: var(--text-muted);
  }

  /* ===== CARDS ===== */
  .reveal .card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--card-radius);
    padding: 0.8em 1em;
    backdrop-filter: blur(var(--card-backdrop-blur));
    -webkit-backdrop-filter: blur(var(--card-backdrop-blur));
    transition: all 0.3s ease;
    text-align: left;
  }

  .reveal .card:hover {
    border-color: var(--card-border-hover);
    box-shadow: var(--card-shadow-hover);
    transform: translateY(-2px);
  }

  .reveal .card h3 {
    margin-top: 0;
    margin-bottom: 0.2em;
  }

  .reveal .card p {
    font-size: 0.6em;
    color: var(--text-muted);
    margin: 0;
  }

  .reveal .card-icon {
    font-size: 1.2em;
    margin-bottom: 0.2em;
    display: block;
  }

  .reveal .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.2em;
    margin-top: 1em;
    width: 100%;
  }

  .reveal .cards-grid-3 {
    grid-template-columns: repeat(3, 1fr);
  }

  .reveal .cards-grid-2 {
    grid-template-columns: repeat(2, 1fr);
  }

  /* ===== TWO COLUMNS ===== */
  .reveal .two-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2em;
    align-items: center;
    width: 100%;
    text-align: left;
  }

  .reveal .two-columns img {
    max-width: 100%;
    border-radius: var(--card-radius);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  }

  /* ===== LISTS ===== */
  .reveal ul, .reveal ol {
    text-align: left;
    margin-left: 0;
    padding-left: 1.2em;
  }

  .reveal li {
    margin-bottom: 0.5em;
    padding-left: 0.3em;
  }

  .reveal li::marker {
    color: var(--accent);
  }

  /* ===== BUTTONS ===== */
  .reveal .btn {
    display: inline-block;
    background: var(--button-gradient);
    color: #fff;
    border: 1px solid var(--button-border);
    border-radius: 8px;
    padding: 0.7em 1.8em;
    font-family: var(--font-body);
    font-weight: 600;
    font-size: 0.9em;
    text-decoration: none;
    box-shadow: var(--button-shadow);
    transition: all 0.3s ease;
    cursor: pointer;
  }

  .reveal .btn:hover {
    background: var(--button-gradient-hover);
    box-shadow: var(--button-shadow-hover);
    transform: translateY(-1px);
  }

  /* ===== IMAGES ===== */
  .reveal img {
    max-width: 90%;
    max-height: 65vh;
    border-radius: 12px;
    border: none !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }

  .reveal .img-no-shadow img,
  .reveal img.no-shadow {
    box-shadow: none;
  }

  /* ===== DIVIDERS & SPACERS ===== */
  .reveal hr {
    border: none;
    height: 2px;
    background: var(--card-border);
    margin: 1.5em auto;
    width: 60%;
  }

  .reveal .spacer {
    height: 1em;
  }

  /* ===== GLOW EFFECTS ===== */
  .reveal .glow {
    text-shadow: var(--text-glow);
  }

  .reveal .glow-box {
    box-shadow: var(--glow-shadow);
  }

  /* ===== FRAGMENT ANIMATIONS ===== */
  .reveal .fragment {
    transition: all 0.4s ease;
  }

  .reveal .fragment.fade-up {
    transform: translateY(20px);
    opacity: 0;
  }

  .reveal .fragment.fade-up.visible {
    transform: translateY(0);
    opacity: 1;
  }

  /* ===== NUMBER / STAT BLOCKS ===== */
  .reveal .stat {
    text-align: center;
    padding: 0.5em;
  }

  .reveal .stat-number {
    font-family: var(--font-heading);
    font-size: 2em;
    font-weight: 800;
    background: var(--heading-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
  }

  .reveal .stat-label {
    font-size: 0.65em;
    color: var(--text-muted);
    margin-top: 0.3em;
  }

  /* ===== QUOTE ===== */
  .reveal blockquote {
    background: var(--card-bg);
    border-left: 4px solid var(--accent);
    border-radius: 0 var(--card-radius) var(--card-radius) 0;
    padding: 1em 1.5em;
    font-style: italic;
    color: var(--text-secondary);
    backdrop-filter: blur(var(--card-backdrop-blur));
    width: 85%;
    margin: 0.8em auto;
    box-shadow: none;
  }

  .reveal blockquote p {
    color: var(--text-secondary);
  }

  /* ===== TIMELINE ===== */
  .reveal .timeline {
    position: relative;
    padding-left: 2em;
    text-align: left;
  }

  .reveal .timeline::before {
    content: '';
    position: absolute;
    left: 0.5em;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--card-border);
  }

  .reveal .timeline-item {
    position: relative;
    margin-bottom: 1.5em;
    padding-left: 1em;
  }

  .reveal .timeline-item::before {
    content: '';
    position: absolute;
    left: -1.55em;
    top: 0.5em;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--accent);
    border: 2px solid var(--bg);
    box-shadow: 0 0 8px rgba(56, 182, 255, 0.4);
  }

  /* ===== SLIDE NUMBER ===== */
  .reveal .slide-number {
    font-family: var(--font-body);
    font-size: 0.7em;
    color: var(--text-muted);
    background: transparent !important;
  }

  /* ===== PROGRESS BAR ===== */
  .reveal .progress span {
    background: var(--accent) !important;
  }

  /* ===== CONTROLS ===== */
  .reveal .controls button {
    color: var(--accent) !important;
  }

  /* ===== LOGO ===== */
  {% if logo %}
  .reveal .slide-logo {
    position: fixed;
    top: 20px;
    left: 24px;
    height: 40px;
    z-index: 100;
    opacity: 0.8;
  }
  {% endif %}
</style>
</head>
<body>

{% if logo %}
<img src="{{ logo }}" class="slide-logo" alt="Logo">
{% endif %}

<div class="reveal">
  <div class="slides">
{{ slides_html }}
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script>
  Reveal.initialize({
    hash: true,
    slideNumber: true,
    transition: '{{ transition }}',
    transitionSpeed: 'default',
    backgroundTransition: 'fade',
    center: true,
    width: 1280,
    height: 720,
    margin: 0.08,
    plugins: []
  });
</script>
</body>
</html>
''')


def load_branding(path: Path) -> dict:
    """Load branding YAML config."""
    with open(path) as f:
        return yaml.safe_load(f)


def generate(slides_path: str, output_path: str, branding_path: str, title: str):
    """Generate a standalone HTML slideshow."""
    branding = load_branding(Path(branding_path))
    slides_html = Path(slides_path).read_text(encoding="utf-8")

    html = HTML_TEMPLATE.render(
        title=title,
        slides_html=slides_html,
        **branding,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    click.echo(f"✓ Generated: {out.resolve()}")


@click.group()
def cli():
    """Slideshow Maker — generate standalone HTML presentations."""
    pass


@cli.command()
@click.option("--slides", required=True, help="HTML file with <section> slide blocks")
@click.option("--output", default=str(DEFAULT_OUTPUT), help="Output HTML path")
@click.option("--branding", default=str(DEFAULT_BRANDING), help="YAML branding config")
@click.option("--title", default="Presentation", help="Presentation title")
def generate_cmd(slides, output, branding, title):
    """Generate a standalone HTML slideshow."""
    generate(slides, output, branding, title)


# Alias for convenience
cli.add_command(generate_cmd, name="generate")


if __name__ == "__main__":
    cli()
