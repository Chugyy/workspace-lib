# TTS

Text-to-speech local via Kokoro ONNX. Cross-platform (Linux x86_64 + macOS), inference CPU rapide (~0.25x RTF), preprocessing markdown intelligent, pauses naturelles entre phrases et paragraphes.

## Setup

```bash
cd ../../lib/tts && ./setup.sh
```

Le setup installe les dependances Python et telecharge automatiquement les modeles Kokoro ONNX (~311 MB) dans `models/`. Pas de credentials necessaires.

## Credentials

Aucune. Les modeles sont locaux et telecharges automatiquement par `setup.sh`.

## Usage

```bash
# Synthese avec pauses naturelles (defaut: francais)
tts say "Bonjour. Voici un message en francais."

# Sauver dans un fichier
tts say "Texte a narrer." -o narration.wav

# Voix anglaise
tts say "Hello world." -v af_heart -l en-us -o hello.wav

# Mode simple (sans controle de pauses)
tts generate "Quick test." -o test.wav

# Previsualiser le preprocessing (sans generer d'audio)
tts preview "## Mon titre\n\nTexte avec **gras** et `code`."

# Lister les voix disponibles
tts voices

# Lire depuis stdin
cat article.md | tts say -o article.wav
```

## Commandes

| Commande | Description |
|----------|-------------|
| `say` | Synthese avec pauses naturelles, preprocessing markdown, controle de vitesse |
| `generate` | Synthese simple (pas de controle de pauses) |
| `voices` | Liste les voix disponibles par langue |
| `preview` | Affiche le texte apres preprocessing (sans generer d'audio) |

## Voix disponibles

| Prefixe | Langue | Voix |
|---------|--------|------|
| `ff_` | Francais | `ff_siwis` (defaut) |
| `af_` | Anglais US (F) | `af_heart`, `af_bella`, `af_nova`, `af_sky` |
| `am_` | Anglais US (M) | `am_adam`, `am_echo`, `am_michael` |
| `bf_` | Anglais GB (F) | `bf_alice`, `bf_emma` |
| `bm_` | Anglais GB (M) | `bm_daniel`, `bm_george` |

## Important pour le francais

Toujours ecrire les vrais accents : e, e, e, a, a, u, u, o, i, i, c. Le modele lit phonetiquement.

## Python API

```python
from tts_engine.engine import TTSEngine, PauseConfig

engine = TTSEngine()

# Generer en memoire
result = engine.generate("Bonjour.", voice="ff_siwis", lang="fr-fr")
print(f"Duree: {result.duration:.1f}s, RTF: {result.rtf:.2f}x")

# Sauver dans un fichier
path, result = engine.save("Texte.", "output.wav", voice="ff_siwis", lang="fr-fr")

# Controle des pauses
pause = PauseConfig(after_sentence=0.4, after_paragraph=0.8, speed=0.9)
result = engine.generate("Texte.", pause=pause)
```

## Preprocessing markdown

Le preprocesseur (`tts_engine.preprocessor`) transforme le markdown en texte parlable :
- Supprime les blocs mermaid et code
- Convertit les tableaux en phrases naturelles
- Retire la syntaxe markdown (gras, italique, titres)
- Supprime les emojis et URLs
- Applique un dictionnaire de prononciation (acronymes tech, anglicismes)
