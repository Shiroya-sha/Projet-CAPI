import json
from constantes import *

# la classe principale qui gère l'application
class AppManager:
    def __init__(self):
        """
        Initialise l'AppManager avec le fichier backlog et l'état global.
        """
        
        # Structure globale `state`
        self.state = {
            "participants": {},  # session_id -> {pseudo, fonction, avatar, vote, fonctionnalite_id}
            "indicators": {  # Indicateurs globaux
                "reunion_active": False,
                "vote_commence": False,
                "votes_reveles": False,
                "tout_le_monde_a_vote": False
            }
        }

    def get_data_participant(self, session_id):
        """
        Retourne les données d'un participant à partir de state["participants"].
        """
        participant = self.state["participants"].get(session_id)
        #print("nom participant ", participant.pseudo)
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

    # --- Gestion des participants ---
    def ajouter_participant(self, pseudo, session_id):
        """
        Ajoute un participant à la structure `state["participants"]`.
        """
        if not pseudo:
            raise ValueError("Le pseudo ne peut pas être vide.")
        
        # Vérification si le pseudo est autorisé
        if pseudo.lower() not in [p.lower() for p in PARTICIPANTS_AUTORISES]:
            raise ValueError(f"Le participant '{pseudo}' n'est pas autorisé.")
        
        # Vérification des doublons
        if pseudo in [p["pseudo"] for p in self.state["participants"].values()]:
            raise ValueError(f"Le participant avec le pseudo '{pseudo}' existe déjà.")

        # Déterminer le rôle du participant
        fonction = "Votant"
        if pseudo.lower() == PO.lower():
            fonction = "Product Owner"
            if any(p["fonction"] == "Product Owner" for p in self.state["participants"].values()):
                raise ValueError("Un Product Owner existe déjà.")
        elif pseudo.lower() == SM.lower():
            fonction = "Scrum Master"
            if any(p["fonction"] == "Scrum Master" for p in self.state["participants"].values()):
                raise ValueError("Un Scrum Master existe déjà.")

        # Ajouter le participant dans `state`
        self.state["participants"][session_id] = {
            "pseudo": pseudo,
            "fonction": fonction,
            "avatar": f"https://placehold.co/60x60/{pseudo[:2].upper()}",
            "vote": None,
            "fonctionnalite_id": None,
            "session_id":session_id
        }
        print(f"Participant ajouté : {self.state['participants'][session_id]}")

    def logout_participant(self, session_id):
        """
        Déconnecte un participant en supprimant ses données de la structure `state`.
        """
        if session_id in self.state["participants"]:
            del self.state["participants"][session_id]
            print(f"Participant avec session_id {session_id} déconnecté.")
        else:
            print(f"Session {session_id} introuvable.")
