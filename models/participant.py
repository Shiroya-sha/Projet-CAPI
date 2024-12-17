
# Participant.py
'''
Représente chaque membre de l'équipe.
Attributs : pseudo, avatar, has_voted.
Méthodes : vote(card), reset_vote(). 
'''
import hashlib

class Participant:
    def __init__(self, pseudo, fonction_participant):
        self.pseudo = pseudo # membre1, membre2 ...
        self.avatar = self.generate_avatar() 
        self.fonction_participant = fonction_participant  # participant, PO, SM 
        self.vote = None # valeur du vote = '20' ou'40' ... nombre de point
    
    def generate_avatar(self):
        '''Générer un avatar basé sur le pseudo (initiales et couleur dynamique)'''
        
        color = hashlib.md5(self.pseudo.encode()).hexdigest()[:6]  # Couleur unique basée sur le pseudo
        return f"https://placehold.co/60x60/{color}/ffffff?text={self.pseudo[:2].upper()}"
    
    
    def soumettre_vote(self, valeur_vote):
        """
        Permet au participant de soumettre un vote.
        """
        self.vote = valeur_vote
        print(f"{self.pseudo} a voté : {valeur_vote}")

    def annuler_vote(self):
        """
        Annule le vote du participant.
        """
        self.vote = None
        print(f"Vote annulé pour {self.pseudo}.")

    def __repr__(self):
        return f"Participant(pseudo='{self.pseudo}', role='{self.fonction_participant}')"