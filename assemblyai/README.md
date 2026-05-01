# AssemblyAI — Research

## Setup

1. `cp .env.example .env`
2. Remplir `ASSEMBLYAI_API_KEY`
3. `pip install assemblyai`

## Credentials

| Variable | Ou la trouver |
|----------|---------------|
| `ASSEMBLYAI_API_KEY` | https://www.assemblyai.com/app/account → API Key |

## Resume

AssemblyAI fournit une API de transcription speech-to-text en temps reel via WebSocket (v3). Le SDK Python (`assemblyai`) abstrait la connexion WebSocket, l'envoi d'audio et la reception de transcripts avec un systeme d'events. Supporte le francais via le modele `universal-streaming-multilingual`, la diarization en streaming via `speaker_labels`, et offre une latence sub-300ms.

## Integration

- **SDK/Librairie** : `assemblyai` (PyPI), version 0.59.0+ — `pip install -U assemblyai`
- **Auth** : API key via header `Authorization: <API_KEY>` sur la connexion WebSocket
- **Base URL** : `wss://streaming.assemblyai.com/v3/ws`
- **Base URL EU** : `wss://streaming.eu.assemblyai.com/v3/ws`

## Real-Time Streaming API

### WebSocket Connection

- **URL** : `wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&speech_model=<model>`
- **Auth** : Header `Authorization: <API_KEY>` a l'ouverture du WebSocket
- **Audio format** : PCM signed 16-bit integer, mono, 16000 Hz
- **Frame size** : 800 frames par buffer (~50ms de chunks audio)
- **Transmission** : Binary WebSocket frames (pas base64, pas JSON pour l'audio)

### Modeles disponibles (streaming)

| Modele | `speech_model` value | Langues | Prix/h |
|--------|---------------------|---------|--------|
| Universal-3 Pro Streaming | `u3-rt-pro` | EN, ES, DE, FR, PT, IT (code-switching natif) | $0.45 |
| Universal-Streaming English | `universal-streaming-english` | EN uniquement | $0.15 |
| Universal-Streaming Multilingual | `universal-streaming-multilingual` | EN, ES, DE, FR, PT, IT (par tour) | $0.15 |
| Whisper Streaming | `whisper-rt` | 99+ langues (auto-detect) | $0.30 |

### Query Parameters

| Parametre | Type | Default | Description |
|-----------|------|---------|-------------|
| `speech_model` | string | **requis** | Modele a utiliser (voir tableau ci-dessus) |
| `sample_rate` | integer | 16000 | Frequence d'echantillonnage en Hz |
| `format_turns` | boolean | false | Active la ponctuation, capitalisation, ITN |
| `speaker_labels` | boolean | false | Active la diarization en streaming |
| `max_speakers` | integer | - | Nombre max de speakers (1-10), ameliore la precision |

### Sending Audio

Envoyer les chunks audio en **binary WebSocket frames** (PCM16 mono raw). Le SDK gere automatiquement le buffering et l'envoi. Pour un relay backend :

1. Recevoir l'audio du client (ex: via un autre WebSocket)
2. S'assurer que c'est en PCM16 mono 16kHz
3. Envoyer chaque chunk comme binary frame au WebSocket AssemblyAI

### Receiving Transcripts

Trois types d'events JSON :

#### BeginEvent (session ouverte)

```json
{
  "type": "Begin",
  "id": "<session_id>",
  "expires_at": "<timestamp>"
}
```

#### TurnEvent (transcript en cours / final)

```json
{
  "type": "Turn",
  "turn_order": 1,
  "transcript": "Bonjour comment allez-vous",
  "end_of_turn": false,
  "end_of_turn_confidence": 0.7,
  "turn_is_formatted": true,
  "audio_duration_seconds": 2.5,
  "speaker_label": "SPEAKER_A",
  "words": [
    {
      "text": "Bonjour",
      "word_is_final": true,
      "start": 0.0,
      "end": 0.5,
      "confidence": 0.95
    }
  ]
}
```

**Champs cles :**
- `end_of_turn` : `false` = partiel (le texte peut encore changer), `true` = turn finalise (immutable)
- `transcript` : accumule les mots finalises. Les mots precedents ne changent jamais (immutable transcriptions)
- `word_is_final` : toujours `true` sauf pour le dernier mot en cours
- `speaker_label` : present si `speaker_labels=true` (ex: `SPEAKER_A`, `SPEAKER_B`)

#### TerminationEvent (session fermee)

```json
{
  "type": "Termination",
  "audio_duration_seconds": 45,
  "session_duration_seconds": 60
}
```

### Turn Detection

| Parametre | Default | Description |
|-----------|---------|-------------|
| `min_turn_silence` | 100ms | Silence avant un check speculatif de fin de tour |
| `max_turn_silence` | 1000ms | Silence max avant de forcer la fin du tour |

Le modele cherche la ponctuation terminale (`.` `?` `!`) apres `min_turn_silence`. Si trouvee, emet le transcript final. Sinon, attend `max_turn_silence`.

### Mid-Stream Configuration

Modifier les parametres sans reconnecter :

```json
{
  "type": "UpdateConfiguration",
  "keyterms_prompt": ["AssemblyAI", "transcription"],
  "max_turn_silence": 1500,
  "min_turn_silence": 200,
  "prompt": "Transcribe French."
}
```

Forcer la fin d'un tour :

```json
{
  "type": "ForceEndpoint"
}
```

### Speaker Diarization

- **Activation** : `speaker_labels=true` dans les query params du WebSocket
- **Compatibilite** : fonctionne avec tous les modeles streaming (`u3-rt-pro`, `universal-streaming-english`, `universal-streaming-multilingual`)
- **Labels** : `SPEAKER_A`, `SPEAKER_B`, `SPEAKER_C`... assignes par ordre d'apparition
- **Max speakers** : 1-10 via `max_speakers` (optionnel, ameliore la precision)
- **Multichannel** : format `1A`, `1B`, `2A`, `2B` (chiffre = canal, lettre = speaker)

**Limites de la diarization streaming :**
- Les labels sont **permanents** : une fois assigne, un label ne change plus (pas de re-clustering retroactif)
- Instable en debut de conversation (peu de donnees vocales)
- Le chevauchement de parole (overlapping speech) est assigne a un seul speaker
- Les utterances courtes ("oui", "ok") manquent de donnees pour une identification fiable

### French Language Support

- **Modele recommande** : `universal-streaming-multilingual` ($0.15/h) ou `u3-rt-pro` ($0.45/h)
- **Detection automatique** : le modele detecte la langue par tour (pas besoin de specifier `language_code`)
- **Code-switching** : `u3-rt-pro` gere le melange de langues nativement dans un meme tour
- **Astuce prompt** : envoyer `"prompt": "Transcribe French."` via UpdateConfiguration pour forcer le francais
- **Alternative** : `whisper-rt` supporte le francais aussi ($0.30/h, 99+ langues)

## Limites & Couts

### Rate limits

| Tier | Nouvelles sessions/min | Concurrence |
|------|----------------------|-------------|
| Free | 5 | Limitee |
| Pay-as-you-go | 100 (par defaut) | Illimitee (auto-scaling) |

- **Auto-scaling** : a 70%+ d'utilisation, la limite augmente automatiquement de 10%
- **Erreur depassement** : WebSocket close code `1008` — "Unauthorized connection: Too many concurrent sessions"
- **Limites custom** : disponibles sur demande (gratuit)

### Couts

| Element | Prix |
|---------|------|
| Universal-Streaming (EN ou multilingual) | $0.15/h ($0.0025/min) |
| Universal-3 Pro Streaming | $0.45/h ($0.0075/min) |
| Whisper Streaming | $0.30/h ($0.005/min) |
| Speaker Diarization (add-on) | +$0.12/h |
| **Streaming multilingual + diarization** | **$0.27/h** |
| **Pro streaming + diarization** | **$0.57/h** |

**Facturation** : basee sur la duree totale de la session (pas seulement l'audio actif). La connexion WebSocket ouverte = facturation en cours.

### Error Handling

| Code | Signification |
|------|---------------|
| `1008` | API key invalide, solde insuffisant, ou trop de sessions concurrentes |
| WebSocket close | Verifier le close code et le message pour le diagnostic |

**Bonne pratique** : toujours envoyer un `terminate_session` (ou `client.disconnect(terminate=True)` via SDK) pour fermer proprement et arreter la facturation.

## Patterns recommandes

1. **Toujours specifier `speech_model`** — pas de defaut, le WebSocket echoue sans
2. **Utiliser `format_turns=True`** — ponctuation et capitalisation automatiques, pas de post-processing
3. **Fermer les sessions proprement** — `client.disconnect(terminate=True)` pour arreter la facturation
4. **Relay backend** : ouvrir un WebSocket client→backend et un backend→AssemblyAI. Relayer les binary frames audio. Relayer les TurnEvents JSON au client.
5. **PCM16 mono 16kHz** — convertir l'audio cote client ou backend avant envoi
6. **Speaker diarization** : activer uniquement si necessaire (+$0.12/h). Labels stables apres quelques secondes de voix par speaker.
7. **Forcer le francais** : utiliser `"prompt": "Transcribe French."` avec le modele multilingual pour eviter les faux positifs de detection de langue
8. **Reconnexion** : le SDK gere la reconnexion automatique. En WebSocket raw, implementer un backoff exponentiel.

## Exemples de code

### Streaming basique avec diarization (SDK Python)

```python
import assemblyai as aai
import os
from typing import Type
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)

api_key = os.getenv("ASSEMBLYAI_API_KEY")


def on_begin(self: Type[StreamingClient], event: BeginEvent):
    print(f"Session started: {event.id}")


def on_turn(self: Type[StreamingClient], event: TurnEvent):
    speaker = getattr(event, "speaker_label", "?")
    status = "FINAL" if event.end_of_turn else "partial"
    print(f"[{speaker}] ({status}) {event.transcript}")


def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
    print(f"Session ended: {event.audio_duration_seconds}s processed")


def on_error(self: Type[StreamingClient], error: StreamingError):
    print(f"Error: {error}")


def main():
    client = StreamingClient(
        StreamingClientOptions(
            api_key=api_key,
            api_host="streaming.assemblyai.com",
        )
    )

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    # Connexion avec diarization + multilingual (francais)
    client.connect(
        StreamingParameters(
            sample_rate=16000,
            speech_model="universal-streaming-multilingual",
            format_turns=True,
            speaker_labels=True,
            max_speakers=4,
        )
    )

    try:
        # Stream depuis le micro (dev/test uniquement)
        client.stream(aai.extras.MicrophoneStream(sample_rate=16000))
    finally:
        client.disconnect(terminate=True)


if __name__ == "__main__":
    main()
```

### Relay backend : client WebSocket → Python → AssemblyAI

```python
import asyncio
import json
import os
import websockets

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
ASSEMBLYAI_WS_URL = (
    "wss://streaming.assemblyai.com/v3/ws"
    "?sample_rate=16000"
    "&speech_model=universal-streaming-multilingual"
    "&format_turns=true"
    "&speaker_labels=true"
    "&max_speakers=4"
)


async def relay_audio(client_ws, path):
    """Relay audio from client WebSocket to AssemblyAI, transcripts back."""

    # Ouvrir connexion vers AssemblyAI
    aai_headers = {"Authorization": ASSEMBLYAI_API_KEY}
    async with websockets.connect(
        ASSEMBLYAI_WS_URL, extra_headers=aai_headers
    ) as aai_ws:

        async def forward_audio():
            """Client audio → AssemblyAI (binary frames)."""
            try:
                async for message in client_ws:
                    if isinstance(message, bytes):
                        # Relayer les chunks PCM16 mono 16kHz
                        await aai_ws.send(message)
            except websockets.ConnectionClosed:
                pass
            finally:
                # Fermer proprement la session AAI
                await aai_ws.close()

        async def forward_transcripts():
            """AssemblyAI transcripts → client (JSON)."""
            try:
                async for message in aai_ws:
                    data = json.loads(message)
                    event_type = data.get("type")

                    if event_type == "Begin":
                        await client_ws.send(json.dumps({
                            "type": "session_started",
                            "session_id": data["id"],
                        }))

                    elif event_type == "Turn":
                        await client_ws.send(json.dumps({
                            "type": "transcript",
                            "text": data.get("transcript", ""),
                            "is_final": data.get("end_of_turn", False),
                            "speaker": data.get("speaker_label", None),
                            "words": data.get("words", []),
                        }))

                    elif event_type == "Termination":
                        await client_ws.send(json.dumps({
                            "type": "session_ended",
                            "duration": data.get("audio_duration_seconds", 0),
                        }))

            except websockets.ConnectionClosed:
                pass

        # Lancer les deux taches en parallele
        await asyncio.gather(forward_audio(), forward_transcripts())


async def main():
    async with websockets.serve(relay_audio, "0.0.0.0", 8765):
        print("Relay server listening on ws://0.0.0.0:8765")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
```

## Variables d'environnement necessaires

| Variable | Description |
|----------|-------------|
| ASSEMBLYAI_API_KEY | Cle API AssemblyAI (depuis https://www.assemblyai.com/app/account) |

## Dependances Python

```
assemblyai>=0.59.0
websockets>=12.0      # si relay WebSocket raw
pyaudio>=0.2.14       # si capture micro (dev/test)
```
