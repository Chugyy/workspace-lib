# Amazon Scraping — Research

Amazon n'expose pas d'API publique pour les donnees produit (BSR, avis, prix). Scraping necessaire, mais Amazon est **l'un des sites les plus agressifs** contre les scrapers. Cette fiche couvre : search results, product page, anti-bot.

## Setup

```bash
pip install patchright
patchright install chromium
```

## Credentials

Aucune credential requise. Le scraping se fait sans authentification Amazon.

## 1. Realite 2025-2026

- Amazon **rotue les selecteurs HTML** et sert du **markup different** selon user-agent, cookies, IP.
- **BSR (Best Seller Rank)** est cache dans des emplacements inconsistants selon categorie et marketplace.
- **Cloudflare + AWS WAF** + detection comportementale (mouse, scroll, timing) : les stealth plugins ne suffisent plus contre la detection avancee.
- Approche pragmatique : **volumes faibles, delays humains, rotation, tolerance aux echecs**.

## 2. Strategie recommandee (gratuite, robuste pour <100 req/jour)

### Stack : Patchright + Playwright Python

`patchright` = fork de `playwright` qui corrige les fuites de detection (navigator.webdriver, chrome.runtime, etc.) a la source. Plus efficace que `playwright-stealth` en 2025.

```bash
pip install patchright
patchright install chromium
```

```python
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="chrome")  # channel="chrome" = moins detectable
    context = browser.new_context(
        locale="en-US",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1440, "height": 900},
    )
    page = context.new_page()
    page.goto("https://www.amazon.com/s?k=crossword+puzzle+books", wait_until="domcontentloaded")
    # scraping logic
    browser.close()
```

### Bonnes pratiques indispensables

1. **headless=False quand possible** (ou `new-headless` mode Chrome). Le headless classique est facilement detecte.
2. **channel="chrome"** au lieu du Chromium bundle (moins de fingerprints "Playwright").
3. **Delays humains** : 5-15s entre pages, variabilite aleatoire (jitter).
4. **Mouse + scroll simules** avant extraction :
   ```python
   page.mouse.move(500, 300)
   page.mouse.wheel(0, 500)
   page.wait_for_timeout(random.randint(1500, 3500))
   ```
5. **User-agent coherent** avec la locale et la plateforme (ne pas mixer Win + Mac locale).
6. **Gestion cookies** : accepter le bandeau cookies, garder la session entre requetes.
7. **Proxies residentiels rotatifs** si volume > 100 req/jour. Sinon, inutile.

## 3. URLs cles

### Search results
```
https://www.amazon.com/s?k={url-encoded-query}&i=stripbooks&page={n}
```
- `i=stripbooks` : restreint aux livres (important pour KDP).
- `page={n}` : pagination (1 a N, 16 resultats par page typiquement).

### Product page
```
https://www.amazon.com/dp/{ASIN}
```
- ASIN = 10 caracteres alphanumeriques, unique par produit.

### Bestsellers par categorie
```
https://www.amazon.com/gp/bestsellers/books/{node-id}
```

## 4. Selecteurs (instables, a verifier avant chaque run)

> **AVERTISSEMENT** : les selecteurs Amazon changent. Ceux-ci sont indicatifs au 2026-04. Toujours verifier en ouvrant la page cible et en utilisant les devtools.

### Search results page
```python
# Container de chaque produit
results = page.query_selector_all('div[data-component-type="s-search-result"]')

for r in results:
    asin = r.get_attribute("data-asin")
    title = r.query_selector('h2 span').inner_text()
    price_whole = r.query_selector('span.a-price-whole')
    price = price_whole.inner_text() if price_whole else None
    rating_el = r.query_selector('span.a-icon-alt')
    rating = rating_el.inner_text() if rating_el else None  # "4.5 out of 5 stars"
    reviews_el = r.query_selector('span.a-size-base.s-underline-text')
    reviews = reviews_el.inner_text() if reviews_el else None  # "1,234"
    link = r.query_selector('h2 a').get_attribute("href")
```

### Product page
Les infos cruciales (BSR, date de publication) sont dans la section "Product information" / "Informations sur le produit".

```python
# BSR est dans une table OU dans un div, selon la categorie. Approche robuste :
page_text = page.content()

# Regex pour BSR (exemple US)
import re
bsr_match = re.search(r'Best Sellers Rank[:\s]*#([\d,]+)\s+in\s+([^(<]+)', page_text)
if bsr_match:
    rank = int(bsr_match.group(1).replace(",", ""))
    category = bsr_match.group(2).strip()

# Date de publication
pub_match = re.search(r'Publication date[:\s]*</span>\s*<span[^>]*>([^<]+)</span>', page_text)

# Nombre de pages
pages_match = re.search(r'Print length[:\s]*</span>\s*<span[^>]*>(\d+)\s+pages', page_text)

# Editeur / Publisher
publisher_match = re.search(r'Publisher[:\s]*</span>\s*<span[^>]*>([^<]+)</span>', page_text)
```

**Alternatives** :
- Regex sur HTML brut : robuste aux changements de DOM tant que les labels restent ("Best Sellers Rank", "Publication date").
- Parser le bloc `<div id="detailBullets_feature_div">` ou `<table id="productDetails_detailBullets_sections1">` (varie).

## 5. Detection et contournement

### Signaux de detection
- **Captcha page** : URL redirigee vers `/errors/validateCaptcha`. Detecter : `page.url.includes("validateCaptcha")` ou presence du formulaire captcha.
- **Blocage IP** : HTTP 503 + page "Sorry, we just need to make sure you're not a robot".
- **Dog page** : `/errors/validateCaptcha` (Amazon affiche un chien).
- **Ralentissement** : timeouts repetes.

### Reactions
- Sur captcha : **arreter la session**, attendre 15-30 minutes, changer d'IP si possible, reprendre.
- Sur 503 : backoff exponentiel (30s, 60s, 120s...).
- Limite quotidienne prudente : **50-80 requetes/jour** par IP residentielle.

### Escalade (payant, pour plus tard)
Si le volume augmente :
- **Bright Data** (Residential proxies) — ~8$/GB.
- **ScrapingBee / ScraperAPI / ZenRows** — wrappers API qui gerent tout. ~30-50$/mois.
- **Apify Amazon Scraper** — pret a l'emploi, ~$0.25 par 1000 produits.

Pour un MVP visant la validation de 5-10 niches (~100 requetes totales), **pas besoin de payer**.

## 6. Cache et deduplication

**Imperativement** cacher chaque page scrappee sur disque (HTML brut + JSON extrait) pendant au moins 24h. Raisons :
- Reprise en cas d'echec sans re-scraper.
- Debug possible a froid.
- Reduction drastique des requetes pendant le developpement.

Structure suggeree :
```
cache/
├── search/{query-hash}-{page}.html
├── product/{asin}.html
└── extracted/
    ├── search/{query-hash}.json
    └── product/{asin}.json
```

## 7. Gestion d'erreurs

| Erreur | Reaction |
|--------|----------|
| Timeout reseau | Retry 3x avec backoff (10s, 30s, 60s) |
| HTTP 503 | Backoff long (5min), puis retry |
| Captcha detecte | Stop session, attente 30min |
| Selecteur absent | Log + skip ce produit, continuer |
| Page blanche | Retry 1x, sinon skip |

## 8. Alternative : Amazon Product Advertising API (PA-API)

Officielle, propre, JSON, mais **necessite un compte Amazon Associates avec ventes recentes** (au moins 3 ventes qualifiees dans les 180 jours). Inaccessible pour demarrer.

Documentation : https://webservices.amazon.com/paapi5/documentation/

A envisager uniquement une fois que le business vend deja (on s'inscrit comme affilie, on fait 3 ventes, on a acces a l'API officielle).

## 9. Limites legales

Scraping Amazon **viole les CGU**. Risques :
- Bannissement IP
- Bannissement compte Amazon si connecte
- Potentielles lettres legales pour usage commercial a grande echelle

Pour un usage de **recherche de niche personnel et a faible volume**, le risque est tres faible. Ne jamais scraper avec un compte Amazon connecte. Ne jamais revendre les donnees scrappees.

## 10. Checklist d'implementation

- [ ] Patchright installe et configure
- [ ] User-agent + locale + viewport realistes
- [ ] Delays humains (5-15s) entre pages
- [ ] Mouse + scroll simules
- [ ] Cache HTML sur disque (TTL 24h)
- [ ] Detection captcha + arret propre
- [ ] Retry avec backoff exponentiel
- [ ] Logs structures (JSON)
- [ ] Limite quotidienne (50-80 req) configurable
- [ ] Selecteurs externalises (YAML ou JSON) pour adapter sans recompiler
