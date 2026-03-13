# Foothold Checkpoint Tool - Manuel Utilisateur Discord

**Version 1.1.0** | Français

Guide complet pour gérer les checkpoints de campagne DCS Foothold via Discord.

---

## Table des Matières

- [Introduction](#introduction)
- [Qu'est-ce qu'un Checkpoint ?](#quest-ce-quun-checkpoint-)
- [Premiers Pas](#premiers-pas)
- [Commandes Disponibles](#commandes-disponibles)
  - [Sauvegarder un Checkpoint](#sauvegarder-un-checkpoint)
  - [Restaurer un Checkpoint](#restaurer-un-checkpoint)
  - [Lister les Checkpoints](#lister-les-checkpoints)
  - [Supprimer un Checkpoint](#supprimer-un-checkpoint)
- [Exemples d'Utilisation](#exemples-dutilisation)
- [Comprendre les Détails des Checkpoints](#comprendre-les-détails-des-checkpoints)
- [Bonnes Pratiques](#bonnes-pratiques)
- [Dépannage](#dépannage)
- [FAQ](#faq)

---

## Introduction

Le Foothold Checkpoint Tool est un plugin Discord qui vous permet de sauvegarder, restaurer et gérer des instantanés (checkpoints) de votre progression dans les campagnes DCS Foothold. Cela garantit que vous ne perdrez jamais votre progression à cause de bugs, de tests ou d'accidents.

### Fonctionnalités Principales

- 💾 **Sauvegarder l'État de la Campagne** : Créer des sauvegardes horodatées de campagnes complètes
- ♻️ **Restaurer des Campagnes** : Revenir à n'importe quel checkpoint précédent
- 📋 **Parcourir les Checkpoints** : Voir toutes les sauvegardes disponibles avec détails
- 🗑️ **Gérer le Stockage** : Supprimer les anciens checkpoints ou ceux dont vous n'avez plus besoin
- 🛡️ **Sauvegarde Automatique** : Backup automatique avant les opérations de restauration
- 🎯 **Interface Interactive** : Menus déroulants et boutons faciles à utiliser

---

## Qu'est-ce qu'un Checkpoint ?

Un **checkpoint** est un instantané complet de l'état d'une campagne Foothold à un moment précis. Il inclut :

- **Fichier de persistence de la campagne** (`.lua`) - État principal de la campagne
- **Fichiers de sauvegarde CTLD** (`.csv`) - Positions des troupes et logistique
- **Fichiers CTLD FARP** (`.csv`) - États des bases avancées
- **Fichiers de stockage** (`.csv`) - Inventaires des ressources
- **Métadonnées** - Nom de campagne, serveur, horodatage, taille, checksums

Chaque checkpoint est stocké dans un seul fichier ZIP compressé avec vérification d'intégrité.

### À Quoi Servent les Checkpoints

- **Avant des Opérations Majeures** : Sauvegarder avant des missions risquées
- **Tester du Nouveau Contenu** : Créer un point de restauration avant de tester des modifications
- **Sauvegardes Hebdomadaires** : Sauvegardes régulières pour la récupération en cas de catastrophe
- **Migrations de Serveur** : Déplacer des campagnes entre serveurs de test et de production
- **Récupération après Bug** : Revenir en arrière si un bug DCS corrompt les fichiers de campagne

---

## Premiers Pas

### Prérequis

Avant d'utiliser les commandes de checkpoint, assurez-vous :

1. ✅ Vous avez le rôle Discord requis (vérifiez avec votre administrateur serveur)
2. ✅ Le bot est en ligne et répond
3. ✅ Vous savez sur quel **serveur** vous voulez travailler
4. ✅ Vous savez quelle **campagne** vous voulez sauvegarder/restaurer

### Permissions Requises

Différentes commandes nécessitent différents rôles Discord :

| Commande | Rôles Typiquement Requis |
|---------|----------------------|
| **Save** | DCS Admin, Mission Designer |
| **Restore** | DCS Admin (le plus restrictif) |
| **List** | Tout le monde (lecture seule) |
| **Delete** | DCS Admin |

> **Note** : Les permissions réelles dépendent de la configuration de votre serveur. Contactez votre admin si vous n'avez pas accès.

### Première Configuration

Aucune configuration nécessaire ! Tapez simplement `/foothold-checkpoint` dans Discord et sélectionnez la commande dont vous avez besoin.

---

## Commandes Disponibles

Toutes les commandes sont sous le groupe `/foothold-checkpoint`. Tapez `/foothold-checkpoint` dans Discord pour voir les suggestions d'auto-complétion.

---

### Sauvegarder un Checkpoint

Créer un nouveau checkpoint de l'état actuel d'une campagne.

#### Syntaxe de la Commande

```
/foothold-checkpoint save
```

#### Paramètres

| Paramètre | Requis | Description |
|-----------|----------|-------------|
| `server` | ✅ Oui | Nom du serveur (auto-complétion disponible) |
| `campaign` | ❌ Non | Campagne à sauvegarder (ou laisser vide pour sélection interactive) |
| `name` | ❌ Non | Nom personnalisé du checkpoint |
| `comment` | ❌ Non | Description ou notes |

#### Comment Utiliser

**Option 1 : Mode Interactif (Recommandé)**

1. Tapez `/foothold-checkpoint save`
2. Sélectionnez le **serveur** via l'auto-complétion
3. Appuyez sur Entrée - un menu déroulant apparaît
4. Sélectionnez quelle(s) campagne(s) sauvegarder
5. (Optionnel) Entrez un nom et un commentaire dans la fenêtre popup
6. Cliquez sur Soumettre

**Option 2 : Mode Direct**

Tapez tout dans une seule commande :
```
/foothold-checkpoint save server:Afghanistan campaign:afghanistan name:Pre-Mission-14 comment:Avant la contre-attaque ennemie
```

#### Exemples

**Sauvegarder une seule campagne interactivement :**
```
/foothold-checkpoint save server:Caucasus
```
Puis sélectionnez "Syria Modern" dans le menu déroulant.

**Sauvegarder avec un nom descriptif :**
```
/foothold-checkpoint save server:Afghanistan campaign:afghanistan name:Backup-Fin-Semaine
```

**Sauvegarder avant de tester :**
```
/foothold-checkpoint save server:TestServer campaign:syria comment:Avant test nouvelles fonctionnalités CTLD
```

**Sauvegarder toutes les campagnes d'un serveur :**
```
/foothold-checkpoint save server:Production
```
Puis sélectionnez **"📦 All Campaigns"** dans le menu déroulant.

#### Ce Qui Se Passe

1. ✅ Le bot lit les fichiers actuels de campagne depuis le dossier `Missions/Saves` du serveur
2. ✅ Crée un checkpoint ZIP compressé avec horodatage
3. ✅ Calcule les checksums d'intégrité pour tous les fichiers
4. ✅ Stocke les métadonnées (serveur, campagne, date, taille)
5. ✅ Envoie une confirmation avec les détails du checkpoint
6. ✅ (Optionnel) Poste une notification sur le canal configuré

#### Message de Succès

```
✅ Checkpoint sauvegardé avec succès !

Nom du fichier : afghanistan_2026-02-16_20-15-30.zip
Campagne : Afghanistan
Serveur : Production
Taille : 2.4 MB
Fichiers : 4
Nom : Pre-Mission-14
Commentaire : Avant la contre-attaque ennemie

Créé le : 2026-02-16 20:15:30
```

---

### Restaurer un Checkpoint

Restaurer une campagne à un état de checkpoint précédent.

#### Syntaxe de la Commande

```
/foothold-checkpoint restore
```

#### Paramètres

| Paramètre | Requis | Description |
|-----------|----------|-------------|
| `server` | ✅ Oui | Nom du serveur cible |
| `checkpoint` | ❌ Non | Nom du fichier checkpoint (ou laisser vide pour menu déroulant) |
| `campaign` | ❌ Non | Nom de campagne (par défaut la campagne d'origine du checkpoint) |
| `auto_backup` | ❌ Non | Créer un backup avant restauration (par défaut : true) |

#### Comment Utiliser

**Option 1 : Mode Interactif (Recommandé)**

1. Tapez `/foothold-checkpoint restore`
2. Sélectionnez le **serveur** sur lequel restaurer
3. Appuyez sur Entrée - un menu déroulant apparaît avec tous les checkpoints
4. Sélectionnez le checkpoint que vous voulez restaurer
5. Confirmez la restauration

**Option 2 : Mode Direct**

Tapez tout dans une seule commande :
```
/foothold-checkpoint restore server:TestServer checkpoint:afghanistan_2026-02-15_14-00-00.zip
```

#### Menu Déroulant de Sélection des Checkpoints

Les checkpoints sont groupés et triés pour une navigation facile :

```
Checkpoints Manuels (plus récent en bas)

afghanistan_2026-02-14_10-00-00.zip
afghanistan • 02-14 10:00 • 2.3 MB

afghanistan_2026-02-16_20-15-30.zip
afghanistan • 02-16 20:15 • 2.4 MB • [Pre-Mi...

─────────── AUTO-BACKUPS ───────────

auto-backup-20260216-201000.zip
afghanistan • 02-16 20:10 • 2.4 MB
```

- **Les checkpoints manuels** apparaissent en premier (plus récent en bas)
- **Les auto-backups** apparaissent après le séparateur
- Affiche : nom de campagne, date/heure, taille du fichier, et nom/commentaire si disponible

#### Protection par Auto-Backup

Par défaut, le bot crée un **backup automatique** avant de restaurer pour éviter toute perte de données.

L'auto-backup :
- Est créé avec le pattern de nom : `auto-backup-YYYYMMDD-HHMMSS.zip`
- Contient l'état actuel avant la restauration
- Apparaît dans la section "AUTO-BACKUPS" lors du listage
- Peut être restauré comme n'importe quel autre checkpoint

**Pour désactiver l'auto-backup** (non recommandé) :
```
/foothold-checkpoint restore server:TestServer checkpoint:old_save.zip auto_backup:false
```

⚠️ **Attention** : Ne désactivez l'auto-backup que si vous êtes certain de ne pas avoir besoin d'un backup de sécurité.

#### Exemples

**Restaurer interactivement :**
```
/foothold-checkpoint restore server:Caucasus
```
Puis sélectionnez le checkpoint dans le menu déroulant.

**Restaurer un checkpoint spécifique :**
```
/foothold-checkpoint restore server:TestServer checkpoint:afghanistan_2026-02-16_20-15-30.zip
```

**Restauration inter-serveurs (déplacer un checkpoint entre serveurs) :**
```
/foothold-checkpoint restore server:ProductionServer checkpoint:afghanistan_test_2026-02-15.zip
```

**Restaurer vers une campagne différente :**
```
/foothold-checkpoint restore server:TestServer checkpoint:old_campaign.zip campaign:new_campaign
```

**Restaurer sans auto-backup :**
```
/foothold-checkpoint restore server:DevServer checkpoint:test.zip auto_backup:false
```

#### Ce Qui Se Passe

1. ✅ Le bot valide l'intégrité du checkpoint (checksums)
2. ✅ Crée un backup automatique de l'état actuel (sauf si désactivé)
3. ✅ Extrait les fichiers du checkpoint vers le dossier `Missions/Saves` du serveur
4. ✅ Renomme les fichiers pour correspondre aux conventions de nommage actuelles de la campagne
5. ✅ Envoie une confirmation avec les détails
6. ✅ (Optionnel) Poste une notification sur le canal configuré

#### Message de Succès

```
♻️ Checkpoint restauré avec succès !

Restauré : afghanistan_2026-02-16_20-15-30.zip
Sur le serveur : TestServer
Campagne : afghanistan
Auto-Backup : auto-backup-20260216-221045.zip

Fichiers restaurés : 4
Date d'origine : 2026-02-16 20:15:30
Restauré le : 2026-02-16 22:10:45
```

#### Notes Importantes

- 🛡️ **L'auto-backup est votre filet de sécurité** - toujours créé avant restauration
- 🔄 **Les fichiers sont automatiquement renommés** pour correspondre aux conventions de fichiers de campagne actuelles
- ⚙️ **Le serveur doit être arrêté** - DCS verrouille les fichiers lorsqu'il est en cours d'exécution
- 📁 **Le fichier de rangs n'est pas restauré** - `Foothold_Ranks.lua` est exclu par défaut pour préserver les classements des joueurs

---

### Lister les Checkpoints

Parcourir tous les checkpoints disponibles avec une interface interactive.

#### Syntaxe de la Commande

```
/foothold-checkpoint list
```

#### Paramètres

**Aucun** - Tout le filtrage et la navigation se font via l'interface interactive.

#### Comment Utiliser

1. Tapez `/foothold-checkpoint list`
2. Appuyez sur Entrée - un navigateur de checkpoints interactif apparaît
3. Utilisez les **boutons de filtre de type** pour afficher :
   - 🔹 **Manual** - Uniquement les checkpoints manuels
   - 🔄 **Auto-backups** - Uniquement les sauvegardes automatiques
   - 📦 **All** - Tous les checkpoints
4. Utilisez le **menu déroulant de campagne** pour sélectionner une campagne spécifique (si plusieurs campagnes existent)
5. Utilisez les **boutons Précédent/Suivant** pour naviguer dans les pages (20 checkpoints par page)
6. Sélectionnez un checkpoint dans le menu déroulant pour voir les détails complets

#### Fonctionnalités du Navigateur Interactif

**Filtres de Type (Ligne 1)** :
```
🔹 Manual (32)  🔄 Auto-backups (15)  📦 All (47)
```
Cliquez sur les boutons pour filtrer par type de checkpoint.

**Filtre de Campagne (Ligne 2)** - *Affiché uniquement si plusieurs campagnes existent* :
```
Campaign: All ▼
  ○ All Campaigns (47)
  ○ afghanistan (23)
  ○ syria (18)
  ○ caucasus (6)
```

**Sélection de Checkpoint (Ligne 3)** :
```
Select a checkpoint... ▼
  ○ afghan_2026-03-01_14-30-00.zip
    afghanistan • 03-01 14:30 • 2.4 MB
  ○ afghan_2026-03-02_18-45-00.zip  
    afghanistan • 03-02 18:45 • 2.3 MB • [Pre-Mission-14]
  ... (18 de plus)
```

**Pagination (Ligne 4)** - *Affichée uniquement si plus de 20 checkpoints* :
```
◀️ Previous    Page 1/3    Next ▶️
```

#### Information d'En-tête

Le navigateur affiche votre statut de filtre actuel :
- `📦 **42 checkpoints**` (pas de filtres)
- `📦 **Showing 1-20 of 47 checkpoints** (Type: Manual)`
- `📦 **Showing 21-40 of 47 checkpoints** (Type: Manual, Campaign: afghanistan)`

#### Exemples

**Parcourir tous les checkpoints :**
```
/foothold-checkpoint list
```
Naviguez dans les pages et utilisez le menu déroulant de filtre pour trouver des campagnes spécifiques.

**Voir uniquement les checkpoints manuels :**
```
/foothold-checkpoint list
```
Cliquez sur le bouton "🔹 Manual" après l'ouverture du navigateur.

**Trouver les auto-backups Afghanistan :**
```
/foothold-checkpoint list
```
1. Cliquez sur le bouton "🔄 Auto-backups"
2. Sélectionnez "afghanistan" dans le menu déroulant de campagne
3. Parcourez les résultats filtrés

---

### Supprimer un Checkpoint

Supprimer les anciens checkpoints ou ceux dont vous n'avez plus besoin pour libérer de l'espace de stockage.

#### Syntaxe de la Commande

```
/foothold-checkpoint delete
```

#### Paramètres

**Aucun** - Toute la sélection se fait via l'interface de navigation interactive.

#### Comment Utiliser

1. Tapez `/foothold-checkpoint delete`
2. Un navigateur de checkpoints interactif apparaît (identique à la commande list)
3. Utilisez les **boutons de filtre de type** pour affiner :
   - 🔹 **Manual** - Uniquement les checkpoints manuels
   - 🔄 **Auto-backups** - Uniquement les sauvegardes automatiques
   - 📦 **All** - Tous les checkpoints
4. Utilisez le **menu déroulant de campagne** pour sélectionner une campagne spécifique (optionnel)
5. Utilisez les **boutons Précédent/Suivant** pour naviguer dans les pages si nécessaire
6. Sélectionnez le checkpoint à supprimer dans le menu déroulant
7. Vérifiez la boîte de dialogue de confirmation avec les détails du checkpoint
8. Cliquez sur **"🗑️ Confirm Delete"** pour continuer ou **"❌ Cancel"** pour annuler
9. La confirmation doit être cliquée dans les 60 secondes

#### Navigateur Interactif

Même interface que la commande list avec un **bouton Delete** supplémentaire (Ligne 5) :
```
🔹 Manual (32)  🔄 Auto-backups (15)  📦 All (47)

Campaign: All ▼

Select a checkpoint... ▼
  ○ afghan_2026-01-15_10-00-00.zip
    afghanistan • 01-15 10:00 • 2.2 MB
  ○ syria_2026-02-01_14-00-00.zip
    syria • 02-01 14:00 • 3.0 MB • [Ancien test]

◀️ Previous    Page 1/2    Next ▶️

        🗑️ Delete
```

#### Boîte de Dialogue de Confirmation

Après avoir cliqué sur Delete, vous verrez :
```
⚠️ Confirm Deletion

Checkpoint : afghanistan_2026-01-15_10-00-00.zip
Campagne : afghanistan
Créé le : 2026-01-15 10:00:00
Taille : 2.2 MB
Fichiers : 4

Cette action ne peut pas être annulée !

[🗑️ Confirm Delete]  [❌ Cancel]
```

#### Confirmation Requise

Après la sélection, vous devez cliquer sur le bouton **"Confirm Delete"** :

```
⚠️ Confirmer la Suppression

Checkpoint : afghanistan_2026-01-15_10-00-00.zip
Campagne : afghanistan
Créé le : 2026-01-15 10:00:00
Taille : 2.2 MB
Fichiers : 4

Cette action ne peut pas être annulée !

[🗑️ Confirm Delete]  [❌ Cancel]
```

#### Exemples

**Supprimer interactivement :**
```
/foothold-checkpoint delete
```
Parcourir tous les checkpoints et en sélectionner un.

**Supprimer avec filtre :**
```
/foothold-checkpoint delete campaign:afghanistan
```
Affiche uniquement les checkpoints afghanistan.

**Supprimer un fichier spécifique :**
```
/foothold-checkpoint delete checkpoint:old_test_2026-01-10.zip
```

#### Ce Qui Se Passe

1. ✅ Affiche les détails du checkpoint et la boîte de dialogue de confirmation
2. ✅ Attend votre confirmation (timeout de 60 secondes)
3. ✅ Supprime le fichier checkpoint
4. ✅ Envoie un message de confirmation
5. ✅ (Optionnel) Poste une notification sur le canal configuré

#### Message de Succès

```
🗑️ Checkpoint supprimé avec succès !

Supprimé : afghanistan_2026-01-15_10-00-00.zip
Campagne : afghanistan
Taille : 2.2 MB

Supprimé le : 2026-02-16 22:30:00
```

#### Notes Importantes

- ⚠️ **La suppression est permanente** - ne peut pas être annulée
- ⏱️ **Timeout de 60 secondes** - vous devez confirmer dans les 60 secondes
- 🔐 **Nécessite une permission** - seuls les admins peuvent supprimer (généralement)

---

## Exemples d'Utilisation

### Routine de Backup Hebdomadaire

**Chaque vendredi soir, créer des backups de fin de semaine :**

```
/foothold-checkpoint save server:Production campaign:afghanistan name:Backup-Semaine-7 comment:Fin de la semaine 7
/foothold-checkpoint save server:Production campaign:syria name:Backup-Semaine-7 comment:Fin de la semaine 7
```

Vous pouvez aussi utiliser l'option "All Campaigns" :
```
/foothold-checkpoint save server:Production
→ Sélectionner : 📦 All Campaigns
→ Nom : Backup-Semaine-7
→ Commentaire : Fin de la semaine 7
```

### Tester du Nouveau Contenu de Mission

**Avant de tester une nouvelle mission :**

```
# 1. Sauvegarder l'état actuel
/foothold-checkpoint save server:TestServer campaign:afghanistan name:Pre-Test-Mission-15 comment:Avant test nouvelle IA ennemie

# 2. Tester la mission
# ... jouer la mission, voir si ça fonctionne ...

# 3a. Si cassé, restaurer l'état précédent
/foothold-checkpoint restore server:TestServer
→ Sélectionner : afghanistan_2026-02-16_20-15-30.zip

# 3b. Si bon, créer un nouveau checkpoint
/foothold-checkpoint save server:TestServer campaign:afghanistan name:Post-Mission-15 comment:Mission 15 terminée avec succès
```

### Déplacer une Campagne Entre Serveurs

**Tester sur le serveur de test avant de déployer en production :**

```
# 1. Sauvegarder l'état de production
/foothold-checkpoint save server:Production campaign:afghanistan name:Backup-Pre-Update

# 2. Sauvegarder l'état de test actuel
/foothold-checkpoint save server:TestServer campaign:afghanistan name:Version-Mise-a-Jour comment:Après mise à jour du contenu

# 3. Tester minutieusement sur le serveur de test
# ... tests ...

# 4. Déployer en production
/foothold-checkpoint restore server:Production
→ Sélectionner : afghanistan_updated_2026-02-16.zip (du serveur de test)

# 5. Si problèmes, revenir en arrière
/foothold-checkpoint restore server:Production
→ Sélectionner : afghanistan_2026-02-16_pre-update.zip
```

### Nettoyage Mensuel

**Supprimer les anciens checkpoints pour libérer de l'espace :**

```
# 1. Lister tous les checkpoints
/foothold-checkpoint list

# 2. Examiner et supprimer les anciens
/foothold-checkpoint delete
→ Sélectionner : afghanistan_2026-01-10_old-test.zip
→ Confirm Delete

/foothold-checkpoint delete
→ Sélectionner : syria_2025-12-15_very-old.zip
→ Confirm Delete
```

### Récupération Après Catastrophe

**Fichiers de campagne corrompus par un bug DCS :**

```
# 1. Vérifier les backups disponibles
/foothold-checkpoint list campaign:afghanistan

# 2. Restaurer le checkpoint correct le plus récent
/foothold-checkpoint restore server:Production
→ Sélectionner : afghanistan_2026-02-16_20-15-30.zip (plus récent avant corruption)
→ Confirmer

# Auto-backup de l'état corrompu sauvegardé en : auto-backup-20260216-223000.zip
```

---

## Comprendre les Détails des Checkpoints

### Format de Nom de Fichier Checkpoint

Les checkpoints utilisent un nommage standardisé :

```
campagne_YYYY-MM-DD_HH-MM-SS.zip
```

Exemples :
- `afghanistan_2026-02-16_20-15-30.zip` → Campagne Afghanistan sauvegardée le 16 fév. 2026 à 20:15:30
- `syria_modern_2026-02-14_10-00-00.zip` → Campagne Syria Modern sauvegardée le 14 fév. 2026 à 10:00:00

Les auto-backups utilisent un pattern différent :
```
auto-backup-YYYYMMDD-HHMMSS.zip
```

Exemple :
- `auto-backup-20260216-201000.zip` → Auto-backup créé le 16 fév. 2026 à 20:10:00

### Champs de Métadonnées

Chaque checkpoint stocke :

| Champ | Description |
|-------|-------------|
| **Campaign** | Nom de la campagne (ex: "afghanistan") |
| **Server** | Serveur où le checkpoint a été créé |
| **Timestamp** | Date et heure de création |
| **Size** | Taille du checkpoint compressé |
| **Files** | Nombre de fichiers inclus |
| **Name** | Nom personnalisé optionnel |
| **Comment** | Description optionnelle |
| **Checksums** | Hachages SHA-256 pour vérification d'intégrité |
| **Auto-backup** | Si c'est un backup automatique |

### Contenu d'un Checkpoint

Un checkpoint typique contient :

```
✅ foothold_afghanistan.lua              (Requis - état principal de la campagne)
✅ foothold_afghanistan_CTLD_Save.csv    (Optionnel - positions des troupes)
✅ foothold_afghanistan_CTLD_FARPS.csv   (Optionnel - états des FARP)
✅ foothold_afghanistan_storage.csv      (Optionnel - données de ressources)
❌ Foothold_Ranks.lua                    (Exclu - classements des joueurs)
```

### Pourquoi le Fichier de Rangs est Exclu

Le fichier `Foothold_Ranks.lua` suit les statistiques et classements des joueurs à travers **toutes les campagnes**. Il est exclu des checkpoints car :

- ❌ Le restaurer remettrait à zéro toutes les statistiques des joueurs
- ❌ Il est partagé entre toutes les campagnes Foothold d'un serveur
- ❌ La progression des joueurs devrait persister à travers les restaurations de checkpoint
- ✅ L'état spécifique à la campagne est dans le fichier principal `.lua`

---

## Bonnes Pratiques

### Quand Sauvegarder des Checkpoints

**Sauvegardez des checkpoints :**
- ✅ Avant des mises à jour majeures du serveur ou des patchs DCS
- ✅ Après des accomplissements de missions importantes
- ✅ Hebdomadairement/mensuellement pour des backups de routine
- ✅ Avant de tester du nouveau contenu ou des missions
- ✅ Après une progression significative dans la campagne
- ✅ Avant des opérations risquées (ex: offensive majeure)

**Ne gaspillez pas le stockage avec :**
- ❌ Des sauvegardes toutes les heures (trop fréquent)
- ❌ Des sauvegardes dupliquées du même état
- ❌ Des sauvegardes de test dont vous n'aurez plus besoin

### Conventions de Nommage

Utilisez des noms et commentaires descriptifs :

**Bon :**
```
Nom : Backup-Semaine-7
Commentaire : Fin de la semaine 7, forces alliées contrôlent 60% de la carte

Nom : Pre-Patch-2.9.7
Commentaire : Avant mise à jour DCS 2.9.7 - backup en cas de problèmes

Nom : Mission-15-Complete
Commentaire : Défense de Kaboul réussie, bases avancées ravitaillées
```

**Mauvais :**
```
Nom : backup
Commentaire : save

Nom : test
Commentaire : (vide)

Nom : asdf
Commentaire : checkpoint
```

### Gestion du Stockage

- 🗂️ Conserver **2-3 checkpoints récents** par campagne
- 🗂️ Conserver **1 checkpoint hebdomadaire** pour les 4 dernières semaines
- 🗂️ Conserver **1 checkpoint mensuel** pour les 3 derniers mois
- 🗑️ Supprimer les anciens **auto-backups** après avoir vérifié que les restaurations ont fonctionné
- 🗑️ Supprimer les **checkpoints de test** après la fin des tests

### Gestion des Auto-Backups

Les auto-backups s'accumulent rapidement. Nettoyez-les :

```
/foothold-checkpoint list
# (affiche les auto-backups dans une section séparée)

/foothold-checkpoint delete
→ Sélectionner les anciens fichiers auto-backup
→ Confirmer la suppression
```

Conservez uniquement les auto-backups récents (dernières 24-48 heures).

### Tester les Restaurations

**Avant de vous fier à un checkpoint, testez-le :**

1. Restaurer d'abord sur le serveur de test
2. Vérifier que la campagne se charge correctement
3. Vérifier que toutes les fonctionnalités marchent
4. Ensuite déployer en production si nécessaire

---

## Dépannage

### "Vous n'avez pas la permission d'utiliser cette commande"

**Cause** : Votre rôle Discord n'a pas la permission pour cette opération.

**Solution** : Contactez votre administrateur serveur pour demander l'accès.

### "Serveur introuvable"

**Cause** : Le nom du serveur n'existe pas dans la configuration du bot.

**Solution** : Vérifiez les serveurs disponibles en utilisant l'auto-complétion. Tapez `/foothold-checkpoint save server:` et voyez les suggestions.

### "Campagne introuvable dans le checkpoint"

**Cause** : Le checkpoint ne contient pas de fichiers pour la campagne spécifiée.

**Solution** : Utilisez `/foothold-checkpoint list` pour voir quelle campagne le checkpoint contient.

### "Aucune campagne détectée"

**Cause** : Aucun fichier de campagne trouvé dans le dossier Missions/Saves du serveur.

**Raisons possibles** :
- La campagne n'a pas encore été exécutée sur ce serveur
- Les fichiers sont au mauvais endroit
- Configuration du serveur incorrecte

**Solution** : Exécutez la campagne au moins une fois dans DCS pour créer les fichiers de sauvegarde, ou contactez l'admin.

### "Fichier checkpoint introuvable"

**Cause** : Le checkpoint a été supprimé ou déplacé.

**Solution** : Utilisez `/foothold-checkpoint list` pour voir les checkpoints actuellement disponibles.

### La Restauration Ne Fonctionne Pas

**Causes possibles** :
- ❌ Le serveur DCS est en cours d'exécution (fichiers verrouillés)
- ❌ Espace disque insuffisant
- ❌ Problèmes de permissions sur le système de fichiers du serveur
- ❌ Fichier checkpoint corrompu

**Solutions** :
1. Assurez-vous que le serveur DCS est arrêté
2. Vérifiez l'espace disque sur le serveur
3. Contactez l'admin si le problème persiste
4. Essayez de restaurer un checkpoint différent

### Le Bot Ne Répond Pas

**Causes possibles** :
- ❌ Le bot est hors ligne
- ❌ Problèmes d'API Discord
- ❌ Erreur de syntaxe de commande

**Solutions** :
1. Vérifiez si le bot est en ligne (statut vert)
2. Réessayez la commande
3. Vérifiez les fautes de frappe dans la commande
4. Contactez l'admin si le bot est hors ligne

---

## FAQ

### Quelle est la taille des fichiers checkpoint ?

Tailles typiques de checkpoint :
- **Petite campagne** : 1-2 MB
- **Campagne moyenne** : 2-5 MB
- **Grande campagne avec beaucoup de données** : 5-10 MB

Les checkpoints sont des fichiers ZIP compressés, donc ils sont assez petits.

### Combien de checkpoints dois-je conserver ?

Recommandé :
- **2-3 checkpoints récents** par campagne (derniers jours)
- **1 backup hebdomadaire** pour le dernier mois
- **1 backup mensuel** pour le long terme

Supprimez régulièrement les anciens auto-backups (ils s'accumulent rapidement).

### Puis-je restaurer un checkpoint sur un serveur différent ?

Oui ! La **restauration inter-serveurs** est entièrement supportée. Vous pouvez :
- Sauvegarder sur **Production** → Restaurer sur **TestServer**
- Sauvegarder sur **TestServer** → Restaurer sur **Production**
- Copier des checkpoints entre n'importe quels serveurs configurés

### Que se passe-t-il si la restauration échoue ?

Si la restauration échoue :
1. ✅ Votre **auto-backup** est en sécurité (créé avant le début de la restauration)
2. ✅ Le fichier checkpoint original **n'est pas modifié**
3. ✅ Les fichiers du serveur restent dans leur **état précédent**
4. ⚠️ Vérifiez le message d'erreur pour les détails
5. ⚠️ Contactez l'admin si le problème persiste

### Puis-je télécharger les fichiers checkpoint ?

Les fichiers checkpoint sont stockés sur le serveur DCS, pas dans Discord. Contactez votre administrateur serveur si vous avez besoin d'un accès direct aux fichiers.

### Que faire si je supprime accidentellement un checkpoint ?

**La suppression est permanente** et ne peut pas être annulée. Cependant :
- ✅ Si vous avez des **auto-backups**, ils peuvent contenir les mêmes données
- ✅ Vérifiez les autres checkpoints récents pour des sauvegardes similaires
- ⚠️ Demandez aux autres admins s'ils ont des copies
- ⚠️ Vérifiez toujours deux fois avant de confirmer la suppression

### Plusieurs personnes peuvent-elles sauvegarder des checkpoints en même temps ?

Oui, mais vous obtiendrez des fichiers checkpoint séparés avec des horodatages différents. Meilleure pratique : coordonnez-vous avec les autres admins pour éviter la confusion.

### Pourquoi certains checkpoints sont dans la section "AUTO-BACKUPS" ?

Les auto-backups sont créés automatiquement avant les opérations de restauration pour protéger contre la perte de données. Ils apparaissent dans une section séparée lors du listage des checkpoints.

Vous pouvez restaurer les auto-backups comme n'importe quel checkpoint manuel.

### Les checkpoints incluent-ils les statistiques des joueurs ?

Non, `Foothold_Ranks.lua` (statistiques des joueurs) est **intentionnellement exclu** pour préserver la progression des joueurs à travers les restaurations de checkpoint.

Seuls les fichiers spécifiques à la campagne sont inclus.

### Puis-je renommer un checkpoint après création ?

Non, les noms de fichiers checkpoint sont fixes. Cependant, vous pouvez :
- ✅ Ajouter un **nom** et un **commentaire** personnalisés lors de la sauvegarde
- ✅ Ceux-ci sont stockés dans les métadonnées et affichés dans les listes
- ❌ Vous ne pouvez pas changer le nom de fichier après création

### Combien de temps les checkpoints sont-ils conservés ?

Les checkpoints sont stockés **indéfiniment** jusqu'à ce que vous les supprimiez. Le bot ne supprime pas automatiquement les anciens checkpoints - vous devez gérer le stockage manuellement.

---

## Besoin d'Aide ?

### Contactez Votre Administrateur Serveur

Pour les problèmes liés à :
- Problèmes de permissions
- Configuration du serveur
- Campagnes manquantes
- Bot hors ligne/ne répond pas

### Signaler des Bugs

Si vous trouvez un bug dans le bot :
- GitHub Issues : https://github.com/VEAF/VEAF-foothold-checkpoint-tool/issues

### Documentation

- **Ce Manuel** : Guide utilisateur Discord
- **Plugin README** : Documentation technique pour les admins
- **README Principal** : Vue d'ensemble générale de l'outil

---

**Fin du Manuel Utilisateur** | Version 1.1.0 | Février 2026
