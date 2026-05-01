# Profile Manager

Gère les profils de credentials pour les outils CLI du workspace.

## Setup

```bash
./setup.sh
```

## Usage

```bash
# Lister tous les outils et leurs profils
profile list

# Lister les profils d'un outil
profile list telegram

# Ajouter un profil interactivement (lit meta.yaml pour les variables requises)
profile add whatsapp pro

# Importer depuis un config.json ou .env existant
profile import telegram default

# Voir un profil (secrets masqués)
profile show telegram default

# Voir un profil (secrets visibles)
profile show telegram default --secrets

# Changer le profil par défaut
profile set-default telegram alerts-bot

# Supprimer un profil
profile remove whatsapp old-account
```

## Comment ça marche

Les profils vivent dans `lib/.profiles/<tool-id>/<profile-name>.json`.
Un fichier `_default` dans chaque dossier indique le profil par défaut.

Chaque CLI résout son profil via le resolver (`lib/.profiles/resolver.py`) :
1. `--profile <name>` (argument CLI explicite)
2. `<TOOL_ID>_PROFILE` (variable d'environnement)
3. `_default` (fichier dans le dossier du tool)
4. Profil unique auto (s'il n'y en a qu'un)
