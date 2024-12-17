from app import app
import pytest

# Ce décorateur indique que la fonction client() est une fixture pytest.
# Une fixture fournit des objets ou des configurations qui peuvent être utilisés dans les tests.
# Par exemple, dans ce cas, la fixture client configure une instance de client de test pour une application Flask.
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# test de redirection vers login
def test_home_redirect(client):
    response = client.get('/')
    assert response.status_code == 302  

# Vérifie la présence du formulaire login
def test_login_page(client):
    response = client.get('/login')
    assert b"pseudo" in response.data  

# Redirection après connexion réussie et si le cookie est défini
def test_login_success(client):
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
def test_salle_de_vote_access(client):
    client.post('/login', data={'pseudo': 'lina'})
    response = client.get('/salle_de_vote')
    assert response.status_code == 200  # Accès autorisé
    assert b"Salle de vote" in response.data  # Vérifie le contenu de la page

