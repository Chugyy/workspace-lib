---
name: tts-engine
description: Local text-to-speech with streaming via MLX Audio (Apple Silicon). Voix française clonée prête à l'emploi (Parisienne) + support Kokoro/Qwen3 pour autres voix. Streaming progressif chunk par chunk. Use for voiceovers, narration, notifications, or any text-to-audio need.
---

# TTS Engine

Text-to-speech local avec streaming progressif via MLX Audio.

## Setup

```bash
cd ../../lib/tts && ./setup.sh
```

## Usage rapide (français)

```bash
source ../../lib/tts/.venv/bin/activate

# Voix française clonée par défaut (Parisienne)
tts say "Bonjour. Voici un message en français avec une voix naturelle."

# Sauver dans un fichier
tts say "Texte à narrer." -o narration.wav
```

## ⚠️ IMPORTANT pour le français

**Toujours écrire les vrais accents** : é, è, ê, à, â, ù, û, ô, î, ï, ç.

Le modèle lit phonétiquement. `degres` sera prononcé "degress" (sans accent), `degrés` sera correct.

## Contrôler l'émotion

Pas de paramètre d'émotion -- on contrôle via le **texte lui-même** :

| Effet voulu | Comment l'écrire |
|-------------|-------------------|
| Neutre/posé | Phrases longues, points seulement, pas de "salut" |
| Joyeux | `!`, "Oh !", "Génial !", phrases courtes |
| Calme/méditatif | Phrases lentes, "...", pauses |
| Sérieux | Vocabulaire formel, structure professionnelle |
| Triste | "...", "C'est dur", phrases hésitantes |

## Commandes

```bash
# Voix française clonée (défaut: parisienne)
tts say "Texte ici"
tts say "Texte" -v parisienne -o output.wav

# Cloner une nouvelle voix depuis un audio de référence (3s+)
tts clone "Nouveau texte" \
  --ref-audio voice_sample.wav \
  --ref-text "Texte exact prononcé dans le sample"

# TTS classique (Kokoro/Qwen3 sans cloning)
tts speak "Hello world" --model kokoro --voice af_heart --lang en
tts generate "Save this." -o speech.wav --model kokoro

# Streaming chunks vers fichiers (pour Remotion etc.)
tts stream-to-file "Texte multi-phrases." -d ./chunks/

# Listes
tts voices --model kokoro
tts models
```

## Voix françaises clonées disponibles

| Voix | Description |
|------|-------------|
| `parisienne` | Femme, accent parisien chaleureux et naturel (défaut) |

Pour ajouter une nouvelle voix clonée :
1. Mettre le WAV de référence dans `assets/voices/{nom}.wav`
2. Créer `assets/voices/{nom}.json` avec `audio`, `ref_text`, `language`, `model`
3. Ajouter `"{nom}": "{nom}"` dans `TTSEngine.CLONED_VOICES` (engine.py)

## Modèles disponibles

| Key | Modèle | Streaming | Pour |
|-----|--------|-----------|------|
| `kokoro` (défaut) | Kokoro 82M | Phrase | EN rapide |
| `qwen3-base-q4` | Qwen3-TTS 0.6B 4-bit | Token | Voice cloning (utilisé par `say`/`clone`) |
| `qwen3-design` | Qwen3-TTS 1.7B VoiceDesign 8-bit | Token | Créer une nouvelle voix depuis description |
| `qwen3-base` | Qwen3-TTS 0.6B bf16 | Token | Voice cloning haute qualité |

## Python API

```python
from tts_engine.engine import TTSEngine
from tts_engine.player import StreamPlayer

# Voix française clonée
engine, ref_audio, ref_text = TTSEngine.from_cloned_voice("parisienne")
engine.save("Texte à narrer.", "output.wav", lang="fr",
            ref_audio=ref_audio, ref_text=ref_text)

# Streaming temps réel
with StreamPlayer() as player:
    for chunk in engine.stream("Long texte ici.", lang="fr",
                                ref_audio=ref_audio, ref_text=ref_text):
        player.queue(chunk.audio)

# Cloner une voix custom
engine = TTSEngine("qwen3-base-q4")
engine.save(
    "Nouveau texte",
    "out.wav",
    lang="fr",
    ref_audio="path/to/reference.wav",
    ref_text="Texte exact du sample",
)

# Créer une nouvelle voix avec VoiceDesign (puis la sauver pour cloning)
from mlx_audio.tts.utils import load_model
model = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit")
for result in model.generate(
    text="Bonjour, voici ma nouvelle voix.",
    instruct="A French woman with a calm, warm voice and Parisian accent",
    language="French",
):
    # Sauver result.audio pour réutiliser comme ref_audio plus tard
    pass
```

## Workflow : créer une nouvelle voix française stable

```python
# 1. Génère une voix avec VoiceDesign jusqu'à en trouver une qui plaît
from mlx_audio.tts.utils import load_model
import numpy as np
from mlx_audio.audio_io import write

vd = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit")
ref_text = "Bonjour, je suis votre assistant vocal."  # phrase de référence
chunks = []
for r in vd.generate(text=ref_text, instruct="A French male voice, warm and calm, 30s, Parisian accent", language="French"):
    chunks.append(np.array(r.audio.tolist(), dtype=np.float32))
    sr = r.sample_rate
write("../../lib/tts/assets/voices/thomas.wav", np.concatenate(chunks), sr, format="wav")

# 2. Crée le JSON metadata, ajoute dans CLOWNED_VOICES, et c'est utilisable via tts say -v thomas
```

## Intégration avec autres outils

```bash
# Voix-off pour vidéo Remotion (chunks séparés par phrase)
tts say "Texte de la scène." -o video/audio/scene.wav

# Article → audio
cat article.txt | tts say -o article.wav

# Notification vocale
tts say "Le déploiement est terminé."
```
