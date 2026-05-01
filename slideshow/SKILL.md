---
name: slideshow-maker
description: Generate standalone HTML slideshows with Reveal.js. Use when the user wants to create presentations, pitch decks, or slide decks. Supports custom branding (colors, fonts, logo), multiple slide types (title, content, cards, images, two-columns), and smooth animations/transitions.
---

# Slideshow Maker

## Setup

```bash
cd .claude/skills/slideshow-maker && ./setup.sh
```

## Usage

```bash
cd .claude/skills/slideshow-maker && .venv/bin/python3 scripts/slideshow_maker.py generate \
  --slides slides.html \
  --output output/presentation.html \
  --branding config/default-branding.yaml \
  --title "My Presentation"
```

## Arguments

```bash
cd .claude/skills/slideshow-maker && .venv/bin/python3 scripts/slideshow_maker.py generate --help
```

| Arg | Description | Default |
|-----|-------------|---------|
| `--slides` | HTML file containing `<section>` slide blocks | required |
| `--output` | Output HTML file path | `output/presentation.html` |
| `--branding` | YAML branding config | `config/default-branding.yaml` |
| `--title` | Presentation title | `"Presentation"` |

## Workflow

1. User describes slides (batch or one by one)
2. Claude generates an HTML file with `<section>` blocks (Reveal.js format)
3. Script wraps slides with branding + Reveal.js into standalone HTML
4. User opens the output file in browser

## Branding Config

Edit `config/default-branding.yaml` to customize colors, fonts, logo.

## Slide Types

Use Reveal.js HTML format inside `<section>` tags:
- **Title slide**: centered h1 + subtitle
- **Content**: h2 + fragments (progressive reveal with `class="fragment"`)
- **Cards**: grid layout with styled card divs
- **Image**: full or partial image slides
- **Two-columns**: side-by-side layout

## Règles de design (OBLIGATOIRES)

Ces règles viennent de feedbacks utilisateur. Les appliquer systématiquement.

### Typographie & tailles
- **Ne jamais utiliser de inline font-size en `em`** — les tailles Reveal.js se cumulent et cassent tout. Utiliser les classes CSS du template (`h2`, `h3`, `p`, `.subtitle`, `.highlight`, `.stat-number`, `.stat-label`).
- Les textes dans les cards doivent rester compacts : `font-size: 0.65em` max pour les contenus secondaires.
- Ne pas mettre de `<h3>` dans une card si c'est juste un label — utiliser `<p>` avec la bonne classe.

### Layout
- **Layout par défaut : texte à gauche, illustration à droite** (`.two-columns`). Sauf pour les slides de récap/KPI/CTA qui peuvent être centrées.
- Les SVG (schémas, graphiques) doivent être **larges** : minimum 380x380 pour un radar/araignée, minimum 420x380 pour un schéma multi-éléments.
- Les éléments SVG (rect, text) doivent avoir des tailles lisibles : `font-size="16"` minimum, rect de hauteur 42px minimum.

### Cards & composants
- **Toujours utiliser les classes du template** (`.card`, `.card-tech`, `.cards-grid`, `.stat`, `.timeline`) au lieu de styles inline avec border/background.
- Ne pas utiliser `.timeline` quand il y a des problèmes d'alignement point/ligne — préférer des cards numérotées.
- Les cards de features en grille : utiliser `grid-template-columns: 1fr 1fr` (2x2) plutôt que 4 empilées verticalement quand l'espace est limité.
- Les KPIs/stats : toujours **côte à côte** (`repeat(3, 1fr)`) et non empilés verticalement.

### Couleurs
- Rester dans le thème bleu (`var(--accent)`, `var(--card-border)`, etc.). Ne pas introduire de rouge sauf pour des éléments négatifs explicites (croix ✗, warnings ⚠).
- Pas de bordures blanches ni de fonds blancs — dark theme uniquement.

### Contenu
- Les slides de CTA n'ont pas besoin de bouton si c'est pour une vidéo filmée — juste afficher le lien (ex: `calendly.com/...`).
- Les slides de résultats : titre + contexte en haut, KPIs en dessous côte à côte.

## Output

Generated HTML files are saved in `output/`. Open in any browser.
