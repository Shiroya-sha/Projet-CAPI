from models.app_manager import AppManager
import pytest 

def test_ajouter_participant():
    manager = AppManager()
    manager.ajouter_participant("hugo", "1234")
    assert "1234" in manager.state["participants"]

def test_logout_participant():
    manager = AppManager()
    manager.ajouter_participant("hugo", "1234")
    manager.logout_participant("1234")
    assert "1234" not in manager.state["participants"]

def test_ajouter_participant_doublon():
    manager = AppManager()
    manager.ajouter_participant("hugo", "1234")
    with pytest.raises(ValueError):
        manager.ajouter_participant("hugo", "5678")

    assert "1234" in manager.state["participants"], "Le participant n'a pas été ajouté correctement"


def test_ajouter_participant_autorises():
    manager = AppManager()
    pseudos_autorises = ["PO", "SM", "lina", "hugo"]

    for i, pseudo in enumerate(pseudos_autorises):
        session_id = f"session_{i}"
        manager.ajouter_participant(pseudo, session_id)
        assert session_id in manager.state["participants"], f"{pseudo} n'a pas été ajouté correctement"

def test_ajouter_participant_pseudo_vide():
    manager = AppManager()
    with pytest.raises(ValueError):
        manager.ajouter_participant("", "session_empty")


def test_ajouter_participant_non_autorises():
    manager = AppManager()
    pseudos_non_autorises = ["khkbi", "admin", "jean", "invalid_user"]

    for pseudo in pseudos_non_autorises:
        with pytest.raises(ValueError, match=f"Le participant '{pseudo}' n'est pas autorisé."):
            manager.ajouter_participant(pseudo, "session_invalid")