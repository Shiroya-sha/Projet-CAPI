import pytest
from app import app

# Pour exécuter les tests faire dans le terminal cette commande : PYTHONPATH=$(pwd) pytest tests/test_routes.py
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client

def test_index_route(client):
    """Test de la route index"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Bienvenue dans l'application Planning Poker." in response.data

def test_login_route_get(client):
    """Test de la route login (GET)"""
    response = client.get('/login')
    print(response.data.decode())  # Debug : Voir le contenu de la réponse
    assert response.status_code == 200
    assert b"Connectez-vous pour participer a la session d'estimation." in response.data

def test_login_route_post(client):
    """Test de la route login (POST)"""
    # Initialiser la session via la route '/'
    client.get('/')
    # Effectuer un POST vers /login
    response = client.post('/login', data={'pseudo': 'TestUser'}, follow_redirects=True)
    print(response.data.decode())  # Debug : Voir le contenu de la réponse
    assert response.status_code == 200
    # Vérifier que "TestUser" est bien dans la session
    with client.session_transaction() as session:
        assert "TestUser" in session["participants"]

def test_logout_route(client):
    """Test de la route logout"""
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Bienvenue dans l'application Planning Poker" in response.data
