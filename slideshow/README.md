# Slideshow

Générer des présentations HTML standalone avec Reveal.js. Supporte branding custom (couleurs, fonts, logo), plusieurs types de slides, et animations/transitions.

## Setup

```bash
cd ../../lib/slideshow && ./setup.sh
```

Pas de credentials nécessaires.

## Usage

```bash
cd ../../lib/slideshow && .venv/bin/python3 scripts/slideshow_maker.py generate \
  --slides slides.html \
  --output output/presentation.html \
  --branding config/default-branding.yaml \
  --title "My Presentation"
```

| Arg | Description | Default |
|-----|-------------|---------|
| `--slides` | Fichier HTML avec blocs `<section>` | requis |
| `--output` | Chemin du fichier HTML de sortie | `output/presentation.html` |
| `--branding` | Config YAML du branding | `config/default-branding.yaml` |
| `--title` | Titre de la présentation | `"Presentation"` |

## Workflow

1. L'utilisateur décrit les slides
2. Claude génère un fichier HTML avec des blocs `<section>` (format Reveal.js)
3. Le script wrap les slides avec le branding + Reveal.js en HTML standalone
4. L'utilisateur ouvre le fichier dans un navigateur

## Inputs / Outputs

- **config/** : branding YAML et configuration
- **output/** : présentations HTML générées
