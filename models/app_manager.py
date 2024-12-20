import json
from constantes import *
from models.fonctionnalite import Fonctionnalite

# La classe principale qui gère l'application
class AppManager:
    """
    @brief Classe principale pour la gestion des participants et des indicateurs globaux.
    """

    def __init__(self, backlog_file=None):
        """
        @brief Initialise l'état global pour les participants et les indicateurs.

        @param backlog_file Chemin vers le fichier JSON contenant le backlog des fonctionnalités.
        """
        self.backlog_file = backlog_file
        self.backlog = self.charger_backlog()  # Liste des fonctionnalités
        print("backlog ", self.backlog)

        # Structure globale `state`
        self.state = {
            "participants": [],  # liste de participants sous forme de dictionnaire
            "context" : "",
            "mapper_session": {},  # {session_id:pseudo ...}
            "id_fonctionnalite": None,  # ID de la fonctionnalité en cours
            "indicateurs": {  # Indicateurs globaux
                "discussion_active": False,
                "vote_commence": False,
                "votes_reveles": False,
                "tout_le_monde_a_vote": False,
                "sm_votant" : False,
                "po_votant": False,
                "pause_cafe" : False,
                "fonctionnalite_approuvee": False  # ajout boolean fonctionnalité
            }
        }

    # --- chargement du backlog des fonctionnalités ---
    def charger_backlog(self, filename=None):
        """
        @brief Charge les fonctionnalités depuis le fichier JSON et les trie par priorité.

        @return Liste des fonctionnalités du backlog.
        """
        
        fichier_a_ouvrir = filename if filename else self.backlog_file
        try:
            with open(fichier_a_ouvrir, "r") as fichier:
                contenu = fichier.read().strip()
                if not contenu:
                    print("Le fichier backlog est vide.")
                    return []

                donnees = json.loads(contenu).get("backlog", [])
                backlog = [Fonctionnalite(**f) for f in donnees]
                backlog.sort(key=lambda f: (f.statut == "Terminé", int(f.priorite)))  
                return backlog
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement du backlog : {e}")
            return []

    def lister_backlog(self):
        """
        @brief Retourne la liste des fonctionnalités du backlog.

        @return Liste des fonctionnalités.
        """
        return self.backlog

    def sauvegarder_backlog(self, filename=None):
        """
        @brief Sauvegarde le backlog trié dans le fichier JSON.
        
        @details Assure que priorités et difficultés sont des entiers.
        @param filename Nom du fichier dans lequel sauvegarder le backlog. Si None, utilise le fichier par défaut.
        """
        try:
            donnees = {
                "backlog": [
                    {
                        **f.to_dict(),
                        "priorite": int(f.priorite),  # Convertir en entier pour garantir la cohérence
                        "difficulte": int(f.difficulte)  # Convertir en entier pour garantir la cohérence
                    } for f in self.backlog
                ]
            }

            # Utiliser le fichier par défaut si aucun fichier n'est fourni
            fichier_sauvegarde = filename if filename else self.backlog_file

            with open(fichier_sauvegarde, "w") as fichier:
                json.dump(donnees, fichier, indent=4, ensure_ascii=False)
                print(f"Backlog sauvegardé avec succès dans {fichier_sauvegarde}.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du backlog : {e}")



    def trier_backlog(self):
        """
        @brief Trie la liste des fonctionnalités par priorité.
        """
        self.backlog.sort(key=lambda f: (f.statut == "Terminé", int(f.priorite)))       

    def ajouter_participant(self, pseudo, session_id):
        """
        @brief Ajoute un participant à l'état global.

        @param pseudo Nom du participant.

        @param session_id ID de session unique.

        @throws ValueError Si le pseudo est vide ou existe déjà.
        """
        if not pseudo:
            raise ValueError("Le pseudo ne peut pas être vide.")

        # Vérification si le pseudo est autorisé
        PARTICIPANTS_AUTORISES = ["po", "sm", "lina", "hugo"]  # Liste des participants autorisés
        if pseudo.lower() not in PARTICIPANTS_AUTORISES:
            raise ValueError(f"Le participant '{pseudo}' n'est pas autorisé.")

        # Vérification des doublons pseudo
        if pseudo in [p["pseudo"] for p in self.state["participants"]]:
            raise ValueError(f"Le participant avec le pseudo '{pseudo}' existe déjà.")

        # Déterminer le rôle du participant
        fonction = "Votant"
        
        avatar_mapping = {
        "po": "static/images/avatar-1.webp",
        "sm": "static/images/avatar-2.webp",
        "hugo": "static/images/avatar-3.webp",
        "lina": "static/images/avatar-4.webp",
        }
        avatar = avatar_mapping.get(pseudo.lower(), "static/images/default-avatar.webp")

        if pseudo.lower() == 'po':
            fonction = "Product Owner"

            if any(p["fonction"] == "Product Owner" for p in self.state["participants"]):
                raise ValueError("Un Product Owner existe déjà.")

        elif pseudo.lower() == 'sm':
            fonction = "Scrum Master"

            if any(p["fonction"] == "Scrum Master" for p in self.state["participants"]):
                raise ValueError("Un Scrum Master existe déjà.")

        # Ajouter le participant dans `state`
        self.state["participants"].append({
            "pseudo": pseudo,
            "fonction": fonction,
            "avatar":   avatar,
            "vote": None,
            "session_id": session_id
        })
        print(f"Participant ajouté : {self.state['participants']}")

        # ajout mappage id session et pseudo
        self.state["mapper_session"][pseudo] = session_id
        print(f"state : {self.state}")

    def get_fonctionnalite(self, fonctionnalite_id):
        """
        @brief Retourne une fonctionnalité spécifique à partir de son ID.

        @param fonctionnalite_id ID de la fonctionnalité à récupérer.

        @return L'objet Fonctionnalite correspondant à l'ID, ou None si introuvable.
        """
        return next((f for f in self.backlog if f.id == fonctionnalite_id), None)

    def afficher_fonctionnalite_prioritaire(self):
        """
        @brief Retourne la fonctionnalité ayant la priorité la plus élevée.

        @return Objet Fonctionnalite avec la priorité la plus élevée, ou None si le backlog est vide.
        """
        return self.backlog[0] if self.backlog else None

    def ajout_fonctionnalite(self, nom, description, priorite, difficulte=None, statut="A faire", mode_de_vote=VOTE_UNANIMITE, participants=[]):
        """
        @brief Ajoute une nouvelle fonctionnalité au backlog.

        @param nom Nom de la fonctionnalité.
        @param description Description de la fonctionnalité.
        @param priorite Priorité de la fonctionnalité.
        @param difficulte Niveau de difficulté (optionnel).
        @param statut Statut initial de la fonctionnalité (par défaut : "A faire").
        @param mode_de_vote Mode de vote utilisé (par défaut : "unanimité").
        @param participants Liste des participants associés à la fonctionnalité.
        """
        new_id = max((f.id for f in self.backlog), default=0) + 1
        fonctionnalite = Fonctionnalite(
            id=new_id,
            nom=nom,
            description=description,
            priorite=priorite,
            difficulte=difficulte,
            statut=statut,
            mode_de_vote=mode_de_vote,
            participants=participants
        )
        try:
            self.backlog.append(fonctionnalite)
            self.trier_backlog()
            self.sauvegarder_backlog()
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du backlog : {e}")

    def modifier_fonctionnalite(self, fonctionnalite_id, **kwargs):
        """
        @brief Modifie une fonctionnalité existante dans le backlog.

        @param fonctionnalite_id ID de la fonctionnalité à modifier.

        @param kwargs Arguments représentant les champs à modifier.
        
        @throws ValueError Si la fonctionnalité n'est pas trouvée.
        """
        fonctionnalite = next((f for f in self.backlog if f.id == fonctionnalite_id), None)
        if not fonctionnalite:
            raise ValueError("Fonctionnalité non trouvée.")

        for key, value in kwargs.items():
            if hasattr(fonctionnalite, key):
                setattr(fonctionnalite, key, value)

        self.trier_backlog()
        self.sauvegarder_backlog()

    def supprimer_fonctionnalite(self, fonctionnalite_id):
        """
        @brief Supprime une fonctionnalité du backlog.

        @param fonctionnalite_id ID de la fonctionnalité à supprimer.
        """
        self.backlog = [f for f in self.backlog if f.id != fonctionnalite_id]
        self.sauvegarder_backlog()
    
    def passer_a_fonctionnalite_suivante(self):
        """
        @brief Permet de passer à la fonctionnalité suivante dans le backlog après validation.

        @return Retourne la fonctionnalité suivante
        """
        prochaine_fonctionnalite = next(
            (f for f in self.backlog if f.statut != "Terminé"), None
        )

        if prochaine_fonctionnalite:
            self.state["id_fonctionnalite"] = prochaine_fonctionnalite.id
            self.sauvegarder_backlog()
            return prochaine_fonctionnalite  # Retourne la fonctionnalité suivante
        return None  # Retourne None si aucune autre fonctionnalité n'est disponible



# --- Gestion des votes ---
    def initier_vote(self, fonctionnalite_id):
        """
        @brief Démarre le processus de vote pour une fonctionnalité donnée.

        @details
        Initialise le vote pour une fonctionnalité spécifique. Réinitialise les votes des participants
        et met à jour les indicateurs dans `state`.

        @param fonctionnalite_id (int): L'ID de la fonctionnalité pour laquelle le vote est initié.

        @raises ValueError: Si la fonctionnalité avec l'ID donné n'existe pas.
        """
        fonctionnalite = next((f for f in self.backlog if f.id == fonctionnalite_id), None)
        if not fonctionnalite:
            raise ValueError("Fonctionnalité non trouvée.")
        
        # initialisation
        self.state["indicateurs"]["vote_commence"] = True
        self.state["id_fonctionnalite"] = fonctionnalite_id
        self.state["indicateurs"]["tout_le_monde_a_vote"] = False
        
        for participant in self.state["participants"]:
            participant["vote"] = None
        
        
        print(f"Vote initié pour la fonctionnalité : {fonctionnalite.nom}")

    def ajouter_vote(self, pseudo, vote):
        """
        @brief Ajoute un vote pour une fonctionnalité en respectant la structure de state.

        @details
        Vérifie si le participant a déjà voté. Si ce n'est pas le cas, enregistre le vote
        pour le participant spécifié.

        @param pseudo (str): Le pseudo du participant qui vote.
        @param vote (int/str): Le vote du participant.

        @raises ValueError: Si le participant a déjà voté ou s'il n'est pas trouvé.
        """

        participant = self.get_data_par_pseudo(pseudo)
        
        if participant["vote"] is not None:
            raise ValueError(f"{participant['pseudo']} a déjà voté.")
        
        # Ajouter le vote
        participant["vote"] = vote
        print(f"Vote ajouté pour {participant['pseudo']} -> {vote}")
        print("état general ", self.state)


    def tout_le_monde_a_vote(self):
        """
        @brief Vérifie si tous les participants attendus ont voté.

        @return bool: True si tous les participants votants ont voté, False sinon.        
        """
        return all(
            p["vote"] is not None for p in self.state["participants"]
            if p["fonction"] == "Votant"
        )

    def reveler_votes(self):
        """
        @brief Révèle les votes actuels pour la fonctionnalité en cours.

        @details
        Collecte et retourne les votes des participants. Met à jour l'indicateur `votes_reveles`.

        @return dict: Un dictionnaire contenant les votes de chaque participant.        """
        votes = {
            p["pseudo"]: p["vote"]
            for p in self.state["participants"]
            if p["vote"] is not None
        }
        self.state["indicateurs"]["votes_reveles"] = True
        print(f"Votes révélés : {votes}")
        return votes
    
    def valider_vote(self):
        """
        @brief Valide les votes pour la fonctionnalité actuellement en cours dans `state`.

        @details
        Selon le mode de vote défini pour la fonctionnalité, valide ou invalide les votes soumis.
        Met à jour l'état de la fonctionnalité et trie le backlog si les votes sont validés.

        @return bool: True si la fonctionnalité est approuvée, False sinon.
        """
        fonctionnalite_id = self.state.get('id_fonctionnalite')
        if not fonctionnalite_id:
            print("Aucune fonctionnalité sélectionnée pour le vote.")
            return False 

        # Récupérer la fonctionnalité par ID
        fonctionnalite = self.get_fonctionnalite(fonctionnalite_id)
        if not fonctionnalite:
            print("Fonctionnalité introuvable dans le backlog.")
            return False

        # Collecte des votes
        votes = {
            p["pseudo"]: p["vote"]
            for p in self.state["participants"]
            if p["fonction"] == "Votant" and p["vote"] is not None
        }
        if not votes:
            print("Aucun vote disponible pour cette fonctionnalité.")
            return False

        # Log des votes pour debug
        print(f"Votes pour la fonctionnalité {fonctionnalite_id}: {votes}")

        # Validation en fonction du mode de vote
        mode_de_vote = fonctionnalite.mode_de_vote

        if mode_de_vote == "unanimite":
            if len(set(votes.values())) == 1:
                self.state['indicateurs']['fonctionnalite_approuvee'] = True
            else:
                self.state['indicateurs']['fonctionnalite_approuvee'] = False

        elif mode_de_vote == "moyenne":
            moyenne = sum(map(int, votes.values())) / len(votes)
            

        else:
            print(f"Mode de vote inconnu : {mode_de_vote}")
            self.state['indicateurs']['fonctionnalite_approuvee'] = False

        # Marquer la fonctionnalité comme terminée si validée
        if self.state['indicateurs']['fonctionnalite_approuvee']:
            fonctionnalite.statut = "Terminé"
            print(f"m Fonctionnalité {fonctionnalite.nom} validée et marquée comme 'Terminé'.")

        # Trier et sauvegarder le backlog
        self.trier_backlog()
        self.sauvegarder_backlog()

        return self.state['indicateurs']['fonctionnalite_approuvee']

    def reinitialiser_votes(self):
        """
        @brief Réinitialise tous les votes.

        @details
        Efface les votes des participants et réinitialise les indicateurs liés au processus de vote.
        """
        for participant in self.state["participants"]:
            participant["vote"] = None
        self.state["indicateurs"]["vote_commence"] = False
        self.state["indicateurs"]["votes_reveles"] = False
        print("Votes réinitialisés.")



    def participants_backlog(self, fonctionnalite_id=None):
        """
        R@brief Retourne les participants associés au backlog ou à une fonctionnalité spécifique.

        @details
        Cette méthode peut retourner la liste des participants associés à une fonctionnalité spécifique 
        (via son ID) ou à l'ensemble du backlog.

        @param fonctionnalite_id (int, optional): ID de la fonctionnalité. Si aucun ID n'est fourni, 
        retourne tous les participants associés au backlog.

        @return list: Liste des participants pour la fonctionnalité donnée ou pour tout le backlog.

        @raises ValueError: Si une fonctionnalité avec l'ID donné n'est pas trouvée.
        """
        if fonctionnalite_id:
            # Trouver la fonctionnalité par ID
            fonctionnalite = self.get_fonctionnalite(fonctionnalite_id)
            if not fonctionnalite:
                raise ValueError(f"Fonctionnalité avec ID {fonctionnalite_id} introuvable.")
            return fonctionnalite.participants


    
    def get_data_par_pseudo(self, pseudo):
         """
        @brief Retourne les données d'un participant à partir de son pseudo.

        @param pseudo (str): Le pseudo du participant.

        @return dict: Les données du participant correspondant au pseudo, ou None si non trouvé.
         """
         participant = next(
            (p for p in self.state["participants"] if p["pseudo"]==pseudo), None
        )
         return participant

    def get_participant_pseudo_liste(self):
        """
        @brief Retourne une liste des pseudos de tous les participants.

        @details
        Extrait et retourne les pseudos de tous les participants actuellement dans l'état global.

        @return list: Liste des pseudos des participants.
    """
        liste_pseudo_participant = [p["pseudo"] for p in self.state["participants"] ]
        print("liste_pseudo_participant ", liste_pseudo_participant)
        return liste_pseudo_participant

    def is_team_complete(self, fonctionnalite):
        """
        @brief Vérifie si l'équipe est complète pour une fonctionnalité donnée.

        @details
        Compare la liste des participants attendus pour la fonctionnalité avec la liste des participants connectés.
        Une équipe est complète si tous les participants attendus sont connectés.

        @param fonctionnalite (object): La fonctionnalité pour laquelle vérifier l'équipe.

        @return bool: True si l'équipe est complète, False sinon.
        """
        print("Structure actuelle de participants:", self.state["participants"])

        for p in self.state["participants"]:
            print(type(p), p)
        participants_attendus = fonctionnalite.participants
        participants_connectes = [
            p["pseudo"] for p in self.state["participants"]
        ]
        return all(p in participants_connectes for p in participants_attendus)

    def logout_participant(self, session_id):
        """
        @brief Supprime un participant de l'état global.

        @details
        Cette méthode déconnecte un participant en supprimant ses données de la liste des participants 
        et du mapping `mapper_session`. Le backlog est ensuite sauvegardé.

        @param session_id (str): L'ID de session du participant à déconnecter. 
        """
        print(f"Tentative de déconnexion pour session_id : {session_id}")
        participants_avant = self.state.get("participants", [])
        print(f"Participants avant déconnexion : {participants_avant}")

        # Filtrer les participants pour supprimer celui avec le session_id
        self.state["participants"] = [
            p for p in participants_avant if p["session_id"] != session_id
        ]
        print(f"Participants après déconnexion : {self.state['participants']}")

        # Supprimer le mapping dans mapper_session
        mapper_session = self.state.get("mapper_session", {})
        for pseudo, sid in list(mapper_session.items()):
            if sid == session_id:
                del mapper_session[pseudo]
                print(f"Mapper session après suppression : {mapper_session}")

        # Sauvegarder le backlog après modification
        self.sauvegarder_backlog()
    

    def deconnecter_tous_les_participants(self):
        """
        @brief Supprime tous les participants de l'état global.

        @details
        Cette méthode déconnecte tous les participants en réinitialisant la liste des participants 
        et le mapping `mapper_session`. Le backlog est ensuite sauvegardé.
        """
        print("Déconnexion de tous les participants.")
        self.state["participants"] = []
        self.state["mapper_session"] = {}
        self.sauvegarder_backlog()
        print("Tous les participants ont été déconnectés.")





