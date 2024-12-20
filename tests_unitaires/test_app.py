# -*- coding: utf-8 -*-

from app import app
import pytest
from app import app_manager
from tests_unitaires.test_app_manager import gestionnaire_temporaire, gestionnaire_temporaire_vide

# Ce décorateur indique que la fonction client() est une fixture pytest.
# Une fixture fournit des objets ou des configurations qui peuvent être utilisés dans les tests.
# Par exemple, dans ce cas, la fixture client configure une instance de client de test pour une application Flask.
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# test de redirection vers login
def test_home_redirection(client):
    response = client.get('/')
    assert response.status_code == 302  

# Vérifie la présence du formulaire login
def test_login_page(client):
    response = client.get('/login')
    assert b"pseudo" in response.data  

# Redirection après connexion réussie et si le cookie est défini
def test_login_succes(client):
    response = client.post('/login', data={'pseudo': 'lina'})
    assert response.status_code == 302  
    assert 'session_id' in response.headers.get('Set-Cookie', '')  

# test de deconnexion
def test_logout(client):
    # Simuler une connexion
    client.post('/login', data={'pseudo': 'lina'})
    response = client.get('/logout')
    assert response.status_code == 302  # Redirection après déconnexion
    response = client.get('/')  # Retour à la page d'accueil
    assert response.status_code == 302  # Redirige vers login




# test d'accès à la salle de vote
def test_salle_de_vote_acces(client):
    """
    Vérifie qu'un utilisateur autorisé peut accéder à la salle de vote après connexion.
    """
    # Étape 1 : Simuler une connexion avec un pseudo autorisé
    response = client.post('/login', data={'pseudo': 'lina'})
    assert response.status_code == 302  # Vérifie la redirection après connexion

    # Étape 2 : Accéder à la salle de vote après redirection
    response = client.get('/salle_de_vote', follow_redirects=True)  # Suivre automatiquement la redirection
    assert response.status_code == 200  # Vérifie que l'accès est autorisé
    assert b"Salle de vote" in response.data  # Vérifie le contenu de la page

# Test de l'accès à la salle de vote sans connexion
def test_salle_de_vote_redirection_non_authentifie(client):
    """
    Vérifie qu'un utilisateur non connecté est redirigé vers '/login'
    lorsqu'il essaie d'accéder à '/salle_de_vote'.
    """
    response = client.get('/salle_de_vote')
    assert response.status_code == 302  # Redirection vers login
    assert response.location.endswith('/login')  # Vérifie l'URL cible

# Test d'ajout d'un participant actif dans la session
def test_set_pseudo_actif(client):
    """
    Vérifie que la route '/set_pseudo_actif' définit correctement le pseudo actif.
    """
    # Connexion préalable
    client.post('/login', data={'pseudo': 'po'})
    response = client.post('/set_pseudo_actif', data={'pseudo': 'po'})
    assert response.status_code == 302  # Redirection après ajout du pseudo actif

    # Vérifie que le pseudo actif a bien été ajouté à la session
    with client.session_transaction() as sess:
        assert sess['pseudo_actif'] == 'po'

# Test de la page backlog
def test_backlog_page(client):
    """
    Vérifie que la route '/backlog' renvoie correctement la page backlog.
    """
    # Connexion préalable
    client.post('/login', data={'pseudo': 'lina'})
    response = client.get('/backlog')
    assert response.status_code == 200  # La page s'affiche correctement
    assert b"backlog" in response.data.lower()  # Vérifie que le mot backlog est présent dans la page

# Test d'ajout de fonctionnalité sans être Product Owner
def test_ajouter_fonctionnalite_acces_non_autorise(client):
    """
    Vérifie que l'ajout de fonctionnalité est refusé si l'utilisateur n'est pas Product Owner.
    """
    # Connexion avec un utilisateur non PO
    client.post('/login', data={'pseudo': 'lina'})
    response = client.post('/ajouter_fonctionnalite', data={})
    assert response.status_code == 302  # Redirection après échec
    

# Test d'ajout de fonctionnalité avec Product Owner
def test_ajouter_fonctionnalite_acces_autorise(client):
    """
    Vérifie que l'ajout de fonctionnalité est accepté si l'utilisateur est Product Owner.
    """
    # Connexion avec un utilisateur  PO
    if test_set_pseudo_actif(client):
        reponse = client.post('/ajouter_fonctionnalite', data={})
        assert reponse.status_code ==  200 

# Test d'ajout de fonctionnalité avec Product Owner
def test_modifier_fonctionnalite_acces_autorise(client):
    """
    Vérifie que l'ajout de fonctionnalité est accepté si l'utilisateur est Product Owner.
    """
    # Connexion avec un utilisateur  PO
    if test_set_pseudo_actif(client):
        reponse = client.post('/edit_fonctionnalite_route', data={})
        assert reponse.status_code ==  200 

def test_soumettre_vote(client):
    """
    Vérifie qu'un utilisateur (Lina) peut soumettre un vote correctement après l'initiation par le Scrum Master,
    avec une équipe complète incluant Hugo.
    """
    # Récupérer la fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    print("fonctionnalite_prioritaire", fonctionnalite_prioritaire)

    # Simuler la connexion de Lina
    client.post('/login', data={'pseudo': 'lina'})

    # Simuler la connexion de Hugo pour compléter l'équipe
    client.post('/login', data={'pseudo': 'hugo'})

    # Simuler la connexion du Scrum Master
    client.post('/login', data={'pseudo': 'sm'})

    # Vérifier la structure de state
    print("Structure state:", app_manager.state)

    # Vérifier que l'équipe est complète
    assert app_manager.is_team_complete(fonctionnalite_prioritaire), "L'équipe n'est pas complète."

    # SM devient actif
    with client.session_transaction() as session:
        session['pseudo_actif'] = 'sm'

    # Initier le vote
    client.post('/initier_vote', follow_redirects=True)

    # Lina devient active pour voter
    with client.session_transaction() as session:
        session['pseudo_actif'] = 'lina'

    # Lina soumet son vote
    response = client.post('/soumettre_vote', data={'pseudo': 'lina', 'vote': '5'}, follow_redirects=True)
    assert response.status_code == 200
    assert "Tous les participants ont voté." in response.data.decode('utf-8'), "Le processus de vote n'a pas été complété correctement."

# Test pour l'accès du Scrum Master
def test_acces_sm(client):
    """
    Vérifie que l'accès à la page de gestion des votes est réservé au Scrum Master.
    """
    # Simuler une connexion avec un utilisateur non SM
    client.post('/login', data={'pseudo': 'lina'})
    
    # Lina devient active 
    with client.session_transaction() as session:
        session['pseudo_actif'] = 'lina'
        
    response = client.get('/acces_sm', follow_redirects=True)
    assert response.status_code == 200  # Vérifie que la page est accessible
    assert "Accès réservé au Scrum Master.".encode('utf-8') in response.data # Vérifie le message d'erreur

    # Simuler une connexion avec un utilisateur SM
    client.post('/login', data={'pseudo': 'sm'})
    
    # SM devient actif
    with client.session_transaction() as session:
        session['pseudo_actif'] = 'sm'

    response = client.get('/acces_sm', follow_redirects=True)
    assert response.status_code == 200  # Vérifie que l'accès est autorisé
    assert "Accès Scrum Master".encode('utf-8') in response.data # Vérifie le contenu de la page



# Test pour révéler les votes
def test_reveler_votes(client):
    """
    Vérifie que le Scrum Master peut révéler les votes pour une fonctionnalité.
    """
    # Simuler une connexion en tant que SM
    client.post('/login', data={'pseudo': 'sm'})
    
    # SM devient actif
    with client.session_transaction() as session:
        session['pseudo_actif'] = 'sm'

    # Révéler les votes
    response = client.post('/reveler_votes', follow_redirects=True)
    assert response.status_code == 200  # Vérifie que l'accès est autorisé
    assert "Votes révélés avec succès".encode('utf-8') in response.data  # Vérifie le message de succès

# Test pour initier un vote
def test_initier_vote(client):
    """
    Vérifie que le Scrum Master peut initier un vote pour une fonctionnalité prioritaire.
    """
    # Simuler une connexion en tant que SM
    client.post('/login', data={'pseudo': 'sm'})
    
    # SM devient actif
    with client.session_transaction() as session:
        session['pseudo_actif'] = 'sm'
        
    # Initier un vote
    response = client.post('/initier_vote', follow_redirects=True)
    assert response.status_code == 200  # Vérifie que l'accès est autorisé
    assert "Le vote a été initié avec succès".encode('utf-8') in response.data  # Vérifie le message de succès

# Test pour réinitialiser un vote
def test_reinitialiser_vote(client):
    """
    Vérifie que le Scrum Master peut réinitialiser les votes pour une fonctionnalité prioritaire.
    """
    # Simuler une connexion en tant que SM
    client.post('/login', data={'pseudo': 'sm'})

    # Réinitialiser les votes
    response = client.post('/reinitialiser_vote', follow_redirects=True)
    assert response.status_code == 200  # Vérifie que l'accès est autorisé
    assert "Les votes ont été réinitialisés avec succès".encode('utf-8') in response.data  # Vérifie le message de succès

