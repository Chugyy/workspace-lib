# Amazon Suggest API — Research

API publique d'autocompletion d'Amazon. Aucune authentification, aucune quota documentee. Usage : decouvrir les mots-cles longue traine que les acheteurs tapent reellement.

## Setup

```bash
pip install httpx
```

## Credentials

Aucune credential requise. L'API d'autocompletion Amazon est publique.

## 1. Endpoint

```
GET https://completion.amazon.com/api/2017/suggestions
```

Pas d'auth. Retourne du JSON. Un endpoint alternatif existe (`/search/complete`) mais celui-ci est plus propre.

## 2. Parametres

### Requis
| Param | Description | Exemple |
|-------|-------------|---------|
| `mid` | Marketplace ID (voir table ci-dessous) | `ATVPDKIKX0DER` |
| `alias` | Categorie de recherche | `aps` (all departments) |
| `prefix` | Requete (URL-encoded, espaces = `+`) | `crossword+puzzle` |

### Optionnels utiles
| Param | Description | Defaut |
|-------|-------------|--------|
| `limit` | Nombre max de suggestions | 11 |
| `lop` | Locale (language/locale) | `en_US`, `fr_FR`, `en_GB`, `de_DE` |
| `suggestion-type` | Type de resultat | `KEYWORD` |
| `site-variant` | Type de device | `desktop` |
| `page-type` | Contexte de page | `Gateway` |

## 3. Marketplace IDs

| Pays | mid | lop |
|------|-----|-----|
| **US** (amazon.com) | `ATVPDKIKX0DER` | `en_US` |
| **UK** (amazon.co.uk) | `A1F83G8C2ARO7P` | `en_GB` |
| **France** (amazon.fr) | `A13V1IB3VIYZZH` | `fr_FR` |
| **Allemagne** (amazon.de) | `A1PA6795UKMFR9` | `de_DE` |
| **Italie** (amazon.it) | `APJ6JRA9NG5V4` | `it_IT` |
| **Espagne** (amazon.es) | `A1RKKUPIHCS9HS` | `es_ES` |
| **Canada** (amazon.ca) | `A2EUQ1WTGCTBG2` | `en_CA` |
| **Japon** (amazon.co.jp) | `A1VC38T7YXB528` | `ja_JP` |

Les suggestions retournees dependent du `mid` (le marche influence les resultats) ET du domaine appele. Pour la France, appeler `completion.amazon.fr` avec `mid=A13V1IB3VIYZZH`.

## 4. Format de reponse (verifie en live)

Requete test :
```
GET https://completion.amazon.com/api/2017/suggestions?mid=ATVPDKIKX0DER&alias=aps&prefix=crossword
```

Reponse :
```json
{
  "alias": "aps",
  "prefix": "crossword",
  "suffix": "",
  "suggestions": [
    {
      "suggType": "KeywordSuggestion",
      "type": "KEYWORD",
      "value": "crossword puzzle books for adults",
      "refTag": "nb_sb_ss_i_1_9",
      "candidateSources": "local",
      "strategyId": "organic",
      "prior": 0.0,
      "ghost": false,
      "help": false,
      "queryUnderstandingFeatures": [...]
    },
    { "value": "crossword puzzle books", ... },
    { "value": "crossword puzzle books for seniors", ... },
    { "value": "crossword puzzles", ... },
    { "value": "easy crossword puzzle books for adults", ... }
  ],
  "predictiveText": null,
  "responseId": "W9S0ZVF0CQ2B",
  "shuffled": false
}
```

**Champ clef** : `suggestions[].value` → chaine de la suggestion.

**Si aucune suggestion** : `suggestions: []`. Cela arrive quand le prefix est trop specifique (ex: `italian food crossword` retourne vide car trop niche). Strategie : partir de seeds courts (1-2 mots) et descendre progressivement.

## 5. Pieges et gotchas

1. **Prefix trop specifique = vide** : `crossword` donne 11 resultats, `italian food crossword` donne 0. Strategie a arbres : commencer par une racine courte, explorer les suggestions, puis re-suggerer a partir de chaque branche.

2. **URL-encoding** : les espaces doivent etre `+` ou `%20`. Les accents (`%C3%A9` pour `e`) doivent etre encodes.

3. **Pas de rate limit officiel** mais rester poli. Observation : aucun blocage constate avec ~1 req/s depuis IP residentielle.

4. **Resultats localises** : `mid=ATVPDKIKX0DER` + `prefix=livre` donne des resultats US (peu utiles en francais). Pour FR, utiliser `mid=A13V1IB3VIYZZH` ET idealement le domaine `completion.amazon.fr`.

5. **`ghost: true`** : suggestions "fantomes" qui ne viennent pas des requetes reelles. Peut etre filtre si on veut uniquement du signal utilisateur authentique.

6. **`strategyId`** : `organic` = suggestions basees sur l'historique de recherche reel. Les autres valeurs (sponsored, fallback) sont moins fiables pour la recherche de niche.

## 6. Strategie d'exploration (tree crawl)

Pour decouvrir les niches profondes, arbre de suggestions :

```
seed = "crossword"
niveau 1 = suggest(seed) → ["crossword puzzle books for adults", ...]
niveau 2 = pour chaque res de niveau 1, suggest(res) → plus fin
niveau 3 = idem
```

A chaque niveau on deduplique, on filtre (longueur min/max, mots interdits), on cumule. Objectif : obtenir 50-200 mots-cles longues traines en ~20-50 requetes.

## 7. Snippet Python minimal

```python
import httpx
import urllib.parse

def amazon_suggest(prefix: str, mid: str = "ATVPDKIKX0DER", alias: str = "aps") -> list[str]:
    params = {
        "mid": mid,
        "alias": alias,
        "prefix": prefix,
        "limit": 11,
    }
    url = "https://completion.amazon.com/api/2017/suggestions"
    resp = httpx.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [s["value"] for s in data.get("suggestions", []) if not s.get("ghost")]

# Exemple
suggestions = amazon_suggest("crossword")
# → ["crossword puzzle books for adults", "crossword puzzle books", ...]
```

## 8. Limites

- Ne donne **pas** de volume de recherche absolu (juste un classement ordonne : 1er = plus populaire).
- Ne donne **pas** d'info concurrence ou bestsellers.
- Sert uniquement a **decouvrir** les requetes populaires, pas a les qualifier.

L'etape de qualification passe par le scraping des resultats Amazon (voir `amazon-scraping.md`).
