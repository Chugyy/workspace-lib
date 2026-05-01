# Image Generator

Generate images via OpenAI gpt-image-2 (default) or NanoBanana API. Supports text-to-image, image editing, thumbnails.

## Setup

1. `cp .env.example .env`
2. Remplir les variables (voir ci-dessous)
3. `./setup.sh` (installe le venv + dependances automatiquement)

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `NANOBANANA_API_KEY` | https://nanobanana.com |
| `PERSONAL_CLOUD_KEY` | Cle Personal Cloud (optionnel, pour `--cloud-upload`) |

## Usage

```bash
cd ../../lib/image-generator

# Generer une image (OpenAI, defaut)
./setup.sh generate -p "A futuristic dashboard with dark theme" -f 16:9 --resolution 2k -q high

# Generer avec NanoBanana
./setup.sh generate -p "A landscape" --provider nanobanana -m pro -f 16:9

# Image editing avec reference
./setup.sh generate -p "Add dramatic lighting" -r photo.png -f 16:9 -q high

# Lister les modeles
./setup.sh models

# Test de connexion
./setup.sh test
```

Pour le detail complet des options et le guide thumbnails, voir `SKILL.md`.

## Inputs / Outputs

- **assets/hugo-photos/** : Photos de reference Hugo (PNG, detourees)
- **output/** : Images generees (gitignore)
