#!/usr/bin/env python3
"""Rappel réunion HA Immo — Philippe Toquard"""
import sys, json
sys.path.insert(0, '/data/workspace/lib/telegram/src')
from telegram_notifier.client import TelegramClient

cfg = json.load(open('/data/workspace/lib/telegram/assets/config.json'))
client = TelegramClient(cfg['bot_token'], cfg['chat_id'])

message = """📅 *Réunion HA Immo dans 20 min — Philippe Toquard*

*Ce que tu as fait (à lui montrer)*
• Pipeline données : 24 communes La Réunion ✅
• Site Next.js : pages, formulaire, admin/CRM ✅

*Points à valider avec lui*
1. Il a vu/validé le PRD ? Les 5 livrables sont OK ?
2. Sa priorité : formulaire live d'abord ou articles SEO aussi ?
3. Il a des mandataires à gérer dans le CRM ou juste lui ?

*Ce qu'on a besoin de lui*
• Photo + bio (page à propos)
• Email pour recevoir les notifications leads
• Logo en HD
• Spécificités locales des 5 communes principales

*Questions commerciales*
• Confirmer ce qui est convenu (tarif / jalons)
• Date souhaitée de mise en ligne

*Objectif*
Aligner sa vision avec ce qui est buildé → définir les priorités → date de déploiement"""

result = client.send_message(message, parse_mode='Markdown')
print('OK' if result.get('ok') else 'ERREUR', result)
