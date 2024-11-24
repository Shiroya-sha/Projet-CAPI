# Fonctionnalites.py
''' Représente une fonctionnalité du backlog.
Attributs : id, nom, priorite, difficulte, statut.
Méthodes : set_difficulte(difficulte), set_statut(statut).'''

# models/fonctionnalites.py
class Fonctionnalites:
    def __init__(self, id, nom, description, priorite, difficulte=None, statut="A faire"):
        self.id = id
        self.nom = nom
        self.description = description
        self.priorite = priorite
        self.difficulte = difficulte
        self.statut = statut  # Peut être "Backlog Produit", "Sélectionné pour Sprint", "En cours", "Terminé"

# Exemple d'utilisation :
# feature = Feature(id=1, nom="Nouvelle fonctionnalité", description="Description de la fonctionnalité", priorite=80)
    
    def set_difficulte(self,difficulte):
        self.difficulte = difficulte
        
        
    def set_statut(self,statut):
        self.statut = statut
        
        