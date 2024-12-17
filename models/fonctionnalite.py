# Fonctionnalites.py
''' Représente une fonctionnalité du backlog.
Attributs : id, nom, priorite, difficulte, statut.
Méthodes : '''

import statistics
from constantes import *

# models/fonctionnalites.py
class Fonctionnalite:
    def __init__(
        self, 
        id, 
        nom, 
        description, 
        priorite, 
        difficulte=None, 
        statut=STATUT_A_FAIRE, 
        mode_de_vote=VOTE_UNANIMITE, 
        participants=[]):
        
        self.id = id
        self.nom = nom  # Nom de la fonctionnalité
        self.description = description  # Description détaillée
        self.priorite = priorite
        self.difficulte = difficulte # Difficulté (faible, moyenne, élevée)
        self.statut = statut  # En attente, termine, en cours, ...
        self.mode_de_vote = mode_de_vote # unanimite, moyenne, medianne...
        self.participants = participants or [] # liste des developpeurs
        
        


      # méthode pour convertir en dictionnaire
    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "description": self.description,
            "priorite": self.priorite,
            "difficulte": self.difficulte,
            "statut": self.statut,
            "mode_de_vote": self.mode_de_vote,
            "participants" : self.participants or [],
  
        }
        
    def __str__(self):
        return f"Fonctionnalité: {self.nom}, priorité: {self.priorite}, Mode de vote: {self.mode_de_vote}"
    
    def __repr__(self):
        """Représentation pour les développeurs (débogage)."""
        return f"<Fonctionnalite id={self.id}, nom='{self.nom}', priorite={self.priorite}>"