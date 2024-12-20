# Application Planning Poker

## La documentation doxygen est disponible sous la version 3 correspondant à la branche main.

## Introduction
L'application Planning Poker est un outil collaboratif conçu pour aider les équipes agiles à estimer la complexité et l'effort nécessaires pour réaliser les tâches d'un backlog. Cette application fonctionne sur un appareil partagé, où les membres de l'équipe se connectent à tour de rôle pour jouer leurs rôles (Product Owner (PO), Scrum Master (SM), ou votant). Elle intègre les principes clés de l'agilité, offrant une interface intuitive pour la gestion des backlogs, les votes et la facilitation des sessions.

Chaque rôle a des responsabilités spécifiques :
- **Product Owner (PO) :** Gère le backlog et définit les priorités.
- **Scrum Master (SM) :** Supervise le processus de vote et valide les résultats.
- **Votants :** Membres de l'équipe qui votent pour estimer les tâches.

L'application assure une collaboration fluide grâce à des fonctionnalités de sauvegarde et de reprise des sessions, suivi de progression et exportation des résultats.

## Aperçu des fonctionnalités
1. **Connexion :**
   - Les utilisateurs se connectent à tour de rôle en sélectionnant leurs rôles depuis le backlog prédéfini.
2. **Gestion du backlog :**
   - Le PO gère le backlog, ajoutant, modifiant et priorisant les tâches.
3. **Vote :**
   - Les votants estiment les tâches.
   - Le SM révèle et valide les votes ou facilite les discussions en cas de désaccord.
4. **Gestion des sessions :**
   - La progression est sauvegardée dans un fichier JSON.
   - Les sessions peuvent être reprises à tout moment.

---

### Gestion des cartes spéciales : Carte Café et Point d'Interrogation

#### **Carte Café**
La carte café est une option spéciale qui permet de suspendre la session pour une pause collective. Voici comment elle fonctionne :
1. **Processus :**
   - Tous les participants, y compris le Product Owner (PO) et le Scrum Master (SM), doivent voter "café".
   - Une fois que tous les participants ont voté, l'application passe automatiquement en mode "pause".
2. **Sauvegarde de l'état :**
   - Le Scrum Master doit cliquer sur **"État initial du backlog"** pour sauvegarder la session en cours avant la pause.
3. **Reprise :**
   - Une fois que tous les participants reviennent de la pause, la session peut être reprise en chargeant l'état sauvegardé.

#### **Point d'Interrogation**
La carte "?" (point d'interrogation) est utilisée lorsqu'un participant estime qu'il n'a pas suffisamment d'informations ou qu'une discussion est nécessaire :
1. **Processus :**
   - Si un participant sélectionne "?", l'application active automatiquement le mode "discussion".
   - Un message est affiché pour signaler qu'une discussion est nécessaire avant de continuer.
2. **Reprise :**
   - Après la discussion, le Scrum Master peut réinitialiser les votes pour permettre un nouveau tour d'estimation.

---

## Instructions d'installation

### Prérequis
Assurez-vous d'avoir les éléments suivants installés :
- Python 3.11.1
- Pip

### Étapes pour exécuter l'application

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/Organisation-CAPI/Projet-CAPI.git
   cd <repository_name>
   ```

2. **Installer les dépendances :**
   Installez les dépendances requises en utilisant le fichier `requirements.txt` :
   ```bash
   pip install -r requirements.txt
   ```

3. **Lancer l'application :**
   Lancez l'application avec la commande suivante :
   ```bash
   python app.py
   ```

4. **Accéder à l'application :**
   Ouvrez votre navigateur web et accédez à :
   ```
   http://127.0.0.1:5000
   ```

## Comment utiliser l'application

### Processus de connexion
1. Les utilisateurs se connectent un à un en sélectionnant leurs rôles, les pseudonymes sont : PO, SM et les votants prédéfinis depuis le backlog.
2. Une fois connectés, ils sont redirigés vers l'interface principale qui affiche les options en fonction de leurs rôles.

### Gestion du backlog (PO)
1. Le PO peut ajouter, modifier ou supprimer des tâches dans le backlog.
2. Chaque tâche inclut des détails comme le nom, la description, la priorité, la difficulté et les participants assignés.
3. Les tâches sont sauvegardées dans un fichier JSON pour la persistance.

### Processus de vote
1. **Démarrer le vote (SM) :**
   - Le SM initie le processus de vote via le menu "Accès SM" et sélectionne "Initier le vote".
   - Les participants connectés à la session sont affichés.

2. **Soumettre les votes (Votants) :**
   - Les votants sélectionnent leurs estimations parmi les options prédéfinies (e.g., 1, 2, 3, 5, etc).
   - Les votes sont soumis en cliquant sur l'avatar correspondant.

3. **Révéler les votes (SM) :**
   - Le SM révèle les votes et valide la tâche en cas de consensus.
   - En cas de désaccord, le SM facilite une discussion et réinitialise les votes pour un nouveau tour.

### Progression et fin de session
1. **Suivi de la progression :**
   - Le menu backlog affiche les statuts des tâches (e.g., "En cours," "Terminé").
   - Les difficultés et estimations sont mises à jour dynamiquement.

2. **Clôture de session :**
   - Une fois toutes les tâches validées, le SM se déconnecte, clôturant ainsi la session.

3. **Sauvegarde et reprise :**
   - La progression est automatiquement sauvegardée dans un fichier JSON.
   - Les sessions peuvent être reprises en chargeant le fichier sauvegardé via le menu.

## Structure JSON
- L'application utilise un fichier JSON structuré pour gérer les tâches et les sessions.
- Chaque tâche inclut :
  ```json
  {
      "name": "Nom de la tâche",
      "description": "Description de la tâche",
      "priority": 1,
      "difficulty": 5,
      "status": "En cours",
      "mode_of_vote": "unanimité",
      "participants": ["lina", "hugo"]
  }
  ```

## Captures d'écran clés
### Page de connexion
- Les utilisateurs sélectionnent leurs rôles et se connectent séquentiellement.

### Interface de vote
- Les participants soumettent leurs votes pour les tâches, visibles uniquement par le SM jusqu'à leur révélation.

### Gestion du backlog
- Le PO gère les listes de tâches et suit la progression.

### Actions du Scrum Master
- Initier, révéler, valider ou réinitialiser les votes selon les besoins.

## Intégration CI/CD
1. **Tests automatisés :**
   - Les tests des fonctionnalités principales (e.g., connexion, gestion du backlog, vote) sont automatisés avec un fichier yml utilisant le package `pytest`.

2. **Documentation :**
   - Générée avec Doxygen pour une meilleure clarté du code.

3. **Déploiement :**
   - Intégré avec GitHub Actions pour une intégration et un déploiement continus.

## Auteurs
- **Hugo MAURIN**
- **Lina RHIM**
