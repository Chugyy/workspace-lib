# TTS

Text-to-speech local via MLX Audio avec streaming progressif. Voix française clonée prête à l'emploi (Parisienne) + support Kokoro/Qwen3.

## Setup

```bash
cd ../../lib/tts && ./setup.sh
```

Pas de credentials nécessaires (modèles locaux).

## Usage

```bash
cd ../../lib/tts && source .venv/bin/activate

# Voix française clonée par défaut (Parisienne)
tts say "Bonjour. Voici un message en français."

# Sauver dans un fichier
tts say "Texte à narrer." -o narration.wav

# TTS classique (Kokoro/Qwen3 sans cloning)
tts speak "Hello world" --model kokoro --voice af_heart --lang en

# Streaming chunks vers fichiers
tts stream-to-file "Texte multi-phrases." -d ./chunks/

# Lister les voix / modèles
tts voices --model kokoro
tts models
```

## Voix françaises clonées

| Voix | Description |
|------|-------------|
| `parisienne` | Femme, accent parisien chaleureux et naturel (défaut) |

## Modèles disponibles

| Key | Modèle | Streaming | Pour |
|-----|--------|-----------|------|
| `kokoro` | Kokoro 82M | Phrase | EN rapide |
| `qwen3-base-q4` | Qwen3-TTS 0.6B 4-bit | Token | Voice cloning |
| `qwen3-design` | Qwen3-TTS 1.7B VoiceDesign 8-bit | Token | Créer une nouvelle voix |
| `qwen3-base` | Qwen3-TTS 0.6B bf16 | Token | Voice cloning haute qualité |

## Important pour le français

Toujours écrire les vrais accents : é, è, ê, à, â, ù, û, ô, î, ï, ç. Le modèle lit phonétiquement.
