# Skill Creator

Guide et outils pour creer et packager des skills Claude Code. Fournit des scripts d'initialisation, de validation et de packaging.

## Setup

Aucune installation requise. Les scripts utilisent Python 3 (stdlib).

## Credentials

Aucune credential necessaire.

## Usage

```bash
# Initialiser un nouveau skill
python3 ../../lib/skill-creator/scripts/init_skill.py

# Valider un skill existant
python3 ../../lib/skill-creator/scripts/quick_validate.py <path-to-skill>

# Packager un skill
python3 ../../lib/skill-creator/scripts/package_skill.py <path-to-skill>
```

## Resources

- `SKILL.md` : Guide complet de conception de skills (principes, anatomie, progressive disclosure)
- `references/anatomy.md` : Structure detaillee d'un skill
- `references/progressive-disclosure.md` : Patterns de chargement progressif
- `references/output-patterns.md` : Patterns de sortie
- `references/workflows.md` : Workflows de creation
