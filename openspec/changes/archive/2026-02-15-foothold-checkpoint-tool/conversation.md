# Conversation - Création de foothold-checkpoint

## Contexte

Création d'un outil CLI Python pour gérer les sauvegardes (checkpoints) des campagnes DCS Foothold de la VEAF.

## Spécifications détaillées

### But de l'outil

Sauvegarder, restaurer et lister des points de sauvegarde pour les campagnes dynamiques DCS Foothold.

### Nom

`foothold-checkpoint`

### Fichiers de persistence

- **Localisation** : `SERVER\Missions\Saves` où SERVER est le chemin du serveur
- **Fichiers par campagne** : Chaque campagne a typiquement :
  - Un fichier `.lua` principal
  - Un fichier `_CTLD_FARPS.csv`
  - Un fichier `_CTLD_Save.csv`
  - Un fichier `_storage.csv`
- **Fichier partagé** : `Foothold_Ranks.lua` (sauvegardé dans chaque checkpoint, restauration optionnelle)
- **Fichiers à ignorer** : `foothold.status`

### Normalisation des noms de campagnes

Les campagnes peuvent avoir des versions dans leurs noms qu'il faut normaliser :
- Patterns de version à ignorer : `_v0.2`, `_V0.1`, `_0.1`
- Exemples :
  - `FootHold_CA_v0.2*` → campagne **"CA"**
  - `FootHold_Germany_Modern_V0.1*` → campagne **"Germany_Modern"**
  - `foothold_afghanistan*` → campagne **"afghanistan"**

**IMPORTANT** : Les campagnes peuvent évoluer et changer de nom technique au fil du temps. La configuration YAML stocke l'historique des noms (du plus ancien au plus récent). Lors de la restauration, on utilise le dernier nom de la liste.

**ATTENTION** : `Germany_Modern` et `Germany_ColdWar` sont deux campagnes **différentes** de la map Germany.

### Structure de stockage

- **Répertoire de checkpoints** : Dossier unique configurable (par défaut `~/.foothold-checkpoints/`)
- **Granularité** : Un checkpoint = UNE campagne
- **Nom du fichier checkpoint** : `{campagne}_{YYYY-MM-DD_HH-MM-SS}.zip`
- **Contenu du ZIP** :
  - `metadata.json` (métadonnées du checkpoint)
  - Tous les fichiers de la campagne
  - `Foothold_Ranks.lua`

### Métadonnées (metadata.json)

```json
{
  "server": "production-1",
  "campaign": "Germany_Modern",
  "timestamp": "2024-02-13T20:30:00Z",
  "name": "Avant mission majeure",
  "comment": "Optionnel",
  "files": {
    "FootHold_Germany_Modern_V0.1.lua": {
      "original_name": "FootHold_Germany_Modern_V0.1.lua",
      "checksum": "sha256:abc123..."
    },
    "FootHold_Germany_Modern_V0.1_CTLD_FARPS.csv": {
      "original_name": "FootHold_Germany_Modern_V0.1_CTLD_FARPS.csv",
      "checksum": "sha256:def456..."
    },
    "Foothold_Ranks.lua": {
      "original_name": "Foothold_Ranks.lua",
      "checksum": "sha256:ghi789..."
    }
  }
}
```

**Utilité du nom original** : Permet de tracer l'historique et de détecter les renommages lors de la restauration.

### Configuration (config.yaml)

**Emplacement** : `~/.foothold-checkpoint/config.yaml`
**Création automatique** : Si non existant au premier lancement

```yaml
# Répertoire de stockage des checkpoints
checkpoints_dir: ~/.foothold-checkpoints

# Serveurs DCS
servers:
  prod-1:
    path: D:\Servers\Production-1\Missions\Saves
    description: "Serveur de production principal"
  test-server:
    path: D:\Servers\Test-Server\Missions\Saves
    description: "Serveur de test"

# Mapping des noms de campagnes (historique du plus ancien au plus récent)
campaigns:
  Germany_Modern:
    - GCW_Modern              # ancien nom
    - Germany_Modern          # nom actuel (utilisé lors de la restauration)
  Germany_ColdWar:
    - GCW_ColdWar
    - Germany_ColdWar
  Caucasus:
    - CA
  Afghanistan:
    - afghanistan
  Sinai:
    - SI
  PersianGulf:
    - persiangulf
  PersianGulf_ColdWar:
    - persiangulf_Coldwar
  Syria:
    - Syria_Extended
```

### Fonctionnalités

#### 1. Save (Sauvegarde)

- Sauvegarder **une** campagne spécifique
- Option `--all` pour sauvegarder **toutes** les campagnes (crée N checkpoints)
- Métadonnées stockées : serveur, campagne, timestamp, nom optionnel, commentaire, checksums
- Nom original de chaque fichier préservé

#### 2. List (Lister)

- Lister tous les checkpoints
- Filtres optionnels :
  - Par serveur : `--server prod-1`
  - Par campagne : `--campaign afghanistan`
- Affichage : nom du fichier, serveur, campagne, date, nom/commentaire

#### 3. Restore (Restauration)

- Restaurer un checkpoint vers n'importe quel serveur (cross-serveur possible)
- Vérification d'intégrité (checksums) avant restauration
- Option `--skip-ranks` pour ne pas restaurer `Foothold_Ranks.lua`
- Utilise le dernier nom de campagne (plus récent) pour créer les fichiers

#### 4. Delete (Suppression)

- Suppression d'un checkpoint
- Mode CLI : option directe
- Mode guidé : menu interactif

### Architecture technique

#### Technologies

- **Python** : 3.10+
- **CLI** : Typer (commandes) + Rich (UI terminal)
- **Config** : PyYAML
- **Archives** : zipfile (standard lib)
- **Checksums** : hashlib (standard lib)

#### Structure du projet

```
VEAF-Foothold-Campaign-Manager/
├── foothold_checkpoint/          # Package Python core
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── checkpoint.py         # Logique checkpoint
│   │   ├── config.py             # Gestion config YAML
│   │   ├── storage.py            # Save/restore/delete/list
│   │   └── campaign.py           # Détection/normalisation
│   └── cli.py                    # CLI avec Typer + Rich
├── plugin/                       # Préparation plugin DCSServerBot
│   ├── __init__.py
│   └── commands.py               # Commandes Discord (structure)
├── config.yaml.example           # Exemple de config
├── tests/
│   └── data/foothold/            # Données de test
├── openspec/                     # Workflow OpenSpec
└── README.md
```

#### Compatibilité DCSServerBot

L'outil sera développé pour être compatible avec DCSServerBot (bot Discord) :
- **Version core** : Module Python réutilisable
- **Version CLI** : Script CLI avec Typer + Rich
- **Version plugin** : Plugin DCSServerBot pour intégration Discord future

**Structure d'un plugin DCSServerBot** (référence) :
```python
class CheckpointPlugin(Plugin):
    def __init__(self, bot: DCSServerBot):
        super().__init__(bot)

    @command(description='Sauvegarder une campagne')
    @app_commands.autocomplete(...)
    async def save(self, interaction: discord.Interaction, ...):
        # Logique Discord
        ...

async def setup(bot: DCSServerBot):
    await bot.add_cog(CheckpointPlugin(bot))
```

### Commandes CLI

#### Mode avec options

```bash
# Sauvegarder une campagne
foothold-checkpoint save --server prod-1 --campaign afghanistan --name "Mission 5"

# Sauvegarder toutes les campagnes
foothold-checkpoint save --server prod-1 --all --name "Sauvegarde globale"

# Lister les checkpoints
foothold-checkpoint list
foothold-checkpoint list --server prod-1
foothold-checkpoint list --campaign afghanistan

# Restaurer
foothold-checkpoint restore afghanistan_2024-02-13_20-30-00.zip --server test-server
foothold-checkpoint restore afghanistan_2024-02-13_20-30-00.zip --server test-server --skip-ranks

# Supprimer
foothold-checkpoint delete afghanistan_2024-02-13_20-30-00.zip
```

#### Mode guidé (interactif)

```bash
# Lancer le mode interactif
foothold-checkpoint
```

Workflow du mode guidé :
1. Menu principal : [Save] [Restore] [List] [Delete] [Exit]
2. Selon le choix, sous-menus pour :
   - Sélectionner le serveur
   - Sélectionner la campagne (ou toutes)
   - Entrer un nom/commentaire
   - Confirmer l'action

Utilise Rich pour :
- Tableaux de données
- Prompts avec choix multiples
- Indicateurs de progression
- Couleurs et formatage

### Comportement détaillé

#### Lors de la sauvegarde

1. Détecte les fichiers de campagne dans le répertoire `Saves` du serveur
2. Normalise le nom de campagne (retire les versions)
3. Crée un fichier ZIP : `{campagne}_{YYYY-MM-DD_HH-MM-SS}.zip`
4. Inclut tous les fichiers de la campagne + `Foothold_Ranks.lua`
5. Génère les checksums SHA-256
6. Crée `metadata.json` avec :
   - Serveur source
   - Nom de campagne normalisé
   - Timestamp
   - Nom/commentaire optionnels
   - Liste des fichiers avec noms originaux et checksums
7. Stocke le ZIP dans `checkpoints_dir`

#### Lors de la restauration

1. Lit `metadata.json` du checkpoint
2. Vérifie l'intégrité (checksums)
3. Lit le nom de campagne (ex: "Germany_Modern")
4. Cherche le dernier nom dans la config (plus récent)
5. Extrait les fichiers et les renomme si nécessaire
6. Copie vers le répertoire `Saves` du serveur cible
7. Option `--skip-ranks` : ne restaure pas `Foothold_Ranks.lua`

#### Lors de la suppression

1. Demande confirmation (mode guidé)
2. Supprime le fichier ZIP du répertoire de checkpoints

#### Lors du listing

1. Parcourt tous les ZIP dans `checkpoints_dir`
2. Lit les `metadata.json`
3. Applique les filtres (`--server`, `--campaign`)
4. Affiche un tableau avec :
   - Nom du fichier
   - Serveur
   - Campagne
   - Date/heure
   - Nom/commentaire

### Données de test

Fichiers de test disponibles dans `tests/data/foothold/` :
- `foothold_afghanistan*` (4 fichiers)
- `FootHold_CA_v0.2*` (4 fichiers)
- `FootHold_Germany_Modern_V0.1*` (4 fichiers)
- `foothold_persiangulf*` (plusieurs versions)
- `FootHold_SI_v0.3*` (4 fichiers)
- `footholdSyria_Extended_0.1*` (3 fichiers)
- `Foothold_Ranks.lua`
- `foothold.status` (à ignorer)

### Priorités de développement

Pour le moment :
1. ✅ Core (logique métier)
2. ✅ CLI avec Typer + Rich
3. ✅ Préparation de la structure plugin/ (sans implémentation complète)
4. ❌ Intégration dans DCSServerBot (plus tard)

### Fonctionnalités confirmées

- ✅ Vérification d'intégrité (checksums) avant restauration
- ✅ Suppression de checkpoints (option CLI + menu interactif)
- ❌ Export/import de checkpoints (non nécessaire)
