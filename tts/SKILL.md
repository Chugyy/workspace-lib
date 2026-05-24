---
name: tts-engine
description: Local text-to-speech via Kokoro ONNX. Cross-platform (Linux + macOS), CPU inference rapide (~0.25x RTF). Preprocessing markdown, pauses naturelles, dictionnaire de prononciation. Use for voiceovers, narration, notifications, or any text-to-audio need.
---

# TTS Engine

Text-to-speech local via Kokoro ONNX avec preprocessing markdown et pauses naturelles.

## Setup

```bash
cd ../../lib/tts && ./setup.sh
```

Le setup telecharge automatiquement les modeles Kokoro ONNX (~311 MB).

## Usage rapide (francais)

```bash
# Synthese avec pauses naturelles
tts say "Bonjour. Voici un message en francais avec une voix naturelle."

# Sauver dans un fichier
tts say "Texte a narrer." -o narration.wav

# Depuis un fichier markdown
cat article.md | tts say -o article.wav
```

## IMPORTANT pour le francais

**Toujours ecrire les vrais accents** : e, e, e, a, a, u, u, o, i, c.

Le modele lit phonetiquement. `degres` sera prononce "degress" (sans accent), `degres` sera correct.

## Controler l'emotion

Pas de parametre d'emotion -- on controle via le **texte lui-meme** :

| Effet voulu | Comment l'ecrire |
|-------------|-------------------|
| Neutre/pose | Phrases longues, points seulement, pas de "salut" |
| Joyeux | `!`, "Oh !", "Genial !", phrases courtes |
| Calme/meditatif | Phrases lentes, "...", pauses |
| Serieux | Vocabulaire formel, structure professionnelle |
| Triste | "...", "C'est dur", phrases hesitantes |

## Commandes

```bash
# Synthese avec pauses naturelles (defaut: francais, voix ff_siwis)
tts say "Texte ici"
tts say "Texte" -v ff_siwis -o output.wav
tts say "Hello world." -v af_heart -l en-us -o hello.wav

# Synthese simple (sans controle de pauses)
tts generate "Quick output." -o speech.wav

# Previsualiser le preprocessing markdown
tts preview "## Titre\n\nTexte avec **gras**."

# Lister les voix
tts voices
```

## Options de la commande `say`

| Option | Defaut | Description |
|--------|--------|-------------|
| `--voice`, `-v` | `ff_siwis` | Voix Kokoro |
| `--lang`, `-l` | `fr-fr` | Langue (fr-fr, en-us, en-gb) |
| `--output`, `-o` | (none) | Fichier de sortie WAV |
| `--speed`, `-s` | `0.95` | Vitesse (0.5-2.0) |
| `--pause-sentence` | `0.28` | Pause apres phrase (secondes) |
| `--pause-paragraph` | `0.55` | Pause apres paragraphe (secondes) |
| `--raw`, `-r` | `false` | Desactiver le preprocessing markdown |

## Voix disponibles

| Prefixe | Langue | Voix |
|---------|--------|------|
| `ff_` | Francais | `ff_siwis` (defaut) |
| `af_` | Anglais US (F) | `af_heart`, `af_bella`, `af_nova`, `af_sky` |
| `am_` | Anglais US (M) | `am_adam`, `am_echo`, `am_michael` |
| `bf_` | Anglais GB (F) | `bf_alice`, `bf_emma` |
| `bm_` | Anglais GB (M) | `bm_daniel`, `bm_george` |

## Python API

```python
from tts_engine.engine import TTSEngine, PauseConfig

engine = TTSEngine()

# Generer en memoire
result = engine.generate("Bonjour.", voice="ff_siwis", lang="fr-fr")
print(f"Duree: {result.duration:.1f}s, RTF: {result.rtf:.2f}x")

# Sauver dans un fichier
path, result = engine.save("Texte.", "output.wav")

# Controle fin des pauses
pause = PauseConfig(after_sentence=0.4, after_paragraph=0.8, speed=0.9)
result = engine.generate("Texte long avec plusieurs phrases.", pause=pause)
```

## Integration avec autres outils

```bash
# Voix-off pour video
tts say "Texte de la scene." -o video/audio/scene.wav

# Article markdown vers audio
cat article.md | tts say -o article.wav

# Notification vocale
tts say "Le deploiement est termine."
```
