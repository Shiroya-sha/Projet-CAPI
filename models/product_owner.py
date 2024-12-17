from models.participant import Participant

class ProductOwner(Participant):
    def __init__(self, pseudo):
        """
        Initialise le Product Owner en tant que Participant avec un rôle spécifique.
        """
        super().__init__(pseudo, fonction_participant="PO") # Appelle le constructeur de Participant
        del self.vote  # Supprime explicitement l'attribut `vote`

    def expliquer_fonctionnalite(self, fonctionnalite):
        """
        Donne une explication détaillée de la fonctionnalité.
        """
        print(f"Explication de la fonctionnalité : {fonctionnalite.nom}")
        print(f"Description : {fonctionnalite.description}")
        print(f"Priorité : {fonctionnalite.priorite}")
