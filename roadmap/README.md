# Roadmap CLI

Gerer les roadmaps du AI Manager depuis la ligne de commande : lister, creer, modifier, suivre les taches et dependances.

## Setup

1. `./setup.sh`
2. `profile add roadmap dev` (configure l'URL backend et la cle interne)

## Credentials

| Variable | Description |
|----------|-------------|
| `BACKEND_URL` | URL du backend AI Manager (ex: `http://127.0.0.1:4810` pour stable, `http://127.0.0.1:4812` pour dev) |
| `INTERNAL_KEY` | Cle interne du backend (header `X-Internal-Key`, default: `proxy-internal-key`) |

### Profils recommandes

Creer un profil par instance AI Manager :

```bash
profile add roadmap stable    # → backend_url=http://127.0.0.1:4810
profile add roadmap dev       # → backend_url=http://127.0.0.1:4812
profile set-default roadmap dev
```

## Usage

### Roadmaps

```bash
roadmap list                              # Lister toutes les roadmaps
roadmap list --pid mon-pid                # Filtrer par PID
roadmap show <id>                         # Details d'une roadmap
roadmap create "Ma roadmap" --pid dev     # Creer
roadmap update <id> --name "Nouveau nom"  # Modifier
roadmap delete <id>                       # Supprimer
roadmap duplicate <id>                    # Copie profonde
roadmap state <id>                        # Etat enrichi (statuts runtime)
roadmap graph <id>                        # Graphe de dependances topologique
```

### Controle

```bash
roadmap start <id>                        # Demarrer (lance les taches level-0)
roadmap stop <id>                         # Stopper
roadmap stop <id> --hard                  # Stopper + annuler les taches en cours
roadmap pause <id>                        # Pause (running continue, pas de nouveaux triggers)
```

### Taches

```bash
roadmap task list <id>                    # Lister les taches
roadmap task show <id> <task_id>          # Details + etat runtime
roadmap task add <id> "Nom tache"         # Ajouter
roadmap task add <id> "Sous-tache" --parent <parent_id>
roadmap task update <id> <task_id> --name "Nouveau"
roadmap task delete <id> <task_id>        # Supprimer
roadmap task check <id> <task_id>         # Marquer comme termine
roadmap task uncheck <id> <task_id>       # Retirer le marquage
roadmap task start <id> <task_id>         # Demarrer l'execution
roadmap task cancel <id> <task_id>        # Annuler
roadmap task retry <id> <task_id>         # Relancer apres echec
roadmap task reset <id> <task_id>         # Remettre en pending
```

### Dependances

```bash
roadmap dep list <id>                     # Lister les dependances
roadmap dep add <id> --task <tid> --on <dep_id>   # Ajouter (avec detection de cycles)
roadmap dep remove <id> <dep_id>          # Supprimer
```

### Blocks (notes/annotations)

```bash
roadmap block list <id>                   # Lister les blocks
roadmap block list <id> --task <tid>      # Filtrer par tache
roadmap block add <id> "Contenu markdown" --task <tid>
```

### Options globales

```bash
roadmap --profile stable list             # Utiliser un profil specifique
roadmap --json list                       # Sortie JSON brute
roadmap --help                            # Aide complete
```

### Resolution d'ID

Les IDs peuvent etre passes en entier ou en prefixe (8 premiers caracteres suffisent). Si le prefixe est ambigu, le CLI affiche les correspondances. La recherche par nom (sous-chaine, insensible a la casse) est aussi supportee.
