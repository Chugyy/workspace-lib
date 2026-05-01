# Google Trends — Research

Google Trends = source de validation de demande d'un mot-cle dans le temps. Usage : verifier qu'une niche est stable/croissante avant d'y investir, detecter saisonnalite.

## 1. Realite 2025-2026 : pytrends est MORT

**`pytrends` a ete archive le 17 avril 2025** sans successeur officiel. Le repo GitHub original est en lecture seule. Les endpoints non documentes qu'il utilisait cassent regulierement. **Ne pas utiliser `pytrends` en 2026.**

## 2. Alternatives evaluees

| Solution | Type | Prix | Fiabilite | Recommandation |
|----------|------|------|-----------|----------------|
| **`pytrends-modern`** | Lib Python open source | Gratuit | Bonne | **Recommande** pour MVP |
| `trendspyg` | Lib Python open source | Gratuit | Bonne | Alternative acceptable |
| SerpApi Google Trends | API payante | ~50$/mois | Excellente | Si volume serieux |
| Glimpse | SaaS | Payant | Excellente | Produit fini, pas une API |
| Google Trends API officielle | API officielle | Quota | Limitee | Lancee en 2025, encore jeune |

## 3. `pytrends-modern` : la reference 2026

Library moderne qui combine les meilleures features de pytrends + trendspyg. Maintenue activement. Retry automatique, support async, RSS feeds pour trending en temps reel.

### Installation

```bash
pip install pytrends-modern
# Ou avec toutes les features (browser fallback, selenium, CLI)
pip install pytrends-modern[all]
```

### API principale

```python
from pytrends_modern import TrendReq

pytrends = TrendReq(
    hl="en-US",       # Langue interface
    tz=360,           # Timezone offset (minutes)
    retries=5,        # Retry auto sur rate limit
    backoff_factor=0.5,
)

pytrends.build_payload(
    kw_list=["italian food crossword", "medical terminology crossword"],
    timeframe="today 5-y",   # 5 ans
    geo="US",                # Pays
)

# Interet au cours du temps
df_interest = pytrends.interest_over_time()
# → DataFrame pandas : date, kw1, kw2, isPartial

# Requetes associees (gold mine pour decouvrir des niches)
related = pytrends.related_queries()
# → dict: {kw: {"top": df, "rising": df}}

# Sujets associes
topics = pytrends.related_topics()

# Distribution geographique
df_geo = pytrends.interest_by_region(resolution="COUNTRY")

# Suggestions d'amelioration de mot-cle
suggestions = pytrends.suggestions(keyword="crossword")
```

### Methodes cles pour le projet KDP

1. **`interest_over_time()`** — courbe sur 5 ans. Permet de detecter :
   - Tendance (haussiere, stable, baissiere)
   - Saisonnalite (ex : "Christmas crossword" pic en novembre-decembre)
   - Effets de mode vs demandes perennes

2. **`related_queries()`** — decouverte de mots-cles lies et en croissance rapide (`rising`). Complement de l'Amazon Suggest API.

3. **`interest_by_region()`** — aide a cibler les Marketplaces prioritaires.

## 4. Parametres importants

### `timeframe`
| Valeur | Signification |
|--------|--------------|
| `"all"` | Depuis 2004 |
| `"today 5-y"` | 5 dernieres annees **(recommande pour valider perenite)** |
| `"today 12-m"` | 12 derniers mois **(recommande pour tendance actuelle)** |
| `"today 3-m"` | 3 derniers mois |
| `"now 7-d"` | 7 derniers jours |

### `geo`
- `""` = mondial
- `"US"`, `"FR"`, `"GB"`, `"DE"`, `"IT"`, `"ES"`, `"CA"` = pays
- `"US-CA"` = sous-region (Californie)

### Limites techniques
- Maximum **5 mots-cles par requete** (`kw_list`)
- Pour comparer plus de 5 mots-cles, faire plusieurs `build_payload` en normalisant sur un mot-cle commun.

## 5. Rate limits et strategie

Google Trends n'expose pas de quota officiel mais **limite agressivement** :
- Burst de ~50 requetes puis blocage temporaire (15-60 min)
- En cas de blocage : HTTP 429 ou reponses vides

### Mitigations

1. **Retry auto + backoff** : `TrendReq(retries=5, backoff_factor=0.5)` → delai exponentiel entre essais.
2. **Gestion explicite** :
   ```python
   from pytrends_modern.exceptions import TooManyRequestsError
   try:
       df = pytrends.interest_over_time()
   except TooManyRequestsError:
       time.sleep(60)  # ou switch proxy
   ```
3. **Proxies** (si volume) :
   ```python
   pytrends = TrendReq(
       proxies=["https://proxy1:8080", "https://proxy2:8080"]
   )
   ```
4. **Delays entre requetes** : 3-5s minimum.
5. **Cache agressif** : une fois les donnees d'une niche recuperees, les cacher 7+ jours. Les tendances ne bougent pas vite.

## 6. Snippet Python complet pour le projet

```python
from pytrends_modern import TrendReq
import time

def get_trend_signal(keyword: str, geo: str = "US") -> dict:
    """
    Retourne un signal sur l'interet d'une niche :
    - moyenne 12 derniers mois
    - evolution sur 5 ans (ratio recent/ancien)
    - saisonnalite (score)
    - requetes en rising
    """
    pytrends = TrendReq(hl=f"en-US", tz=360, retries=5, backoff_factor=1.0)

    # 5 ans pour tendance
    pytrends.build_payload([keyword], timeframe="today 5-y", geo=geo)
    df_5y = pytrends.interest_over_time()
    time.sleep(3)

    if df_5y.empty:
        return {"status": "no_data"}

    values = df_5y[keyword].values
    recent_avg = values[-12:].mean()   # ~3 derniers mois
    old_avg = values[:12].mean()       # ~3 premiers mois
    trend_ratio = recent_avg / old_avg if old_avg > 0 else None

    # Saisonnalite : ecart-type / moyenne
    seasonality = values.std() / values.mean() if values.mean() > 0 else 0

    # Related queries
    pytrends.build_payload([keyword], timeframe="today 12-m", geo=geo)
    related = pytrends.related_queries()
    rising = related.get(keyword, {}).get("rising")
    rising_list = rising["query"].tolist() if rising is not None else []

    return {
        "status": "ok",
        "recent_avg": float(recent_avg),
        "trend_ratio": trend_ratio,   # >1 = en hausse, <1 = en baisse
        "seasonality": float(seasonality),
        "rising_queries": rising_list[:10],
    }
```

## 7. Pieges

1. **Normalisation Google Trends** : les valeurs sont toujours entre 0 et 100, **relatives a la plage de temps demandee**. `100` = pic dans cette fenetre, pas volume absolu.

2. **`isPartial`** : la derniere semaine/mois est souvent marquee partielle (`isPartial=True`). L'exclure des moyennes recentes.

3. **Volumes trop faibles** : Google Trends renvoie du vide si la requete n'a pas assez de volume. Solution : elargir la requete (`"crossword"` au lieu de `"italian food crossword"`).

4. **Difference entre mondial et `geo="US"`** : les courbes different. Toujours preciser `geo`.

5. **Browser fallback** (`pytrends-modern[all]`) : utilise Camoufox si les endpoints classiques echouent. Utile mais plus lent.

## 8. Usage dans le scoring

Integration dans le scorer du projet :

```python
score_trend = 0
if trend_data["status"] == "ok":
    if trend_data["trend_ratio"] is not None:
        if trend_data["trend_ratio"] > 1.1:
            score_trend += 15  # en hausse
        elif trend_data["trend_ratio"] > 0.9:
            score_trend += 10  # stable
        else:
            score_trend += 0   # en baisse
    if trend_data["recent_avg"] > 20:
        score_trend += 5  # volume minimum
```

## 9. Alternative minimaliste (si `pytrends-modern` casse)

Fallback manuel : scraper directement `trends.google.com` avec Playwright. Complexe, cher, mais fonctionne quand toutes les libs Python cassent. Voir `amazon-scraping.md` pour les techniques generiques.

## 10. Checklist d'implementation

- [ ] `pytrends-modern` installe
- [ ] Retry + backoff configures
- [ ] Gestion explicite `TooManyRequestsError`
- [ ] Cache disque (JSON, TTL 7 jours)
- [ ] Delays inter-requetes (3-5s)
- [ ] Export DataFrame en JSON pour persistance
- [ ] Scoring integre dans le niche scorer
