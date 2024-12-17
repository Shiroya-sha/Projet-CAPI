import json
from constantes import *
<<<<<<< HEAD
=======
from models.fonctionnalite import Fonctionnalite
>>>>>>> 2908ac5 (Ajout PO)

# La classe principale qui gère l'application
class AppManager:
    """
    @brief Classe principale pour la gestion des participants et des indicateurs globaux.
    """

<<<<<<< HEAD
    def __init__(self):
        """
        @brief Initialise l'état global pour les participants et les indicateurs.
        """
        self.state = {
            "participants": {},
            "indicators": {
                "reunion_active": False,
                "vote_commence": False,
                "votes_reveles": False,
                "tout_le_monde_a_vote": False
            }
        }
=======
    def __init__(self, backlog_file=None):
        """
        @brief Initialise l'état global pour les participants et les indicateurs.
        """
        self.backlog_file = backlog_file
        self.backlog = self.charger_backlog()  # Liste des fonctionnalités

        # Structure globale `state`
        self.state = {
            "participants": [],  # liste de participants sous forme de dictionnaire
            "mapper_session" : {} , # {session_id:pseudo ...}
            "id_fonctionnalite": None, # ID de la fonctionnalité en cours
            "indicateurs": {  # Indicateurs globaux
                "reunion_active": False,
                "vote_commence": False,
                "votes_reveles": False,
                "tout_le_monde_a_vote": False,
                "fonctionnalite_approuvee": False # ajout boolean focntionnalité
            }
        }
    
    # --- chargement du backlog dess fonctionnalités ---
    def charger_backlog(self):
        """
        Charge les fonctionnalités depuis le fichier JSON et les trie par priorité.
        """
        try:
            with open(self.backlog_file, "r") as fichier:
                contenu = fichier.read().strip()
                if not contenu:
                    print("Le fichier backlog est vide.")
                    return []

                donnees = json.loads(contenu).get("backlog", [])
                backlog = [Fonctionnalite(**f) for f in donnees]
                backlog.sort(key=lambda f: int(f.priorite))
                return backlog
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erreur lors du chargement du backlog : {e}")
            return []

    def lister_backlog(self):
        """
        Retourne la liste des fonctionnalités du backlog.
        """
        return self.backlog
    
    def sauvegarder_backlog(self):
        """
        Sauvegarde le backlog dans le fichier JSON.
        """
        try:
            with open(self.backlog_file, "w") as fichier:
                donnees = {"backlog": [f.to_dict() for f in self.backlog]}
                json.dump(donnees, fichier, indent=4)
            print("Backlog sauvegardé avec succès.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du backlog : {e}")
    
    def trier_backlog(self):
        """
        Trie la liste des fonctionnalités par priorité.
        """
        self.backlog.sort(key=lambda f: int(f.priorite))
>>>>>>> 2908ac5 (Ajout PO)

    def get_data_participant(self, session_id):
        """
        @brief Récupère les données d'un participant à partir de son session_id.

<<<<<<< HEAD
        @param session_id ID de session du participant.
=======
        @param session_id ID de sessiontrier_backlog du participant.
>>>>>>> 2908ac5 (Ajout PO)
        @return Dictionnaire des données utilisateur ou None si non trouvé.
        """
        participant = self.state["participants"].get(session_id)
        if not participant:
            return None
        return {
            "pseudo": participant["pseudo"],
            "fonction": participant["fonction"],
            "is_po": participant["fonction"] == "Product Owner",
            "is_sm": participant["fonction"] == "Scrum Master",
            "avatar": participant["avatar"],
            "vote": participant["vote"],
        }

    def ajouter_participant(self, pseudo, session_id):
        """
        @brief Ajoute un participant à l'état global.

        @param pseudo Nom du participant.
        @param session_id ID de session unique.
        @throws ValueError Si le pseudo est vide ou existe déjà.
        """
        if not pseudo:
            raise ValueError("Le pseudo ne peut pas être vide.")

<<<<<<< HEAD
        # Vérification si le pseudo est autorisé
        if pseudo.lower() not in [p.lower() for p in PARTICIPANTS_AUTORISES]:
            raise ValueError(f"Le participant '{pseudo}' n'est pas autorisé.")

        # Vérification des doublons
        if pseudo in [p["pseudo"] for p in self.state["participants"].values()]:
            raise ValueError(f"Le participant '{pseudo}' existe déjà.")

        # Ajouter le participant
        self.state["participants"][session_id] = {
            "pseudo": pseudo,
            "fonction": "Votant",
            "avatar": f"https://placehold.co/60x60/{pseudo[:2].upper()}",
            "vote": None
        }
=======
        # Vérification des doublons pseudo
        if pseudo in [p["pseudo"] for p in self.state["participants"]]:
            raise ValueError(f"Le participant avec le pseudo '{pseudo}' existe déjà.")

        # Déterminer le rôle du participant
        fonction = "Votant"
        
        if pseudo.lower() == 'po':
            fonction = "Product Owner"
            
            if any(p["fonction"] == "Product Owner" for p in self.state["participants"]):
                raise ValueError("Un Product Owner existe déjà.")
                
        elif pseudo.lower() == 'sm':
            fonction = "Scrum Master"
            
            if any(p["fonction"] == "Scrum Master" for p in self.state["participants"]):
                raise ValueError("Un Scrum Master existe déjà.")

        # Ajouter le participant dans `state`
        self.state["participants"].append( {
            
            "pseudo": pseudo,
            "fonction": fonction,
            "avatar": f"https://placehold.co/60x60/{pseudo[:2].upper()}",
            "vote": None,
            "session_id":session_id
        })
        print(f"Participant ajouté : {self.state['participants']}")
        
        # ajout mappage id session et pseudo
        self.state["mapper_session"][pseudo] = session_id
        
        print(f"state : {self.state}")

    def get_fonctionnalite(self, fonctionnalite_id):
        """
        Retourne une fonctionnalité spécifique à partir de son ID.

        Args:
            fonctionnalite_id (int): L'ID de la fonctionnalité à récupérer.

        Returns:
            Fonctionnalite: L'objet Fonctionnalite correspondant à l'ID.
            None: Si aucune fonctionnalité n'est trouvée avec cet ID.
        """
        return next((f for f in self.backlog if f.id == fonctionnalite_id), None)

    def afficher_fonctionnalite_prioritaire(self):
        """
        Retourne un dictionnaire avec la fonctionnalité ayant la plus haute priorité.
        """
        return self.backlog[0] if self.backlog else None

    def ajout_fonctionnalite(self, nom, description, priorite, difficulte=None, statut="A faire", mode_de_vote=VOTE_UNANIMITE,  participants=[]):
        """
        Ajoute une nouvelle fonctionnalité au backlog.
        """
        new_id = max((f.id for f in self.backlog), default=0) + 1
        print("id new ", new_id)
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

        print("fonctionnalite ",fonctionnalite)
        try:
            self.backlog.append(fonctionnalite)
            self.trier_backlog()
            self.sauvegarder_backlog()
        
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du backlog : {e}")
            
        print(f"Fonctionnalité ajoutée : {nom}")

    def modifier_fonctionnalite(self, fonctionnalite_id, **kwargs):
        """
        Modifie une fonctionnalité existante dans le backlog.
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
        Supprime une fonctionnalité du backlog.
        """
        self.backlog = [f for f in self.backlog if f.id != fonctionnalite_id]
        self.sauvegarder_backlog()

>>>>>>> 2908ac5 (Ajout PO)

    def logout_participant(self, session_id):
        """
        @brief Supprime un participant de l'état global.

        @param session_id ID de session du participant.
        """
        if session_id in self.state["participants"]:
            del self.state["participants"][session_id]
