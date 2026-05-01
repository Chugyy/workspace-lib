"""Markdown-to-speech preprocessor.

Transforms markdown content into clean, speakable text:
- Strips mermaid/code blocks entirely
- Converts tables to natural sentences
- Removes markdown syntax (**, *, ##, etc.)
- Removes emojis, URLs, style artifacts
- Applies pronunciation dictionary for acronyms and technical terms
- Normalizes whitespace and pauses
"""
import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Pronunciation dictionary
# ---------------------------------------------------------------------------
# Loaded from assets/pronunciation.json if it exists, merged with built-in
# defaults. Format: { "term": "spoken form" }
# Case-insensitive matching. Longer terms matched first to avoid partial hits.
# ---------------------------------------------------------------------------

_BUILTIN_PRONUNCIATIONS: dict[str, str] = {
    # --- Tech acronyms ---
    "SaaS": "sass",
    "API": "A-P-I",
    "APIs": "A-P-I",
    "REST": "resste",
    "IoT": "aille-au-ti",
    "MCP": "M-C-P",
    "MRR": "M-R-R",
    "ARR": "A-R-R",
    "UI": "U-I",
    "UX": "U-X",
    "IA": "I-A",
    "AI": "A-I",
    "LLM": "L-L-M",
    "LLMs": "L-L-M",
    "GPU": "G-P-U",
    "CPU": "C-P-U",
    "CI/CD": "C-I C-D",
    "DNS": "D-N-S",
    "SQL": "S-Q-L",
    "CSS": "C-S-S",
    "HTML": "H-T-M-L",
    "JSON": "jayzone",
    "YAML": "yaml",
    "CLI": "C-L-I",
    "SDK": "S-D-K",
    "VPS": "V-P-S",
    "SSH": "S-S-H",
    "TTS": "T-T-S",
    "CRUD": "crude",
    "ONNX": "onixe",
    "RTF": "R-T-F",
    "MVP": "M-V-P",
    "POC": "P-O-C",
    "CRM": "C-R-M",
    "ERP": "E-R-P",
    "B2B": "bi-tou-bi",
    "B2C": "bi-tou-ci",
    "KPI": "K-P-I",
    "ROI": "R-O-I",
    "CAC": "C-A-C",
    "LTV": "L-T-V",
    "SEO": "S-E-O",
    "CTO": "C-T-O",
    "CEO": "C-E-O",
    "CFO": "C-F-O",
    "RGPD": "R-G-P-D",
    "GDPR": "G-D-P-R",
    "OAuth": "o-auss",
    "JWT": "jotte",
    "URL": "U-R-L",
    "URLs": "U-R-L",
    "SMTP": "S-M-T-P",
    "HTTP": "H-T-T-P",
    "HTTPS": "H-T-T-P-S",
    "CORS": "corsse",
    "NPM": "N-P-M",
    "ORM": "O-R-M",
    "PDF": "P-D-F",
    "CSV": "C-S-V",
    "ETL": "E-T-L",
    "NLP": "N-L-P",
    "RAG": "ragge",
    "PR": "P-R",
    "CI": "C-I",
    "CD": "C-D",
    "QA": "Q-A",
    "DX": "D-X",

    # --- Anglicismes tech (écrits en phonétique française) ---
    # Le TTS tourne en mode FR, donc les mots anglais doivent être
    # écrits comme un français les prononcerait.
    "API-first": "A-P-I feurste",
    "first": "feurste",
    "onboarding": "onne-bordingue",
    "copywriting": "copi-raïtingue",
    "scraping": "scrépingue",
    "scraper": "scrépeur",
    "scrapers": "scrépeurs",
    "streaming": "strimingue",
    "marketing": "marketingue",
    "pitch": "pitche",
    "feedback": "fide-bak",
    "workflow": "weurk-flo",
    "framework": "fréme-weurk",
    "open source": "opène-source",
    "open-source": "opène-source",
    "machine-readable": "machinn ridable",
    "machine readable": "machinn ridable",
    "benchmark": "bennch-mark",
    "benchmarks": "bennch-marks",
    "dashboard": "dache-bord",
    "template": "temm-plaite",
    "templates": "temm-plaites",
    "plugin": "plogue-inne",
    "plugins": "plogue-inns",
    "marketplace": "markète-plaice",
    "startup": "star-teup",
    "start-up": "star-teup",
    "startups": "star-teups",
    "bootstrap": "boute-strap",
    "freelance": "fri-lance",
    "freelances": "fri-lances",
    "freelancer": "fri-lanceur",
    "crowdfunding": "kraoud-feundingue",
    "business": "biznèss",
    "branding": "bran-dingue",
    "design": "dizaïne",
    "designer": "dizaïneur",
    "feature": "fitcheur",
    "features": "fitcheurs",
    "release": "rilice",
    "deploy": "diplo-ï",
    "deployment": "diploi-mente",
    "refactoring": "ri-factoring",
    "debugging": "di-beu-guingue",
    "testing": "tèstingue",
    "hosting": "ho-stingue",
    "cloud": "klaoud",
    "container": "conntènneur",
    "containers": "conntènneurs",
    "serverless": "serveur-lèss",
    "backend": "bak-ènde",
    "frontend": "fronte-ènde",
    "full-stack": "foule-stak",
    "fullstack": "foule-stak",
    "middleware": "midl-wèr",
    "endpoint": "ènde-poïnte",
    "endpoints": "ènde-poïntes",
    "webhook": "wèbe-houk",
    "webhooks": "wèbe-houks",
    "token": "tokène",
    "tokens": "tokènes",
    "pipeline": "païpe-laïne",
    "pipelines": "païpe-laïnes",
    "sprint": "sprinte",
    "sprints": "sprintes",
    "blocker": "blokeur",
    "blockers": "blokeurs",
    "trade-off": "tréde-off",
    "trade-offs": "tréde-offs",
    "tradeoff": "tréde-off",
    "bottleneck": "botl-nèk",
    "scalable": "skélable",
    "scalability": "skélabiliti",
    "maintainability": "mènntènabiliti",
    "wrapper": "rapeur",
    "wrappers": "rapeurs",
    "boilerplate": "boïleur-plaite",
    "codebase": "code-béïsse",
    "runtime": "reune-taïme",
    "monorepo": "mono-répo",
    "microservice": "micro-service",
    "microservices": "micro-services",
    "legacy": "lèga-ci",
    "quick win": "kouik winn",
    "quick wins": "kouik winnz",
    "painpoint": "péïne-poïnte",
    "pain point": "péïne-poïnte",
    "growth": "grosse",
    "hacking": "hakingue",
    "growth hacking": "grosse hakingue",
    "lead": "lide",
    "leads": "lides",
    "churn": "tcheurne",
    "upsell": "eup-sèl",
    "cross-sell": "crosse-sèl",
    "pricing": "praïcingue",
    "freemium": "fri-miom",
    "paywall": "pé-wol",
    "lock-in": "lok-inn",
    "vendor lock-in": "vènndor lok-inn",
    "moat": "mote",
    "early adopter": "eurli a-dopteur",
    "early adopters": "eurli a-dopteurs",
    "game changer": "guéme tchéïnjeur",
    "deep tech": "dip tèk",
    "low-code": "lo-code",
    "no-code": "no-code",

    # --- Mots français mal prononcés par espeak-ng ---
    # th → t (espeak prononce le th à l'anglaise)
    "math": "matte",
    "maths": "mattes",
    "algorithme": "algoritmme",
    "algorithmes": "algoritmmes",
    "algorithmique": "algoritmique",
    "arithmétique": "aritmétique",
    "logarithme": "logaritmme",
    "logarithmes": "logaritmmes",
    "logarithmique": "logaritmique",
    "rythme": "ritmme",
    "rythmes": "ritmmes",
    "rythmique": "ritmique",

    # œ / ligatures scientifiques
    "stœchiométrie": "steuquiométrie",
    "stœchiométrique": "steuquiométrique",
    "stœchiométriques": "steuquiométriques",
    "fœtus": "fétuss",
    "œdème": "édème",
    "œdèmes": "édèmes",
    "œsophage": "ézofage",

    # Noms de scientifiques (prononciation française usuelle)
    "Euler": "Hoyleur",

    "Leibniz": "Laïbnitz",
    "Schrödinger": "Chreudinguère",
    "Heisenberg": "Aïzennbèrg",
    "Bernoulli": "Bèrnoulli",
    "Fibonacci": "Fibonatchchi",

    # Mots italiens courants
    "Pinocchio": "Pinokio",
    "cappuccino": "kapoutchino",
    "mozzarella": "motzaréla",
    "paparazzi": "paparatzi",
    "graffiti": "grafiti",
    "gnocchi": "nioki",
    "bruschetta": "brouskéta",
    "a priori": "a priori",
    "a posteriori": "a postériori",

    # Clusters exotiques
    "yacht": "yote",
    "fjord": "fyorde",
    "kitsch": "kitche",

    # --- French spoken forms ---
    "etc.": "et cétéra",
    "e.g.": "par exemple",
    "i.e.": "c'est-à-dire",
    "vs": "versus",
    "vs.": "versus",
    "nb": "nota bénné",
    "NB": "nota bénné",
}


def _load_pronunciation_dict() -> dict[str, str]:
    """Load and merge pronunciation dictionaries.

    Priority: assets/pronunciation.json overrides built-in defaults.
    """
    merged = dict(_BUILTIN_PRONUNCIATIONS)

    # Load custom dict from assets/ if it exists
    custom_path = Path(__file__).parent.parent.parent / "assets" / "pronunciation.json"
    if custom_path.exists():
        try:
            custom = json.loads(custom_path.read_text(encoding="utf-8"))
            merged.update(custom)
        except (json.JSONDecodeError, OSError):
            pass

    return merged


def _apply_pronunciations(text: str, pdict: dict[str, str]) -> str:
    """Replace terms with their spoken equivalents.

    Matches whole words only (word boundaries), case-sensitive by default.
    Case-insensitive only for terms that are ALL CAPS or contain mixed case
    that wouldn't collide with normal French words.
    Processes longer terms first to avoid partial matches.
    """
    # Sort by length descending so "API-first" matches before "API"
    sorted_terms = sorted(pdict.keys(), key=len, reverse=True)

    for term in sorted_terms:
        spoken = pdict[term]
        # Use word boundaries to avoid matching inside words
        # Case-sensitive matching to prevent "AI" matching in "faire", "UI" in "qui", etc.
        escaped = re.escape(term)
        pattern = re.compile(r'\b' + escaped + r'\b')
        text = pattern.sub(spoken, text)

    return text


def preprocess_for_speech(text: str, custom_pronunciations: dict[str, str] | None = None) -> str:
    """Clean markdown text for TTS consumption.

    Args:
        text: Raw markdown text.
        custom_pronunciations: Optional extra pronunciation overrides
                               (merged on top of built-in + assets/pronunciation.json).
    """
    # Load pronunciation dictionary
    pdict = _load_pronunciation_dict()
    if custom_pronunciations:
        pdict.update(custom_pronunciations)

    # 1. Remove mermaid blocks entirely (```mermaid ... ```)
    text = re.sub(r'```mermaid\s*\n.*?```', '', text, flags=re.DOTALL)

    # 2. Remove all other code blocks (```...```)
    text = re.sub(r'```\w*\s*\n.*?```', '', text, flags=re.DOTALL)

    # 3. Remove inline code (`...`)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 4. Convert markdown tables to natural text
    text = _convert_tables(text)

    # 5. Remove markdown headers syntax, keep text
    # "## Mon titre" → "Mon titre."
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1.', text, flags=re.MULTILINE)

    # 6. Remove bold/italic markers
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # ***bold italic***
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)       # **bold**
    text = re.sub(r'\*(.+?)\*', r'\1', text)            # *italic*
    text = re.sub(r'__(.+?)__', r'\1', text)            # __bold__
    text = re.sub(r'_(.+?)_', r'\1', text)              # _italic_

    # 7. Remove emojis (Unicode emoji ranges)
    text = re.sub(
        r'[\U0001F600-\U0001F64F'   # emoticons
        r'\U0001F300-\U0001F5FF'     # symbols & pictographs
        r'\U0001F680-\U0001F6FF'     # transport & map
        r'\U0001F1E0-\U0001F1FF'     # flags
        r'\U00002702-\U000027B0'     # dingbats
        r'\U0001F900-\U0001F9FF'     # supplemental symbols
        r'\U0001FA00-\U0001FA6F'     # chess symbols
        r'\U0001FA70-\U0001FAFF'     # symbols extended
        r'\U00002600-\U000026FF'     # misc symbols
        r'\U0000FE00-\U0000FE0F'     # variation selectors
        r'\U0000200D'                # zero width joiner
        r']+', '', text
    )

    # 8. Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # 9. Remove markdown links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 10. Remove markdown images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

    # 11. Remove horizontal rules (---, ***, ___)
    text = re.sub(r'^[\-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 12. Convert list markers to natural flow
    # "- Item" → "Item."
    # "1. Item" → "Item."
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 13. Remove arrows → ← ↔ and replace with spoken equivalents
    text = text.replace('→', ', ')
    text = text.replace('←', ', ')
    text = text.replace('↔', ', ')
    text = text.replace('—', ', ')

    # 14. Clean up multiple newlines → double newline (pause)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 15. Clean up multiple spaces
    text = re.sub(r' {2,}', ' ', text)

    # 16. Remove lines that are only whitespace
    text = re.sub(r'^\s+$', '', text, flags=re.MULTILINE)

    # 17. Final cleanup: collapse excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 18. Apply pronunciation dictionary (last step — works on clean text)
    text = _apply_pronunciations(text, pdict)

    return text.strip()


def _convert_tables(text: str) -> str:
    """Convert markdown tables to natural spoken text.

    | Header1 | Header2 |      →  "Header1 : Value1. Header2 : Value2."
    |---------|---------|
    | Value1  | Value2  |
    """
    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Detect table start: line with | separators
        if '|' in line and line.startswith('|') and line.endswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                table_lines.append(lines[i].strip())
                i += 1

            spoken = _table_to_speech(table_lines)
            if spoken:
                result.append(spoken)
        else:
            result.append(lines[i])
            i += 1

    return '\n'.join(result)


def _table_to_speech(table_lines: list[str]) -> str:
    """Convert parsed table lines to spoken text."""
    if len(table_lines) < 2:
        return ''

    # Parse headers
    headers = [cell.strip() for cell in table_lines[0].split('|') if cell.strip()]

    # Skip separator line (|---|---|)
    data_start = 1
    if data_start < len(table_lines) and re.match(r'^[\|\s\-:]+$', table_lines[data_start]):
        data_start = 2

    if data_start >= len(table_lines):
        return ''

    # Convert each row
    sentences = []
    for row_line in table_lines[data_start:]:
        cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
        if not cells:
            continue

        # Build natural sentence from row
        parts = []
        for h, c in zip(headers, cells):
            if c and c != '—' and c != '-':
                # Skip if cell is just a symbol (x, ?, -)
                if c in ('x', '?', '-', '✓', '✗'):
                    continue
                parts.append(f"{h} : {c}")

        if parts:
            sentences.append('. '.join(parts) + '.')

    return '\n'.join(sentences)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    print(preprocess_for_speech(text))
