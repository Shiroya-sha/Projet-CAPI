import json
from constantes import *

# La classe principale qui gère l'application
class AppManager:
    """
    @brief Classe principale pour la gestion des participants et des indicateurs globaux.
    """

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

    def get_data_participant(self, session_id):
        """
        @brief Récupère les données d'un participant à partir de son session_id.

        @param session_id ID de session du participant.
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

    def logout_participant(self, session_id):
        """
        @brief Supprime un participant de l'état global.

        @param session_id ID de session du participant.
        """
        if session_id in self.state["participants"]:
            del self.state["participants"][session_id]
