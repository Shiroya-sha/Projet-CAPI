from models.app_manager import AppManager
import pytest 
import os
import shutil
import json
from constantes import *


@pytest.fixture
def gestionnaire_temporaire_vide():
    """
    Fixture qui initialise un gestionnaire avec un backlog vide.
    """
    fichier_temporaire = "backlog_test.json"
    with open(fichier_temporaire, "w") as temp:
        json.dump({"backlog": []}, temp)  # Créer un fichier temporaire avec un backlog vide

    gestionnaire = AppManager(backlog_file=fichier_temporaire)

    yield gestionnaire

    # Nettoyer après le test
    os.remove(fichier_temporaire)

@pytest.fixture
def gestionnaire_temporaire():
    """
    Fixture qui configure un gestionnaire avec un fichier temporaire pour les tests.
    Cette fixture copie le fichier backlog.json dans un fichier temporaire
    et crée une instance de gestionnaire (AppManager) utilisant ce fichier temporaire.
    Après chaque test, le fichier temporaire est supprimé.
    """
    # Chemins des fichiers
    # Chemin vers le fichier backlog.json
    BACKLOG_ORIGINAL = os.path.join(os.path.dirname(__file__), 'data', 'backlog.json')
    fichier_temporaire = "backlog_test.json"

    # Créer une copie temporaire du backlog existant
    shutil.copyfile(BACKLOG_ORIGINAL, fichier_temporaire)

    # Créer une instance de AppManager avec le fichier temporaire
    gestionnaire = AppManager(backlog_file=fichier_temporaire)
    #gestionnaire.load_backlog()  # Charger le backlog depuis le fichier temporaire

    yield gestionnaire  # Passe le gestionnaire au test

    # Nettoyer après le test
    os.remove(fichier_temporaire)  # Supprimer le fichier temporaire

# Test pour vérifier qu'un participant en double n'est pas ajouté
def test_ajouter_participant_doublon(gestionnaire_temporaire_vide):    
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")  # Ajout initial du participant "hugo"
    
    with pytest.raises(ValueError):  # On s'attend à ce qu'un doublon lève une exception
        gestionnaire_temporaire_vide.ajouter_participant("hugo", "5678")  # Tentative d'ajout du même pseudo avec un autre ID de session

    # Vérifie que le participant initial est présent dans la liste des participants
    assert any(p["session_id"] == "1234" for p in gestionnaire_temporaire_vide.state["participants"]), "Le participant n'a pas été ajouté correctement"

# ajout participant autorisé
def test_ajouter_participant_autorises(gestionnaire_temporaire_vide):    
    gestionnaire_temporaire_vide.state["participants"] = []
    pseudos_autorises = ["PO", "SM", "lina", "hugo"]
    for i, pseudo in enumerate(pseudos_autorises):
        session_id = f"session_{i}"
        gestionnaire_temporaire_vide.ajouter_participant(pseudo, session_id)
        assert any(p["session_id"] == session_id for p in gestionnaire_temporaire_vide.state["participants"]), f"{pseudo} n'a pas été ajouté correctement"

# ajout participant avec pseudo vide
def test_ajouter_participant_pseudo_vide(gestionnaire_temporaire_vide):    
    with pytest.raises(ValueError):
        gestionnaire_temporaire_vide.ajouter_participant("", "session_empty")

# ajout participant non autorisé
def test_ajouter_participant_non_autorises(gestionnaire_temporaire_vide):    
    gestionnaire_temporaire_vide.state["participants"] = []    
    pseudos_non_autorises = ["khkbi", "admin", "jean", "invalid_user"]    
    for pseudo in pseudos_non_autorises:
        with pytest.raises(ValueError, match=f"Le participant '{pseudo}' n'est pas autorisé."):
            gestionnaire_temporaire_vide.ajouter_participant(pseudo, "session_invalid")

# vérifie l'ajout d'une fonctionnalité
def test_ajout_fonctionnalite(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Test Fonctionnalité",
        description="Une fonctionnalité pour les tests",
        priorite=1,
        difficulte=5,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["test_participant"]
    )
    assert len(gestionnaire_temporaire_vide.backlog) == 1
    assert gestionnaire_temporaire_vide.backlog[0].nom == "Test Fonctionnalité"

# vérifie la modification d'une fonctionnalité
def test_modifier_fonctionnalite(gestionnaire_temporaire):
    fonctionnalite_id = gestionnaire_temporaire.backlog[0].id
    old_nom = gestionnaire_temporaire.backlog[0].nom
    gestionnaire_temporaire.modifier_fonctionnalite(fonctionnalite_id, nom="Feature Modifiée", description="Nouvelle description")
    fonctionnalite_modifiee = gestionnaire_temporaire.get_fonctionnalite(fonctionnalite_id)
    assert fonctionnalite_modifiee.nom == "Feature Modifiée", "Le nom n'a pas été modifié."
    assert fonctionnalite_modifiee.description == "Nouvelle description", "La description n'a pas été modifiée."

# vérifie la suppression d'une fonctionnalité
def test_supprimer_fonctionnalite(gestionnaire_temporaire):
    fonctionnalite_id = gestionnaire_temporaire.backlog[0].id
    gestionnaire_temporaire.supprimer_fonctionnalite(fonctionnalite_id)
    assert not any(f.id == fonctionnalite_id for f in gestionnaire_temporaire.backlog), "La fonctionnalité n'a pas été supprimée."

# vérifie la déconnexion d'un participant
def test_logout_participant(gestionnaire_temporaire_vide):   
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.logout_participant("1234")
    assert "1234" not in gestionnaire_temporaire_vide.state["participants"]

# verifier si les votes sont initiés par le SM
def test_initier_vote(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Fonctionnalité Test",
        description="Test pour initier un vote",
        priorite=1,
        difficulte=3,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["hugo"]
    )
    fonctionnalite_id = gestionnaire_temporaire_vide.backlog[0].id
    gestionnaire_temporaire_vide.initier_vote(fonctionnalite_id)
    assert gestionnaire_temporaire_vide.state["indicateurs"]["vote_commence"], "Le vote n'a pas été initié correctement."
    assert gestionnaire_temporaire_vide.state["id_fonctionnalite"] == fonctionnalite_id, "L'ID de la fonctionnalité votée est incorrect."

# Test pour ajouter un vote
def test_ajouter_vote(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Fonctionnalité Test",
        description="Test pour ajouter un vote",
        priorite=1,
        difficulte=3,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["hugo"]
    )
    fonctionnalite_id = gestionnaire_temporaire_vide.backlog[0].id
    gestionnaire_temporaire_vide.initier_vote(fonctionnalite_id)
    gestionnaire_temporaire_vide.ajouter_vote("hugo", 5)
    participant = gestionnaire_temporaire_vide.get_data_par_pseudo("hugo")
    assert participant["vote"] == 5, "Le vote n'a pas été enregistré correctement."

# Test pour tout le monde a voté
def test_tout_le_monde_a_vote(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.ajouter_participant("lina", "5678")
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Fonctionnalité Test",
        description="Test pour tout le monde a voté",
        priorite=1,
        difficulte=3,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["hugo", "lina"]
    )
    fonctionnalite_id = gestionnaire_temporaire_vide.backlog[0].id
    gestionnaire_temporaire_vide.initier_vote(fonctionnalite_id)
    gestionnaire_temporaire_vide.ajouter_vote("hugo", 5)
    assert not gestionnaire_temporaire_vide.tout_le_monde_a_vote(), "Le test a échoué avant que tout le monde ait voté."
    gestionnaire_temporaire_vide.ajouter_vote("lina", 8)
    assert gestionnaire_temporaire_vide.tout_le_monde_a_vote(), "Le test a échoué après que tout le monde ait voté."

# Test pour révéler les votes
def test_reveler_votes(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.ajouter_participant("lina", "5678")
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Fonctionnalité Test",
        description="Test pour révéler les votes",
        priorite=1,
        difficulte=3,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["hugo", "lina"]
    )
    fonctionnalite_id = gestionnaire_temporaire_vide.backlog[0].id
    gestionnaire_temporaire_vide.initier_vote(fonctionnalite_id)
    gestionnaire_temporaire_vide.ajouter_vote("hugo", 5)
    gestionnaire_temporaire_vide.ajouter_vote("lina", 8)
    votes = gestionnaire_temporaire_vide.reveler_votes()
    assert votes == {"hugo": 5, "lina": 8}, "Les votes révélés ne sont pas corrects."

# Test pour valider un vote
def test_valider_vote(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Fonctionnalité Test",
        description="Test pour valider un vote",
        priorite=1,
        difficulte=3,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["hugo"]
    )
    fonctionnalite_id = gestionnaire_temporaire_vide.backlog[0].id
    gestionnaire_temporaire_vide.initier_vote(fonctionnalite_id)
    gestionnaire_temporaire_vide.ajouter_vote("hugo", 5)
    result = gestionnaire_temporaire_vide.valider_vote()
    assert result, "Le vote n'a pas été validé correctement."

# Test pour réinitialiser les votes
def test_reinitialiser_votes(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Fonctionnalité Test",
        description="Test pour réinitialiser les votes",
        priorite=1,
        difficulte=3,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["hugo"]
    )
    fonctionnalite_id = gestionnaire_temporaire_vide.backlog[0].id
    gestionnaire_temporaire_vide.initier_vote(fonctionnalite_id)
    gestionnaire_temporaire_vide.ajouter_vote("hugo", 5)
    gestionnaire_temporaire_vide.reinitialiser_votes()
    participant = gestionnaire_temporaire_vide.get_data_par_pseudo("hugo")
    assert participant["vote"] is None, "Les votes n'ont pas été réinitialisés correctement."

# Test pour obtenir les données par pseudo
def test_get_data_par_pseudo(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    participant_data = gestionnaire_temporaire_vide.get_data_par_pseudo("hugo")
    assert participant_data is not None, "Aucune donnée retournée pour le participant."
    assert participant_data["pseudo"] == "hugo", "Les données du participant sont incorrectes."

# Test pour vérifier si l'équipe est complète
def test_is_team_complete(gestionnaire_temporaire_vide):
    gestionnaire_temporaire_vide.ajouter_participant("hugo", "1234")
    gestionnaire_temporaire_vide.ajouter_participant("lina", "5678")
    gestionnaire_temporaire_vide.ajout_fonctionnalite(
        nom="Fonctionnalité Test",
        description="Test pour vérifier si l'équipe est complète",
        priorite=1,
        difficulte=3,
        statut="A faire",
        mode_de_vote="unanimite",
        participants=["hugo", "lina"]
    )
    fonctionnalite = gestionnaire_temporaire_vide.backlog[0]
    assert gestionnaire_temporaire_vide.is_team_complete(fonctionnalite), "L'équipe n'est pas considérée comme complète."
