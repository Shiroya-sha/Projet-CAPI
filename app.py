# -*- coding: utf-8 -*-

# Point d'entrée de l'application Flask
'''
@file
@brief Fichier principal de l'application Flask.

@details
Ce fichier initialise l'application Flask, configure les routes et importe les autres modules nécessaires.
L'objet session de Flask est utilisé pour stocker les données globales nécessaires à ce projet.
'''

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
import numpy as np
import json

from models.app_manager import AppManager
import os
import uuid
from constantes import *

# Chemin vers le fichier backlog.json
BACKLOG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'backlog.json')

# créer l'application Flask
app = Flask(__name__)

# Secret key pour le développement local
app.secret_key = CLE_SECRETE

# Configurer le nom du serveur
app.config['SERVER_NAME'] = NOM_SERVEUR

# création de l'objet AppManager avec chargement du backlog
app_manager = AppManager(backlog_file=BACKLOG_FILE)

# supprimer le cache du navigateur
@app.after_request
def add_header(response):
    """
    @brief Désactive le cache du navigateur.

    @param response La réponse HTTP générée par Flask.
    
    @return La réponse modifiée avec les en-têtes pour désactiver le cache.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# injecter les variables globales dans les templates 
@app.context_processor
def inject_globals():
    """
    @brief Injecte des variables globales dans les templates.

    @return Dictionnaire contenant les variables globales (is_sm et is_po).
    """
    # Récupérer le pseudo actif depuis la session
    pseudo_actif = session.get('pseudo_actif')
    participant_actif = None

    # Si un pseudo actif est défini, récupérer ses données
    if pseudo_actif:
        participant_actif = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo_actif), None)

    # Injecter les données dans les templates
    return {
        "pseudo_actif": pseudo_actif,
        "participant_actif": participant_actif,
        "state": app_manager.state,
    }

# Route par défaut
@app.route('/')
def home():
    """
    @brief Point d'entrée de l'application.

    @details Redirige les utilisateurs vers la page de connexion

    @return Redirection vers la page de connexion.
    """
    return redirect(url_for('login'))

# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    @brief Gestion de la connexion des participants.

    @details Cette route permet de se connecter avec un pseudo valide.
    Si le pseudo est valide, un ID de session unique est généré,
    et l'utilisateur est redirigé vers la salle de vote.

    @return Page de connexion ou redirection vers la salle 
    de vote après authentification.
    """
    if request.method == 'POST':
        pseudo = request.form['pseudo'].strip().lower()
        
        # Générer un ID de session unique
        session_id = str(uuid.uuid4())  
        print(f"Pseudo reçu : {pseudo}, Session ID généré : {session_id}")

         # Vérifier si le pseudo est valide
        fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
        participants_backlog = fonctionnalite_prioritaire.participants if fonctionnalite_prioritaire else []
        print("participants_backlog : ",participants_backlog)

       # Autoriser uniquement PO, SM ou participants du backlog
        if pseudo not in ["po","PO","sm", "SM"] and pseudo not in participants_backlog:
            flash(f"Le pseudo '{pseudo}' n'est pas autorisé à se connecter pour cette session.", "danger")
            return redirect(url_for('login'))
        
        try:
            app_manager.ajouter_participant(pseudo, session_id)
            # Stocker la session et rediriger vers la salle de vote
            session['session_id'] = session_id
            session.modified = True

            reponse = redirect(url_for('salle_de_vote'))
            reponse.set_cookie('session_id', session_id)
            return reponse
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# Route de déconnexion
@app.route('/logout')
def logout():
    """
    @brief Déconnecte tous les participants si le Scrum Master (SM) est actif.

    @details
    Cette fonction vérifie si le participant actif est le Scrum Master. Si c'est le cas, 
    tous les participants sont déconnectés, et leurs sessions sont effacées.
    Si le participant actif n'est pas le Scrum Master, un message de restriction est affiché, 
    et la redirection se fait vers la salle de vote.

    @return
    - Redirection vers la page de connexion si le Scrum Master déconnecte tout le monde.
    - Redirection vers la salle de vote avec un message d'avertissement sinon.
    """
    session_id = session.get('session_id')
    pseudo_actif = session.get('pseudo_actif')
    
    # Vérifier si le participant est le Scrum Master
    participant = next(
        (p for p in app_manager.state["participants"] if p["session_id"] == session_id),
        None
    )
    print("Participant trouvé : ", participant)

    if pseudo_actif == "sm":
        # Déconnecter tout le monde
        app_manager.state["participants"] = []
        app_manager.state["mapper_session"] = {}
        app_manager.sauvegarder_backlog()

        # Effacer toutes les sessions Flask
        session.clear()

        flash("Tous les participants ont été déconnectés par le Scrum Master.", "success")
        return redirect(url_for('login'))
    else:
        # Si ce n'est pas le Scrum Master, rester dans la salle de vote
        flash("Seul le Scrum Master peut déconnecter tout le monde.", "warning")
        return redirect(url_for('salle_de_vote'))

# Route de participants_debug
@app.route('/participants_debug')
def participants_debug():
    """
    @brief Retourne la liste des participants connectés pour le débogage.

    @details
    Cette fonction extrait la liste des participants actuellement connectés depuis l'état de l'application
    et la retourne au format JSON. Elle est principalement utilisée à des fins de diagnostic
    et de suivi des connexions.

    @return
    JSON contenant les informations sur les participants connectés.
    """
    participants = app_manager.state.get("participants", [])
    print(f"Participants connectés : {participants}")
    return jsonify(participants)

# Route de salle_de_vote
@app.route('/salle_de_vote')
def salle_de_vote():
    """
    @brief Affiche la salle de vote pour les participants connectés.

    @details
    Cette route permet d'accéder à la salle de vote. Elle vérifie si :
    - L'utilisateur est authentifié (présence d'une session valide).
    - La session correspond à un participant enregistré dans l'application.
    - Une fonctionnalité prioritaire est définie. Si ce n'est pas le cas, un message est affiché
      et l'utilisateur est redirigé vers le backlog.

    La vue inclut les informations suivantes :
    - Les participants connectés.
    - Les cartes de vote disponibles.
    - L'état de l'équipe et du vote en cours.

    @return
    - Page HTML de la salle de vote si toutes les vérifications sont réussies.
    - Redirection vers la page de connexion ou le backlog avec des messages en cas d'erreur.
    """
    session_id = session.get('session_id')
    if 'session_id' not in session:
        flash("Vous devez être connecté pour accéder à cette page.", "danger")
        return redirect(url_for('login')) 

    # Vérifier si le participant existe dans les données d'AppManager
    participant = next((p for p in app_manager.state["participants"] if p["session_id"] == session['session_id']), None)
    if not participant:
        flash("Session invalide ou expirée.", "danger")
        return redirect(url_for('login'))

    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire.", "warning")
        return redirect(url_for('backlog'))

    # Vérifier si l'équipe est complète
    equipe_complete = app_manager.is_team_complete(fonctionnalite_prioritaire)

    # Récupérer les participants connectés
    participants = app_manager.state["participants"]

    # Récupérer le pseudo actif
    pseudo_actif = session.get('pseudo_actif', None)

    # État du vote
    vote_commence = app_manager.state["indicateurs"]["vote_commence"]

    return render_template(
        'salle_de_vote.html',
        participants=participants,
        cartes=CARTES_VOTE,
        fonctionnalite=fonctionnalite_prioritaire,
        equipe_complete=equipe_complete,
        pseudo_actif=pseudo_actif,
        vote_commence=vote_commence
    )



# activation si on clique sur l'avatar
@app.route('/set_pseudo_actif', methods=['POST'])
def set_pseudo_actif():
    """
    @brief Définit le participant actif basé sur le pseudo sélectionné.

    @details
    Cette fonction est appelée lorsque l'utilisateur clique sur un avatar pour activer un participant.
    Elle effectue les étapes suivantes :
    - Vérifie si un pseudo a été envoyé via le formulaire.
    - Vérifie si le pseudo correspond à un participant existant dans l'état de l'application.
    - Définit le participant actif dans la session Flask si toutes les vérifications réussissent.

    En cas d'échec à une étape, l'utilisateur est redirigé vers la salle de vote avec un message d'erreur.

    @return
    - Redirection vers la salle de vote avec un message de succès si le pseudo est activé.
    - Redirection vers la salle de vote avec un message d'erreur en cas de problème.
    """
    pseudo = request.form.get("pseudo")  # Obtenu depuis le clic sur l'avatar
    if not pseudo:
        flash("Aucun pseudo sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Vérifier que le pseudo existe dans `state`
    participant = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo), None)

    if not participant:
        flash(f"Le participant '{pseudo}' n'existe pas.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Stocker le pseudo actif dans la session
    session['pseudo_actif'] = pseudo
    session.modified = True
    flash(f"{pseudo} est maintenant actif.", "success")
    return redirect(url_for('salle_de_vote'))


@app.route('/afficher_ajout_fonctionnalite')
def afficher_ajout_fonctionnalite():
    """
    @brief Affiche la page pour ajouter une nouvelle fonctionnalité.

    @details Accessible uniquement pour le Product Owner.
    Si aucun participant actif n'est sélectionné ou si le 
    participant actif n'est pas un Product Owner, un message 
    d'erreur est affiché et l'utilisateur est redirigé.

    @return La page HTML pour ajouter une fonctionnalité ou une redirection vers la salle de vote.
    """
    pseudo_actif = session.get('pseudo_actif')
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))
    

    participant_actif = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo_actif), None)
    
    if not participant_actif or participant_actif["fonction"] != "Product Owner":
        flash("Accès réservé au Product Owner.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Récupérer les données temporaires depuis la session
    participants_temp = session.get('participants_temp', [])  # Récupérer les participants temporaires ou liste vide
    form_data = session.get('form_data', {})

    return render_template(
        'ajout_fonctionnalite.html',
        form_data=form_data,
        participants_temp=participants_temp
    )



@app.route('/ajouter_fonctionnalite', methods=['POST'])
def ajouter_fonctionnalite():
    """
    @brief Ajoute une nouvelle fonctionnalité au backlog.

    @details Valide les données soumises via le formulaire d'ajout de fonctionnalité.
    Si les données sont valides, la fonctionnalité est ajoutée via AppManager.
    Sinon, des erreurs sont affichées et l'utilisateur reste sur la page d'ajout.

    @return Redirection vers le backlog ou la page d'ajout en cas d'erreur.
    """
    erreurs = {}
    pseudo_actif = session.get('pseudo_actif')
    if not pseudo_actif or pseudo_actif.lower() != "po":
        flash("Acces reserve au Product Owner", "danger")
        return redirect(url_for('salle_de_vote'))
    try:
        nom = request.form.get('nom', '').strip()
        description = request.form.get('description', '').strip()
        priorite = request.form.get('priorite', '').strip()
        difficulte = request.form.get('difficulte', '').strip()
        mode_de_vote = request.form.get('mode_de_vote', 'unanimite').strip()
        statut = request.form.get('statut', 'A faire').strip()
        participants = session.get('participants_temp', [])

        # Valider les données
        if not priorite.isdigit() or not (PRIORITE_MIN <= int(priorite) <= PRIORITE_MAX):
            erreurs['priorite'] = f"La priorité doit être comprise entre {PRIORITE_MIN} et {PRIORITE_MAX}."
        if not difficulte.isdigit() or not (DIFFICULTE_MIN <= int(difficulte) <= DIFFICULTE_MAX):
            erreurs['difficulte'] = f"La difficulté doit être comprise entre {DIFFICULTE_MIN} et {DIFFICULTE_MAX}."

        if erreurs:
            return render_template('ajout_fonctionnalite.html', errors=erreurs, form_data=request.form)

        print(f"nom {nom} description {description} int(priorite) {int(priorite)} int(difficulte) {int(difficulte)} mode_de_vote {mode_de_vote} statut {statut} participants {participants} ")
        
        # Ajouter la fonctionnalité via AppManager
        app_manager.ajout_fonctionnalite(nom, description, int(priorite), int(difficulte),statut, mode_de_vote,  participants)

        # Nettoyer les données temporaires
        session.pop('participants_temp', None)
        session.pop('form_data', None)

        flash("La fonctionnalité a été ajoutée avec succès.", "success")
        return redirect(url_for('backlog'))
    
    except Exception as e:
        flash("Une erreur est survenue lors de l'ajout de la fonctionnalité.", "danger")
        return redirect(url_for('afficher_ajout_fonctionnalite'))

@app.route('/ajouter_participant_route', methods=['POST'])
def ajouter_participant_route():
    """
    @brief Ajoute un participant temporaire à une fonctionnalité.

    @details Cette route permet d'ajouter un participant temporaire via le formulaire 
    d'ajout de fonctionnalité. Les données temporaires sont stockées dans la session.

    @return Redirection vers la page d'ajout de fonctionnalité.
    """
    pseudo = request.form.get('participant_pseudo', '').strip()
    print("participant ajouté dans fonctionnalité :", pseudo)

    # Initialiser la liste si elle n'existe pas
    if 'participants_temp' not in session:
        session['participants_temp'] = []
    
    if pseudo and pseudo not in session['participants_temp']:
        session['participants_temp'].append(pseudo)
        session.modified = True  # Marquer la session comme modifiée
        flash(f"Participant '{pseudo}' ajouté avec succès.", "success")
    else:
        flash("Le participant existe déjà ou aucun pseudo n'a été saisi.", "warning")
    
    # Conserver les autres données du formulaire
    session['form_data'] = {
        "nom": request.form.get('nom', '').strip(),
        "description": request.form.get('description', '').strip(),
        "priorite": request.form.get('priorite', '').strip(),
        "difficulte": request.form.get('difficulte', '').strip()
    }
    return redirect(url_for('afficher_ajout_fonctionnalite'))

@app.route('/edit_fonctionnalite_route/<int:fonctionnalite_id>', methods=['GET', 'POST'])
def edit_fonctionnalite_route(fonctionnalite_id):
    """
    @brief Modifie une fonctionnalité existante.

    @details Cette route affiche la page d'édition d'une fonctionnalité
    ou applique les modifications soumises via le formulaire.

    @param fonctionnalite_id L'identifiant de la fonctionnalité à modifier.

    @return Redirection vers le backlog ou la page d'édition.
    """
    # Récupérer la fonctionnalité à modifier via AppManager
    fonctionnalite = app_manager.get_fonctionnalite(fonctionnalite_id)
    if not fonctionnalite:
        flash("Fonctionnalité non trouvée.", "danger")
        return redirect(url_for('backlog'))
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            updated_data = {
                'nom': request.form['nom'].strip(),
                'description': request.form['description'].strip(),
                'priorite': request.form['priorite'].strip(),
                'difficulte': request.form['difficulte'].strip(),
                'mode_de_vote': request.form.get('mode_de_vote', fonctionnalite.mode_de_vote).strip(),
                'statut': request.form.get('statut', fonctionnalite.statut).strip(),
                'participants': request.form.getlist('participants[]')  # Liste des participants
            }

            # Déléguer la mise à jour à AppManager
            app_manager.modifier_fonctionnalite(fonctionnalite_id, **updated_data)

            flash("La fonctionnalité a été mise à jour avec succès.", "success")
            return redirect(url_for('backlog'))

        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash("Une erreur est survenue lors de la mise à jour de la fonctionnalité.", "danger")
            print(f"Erreur dans edit_fonctionnalite : {e}")

    # Charger la page avec les données actuelles de la fonctionnalité
    return render_template('edit_fonctionnalite.html', fonctionnalite=fonctionnalite)

@app.route('/supprimer_fonctionnalite_route/<int:fonctionnalite_id>', methods=['GET','POST'])
def supprimer_fonctionnalite_route(fonctionnalite_id):
    """
    @brief Supprime une fonctionnalité existante.

    @details Cette route permet de supprimer une fonctionnalité du backlog 
    en fonction de son identifiant.

    @param fonctionnalite_id L'identifiant de la fonctionnalité à supprimer.

    @return Redirection vers le backlog après suppression.
    """

    try:
        # Déléguer la suppression à AppManager
        app_manager.supprimer_fonctionnalite(fonctionnalite_id)
        flash("La fonctionnalité a été supprimée avec succès.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash("Une erreur est survenue lors de la suppression de la fonctionnalité.", "danger")
        print(f"Erreur dans supprimer_fonctionnalite : {e}")

    # Redirection vers le backlog
    return redirect(url_for('backlog'))


@app.route('/passer_a_fonctionnalite_suivante', methods=['POST'])
def passer_a_fonctionnalite_suivante():
    """
    @brief Permet au Product Owner de passer à la fonctionnalité suivante après validation.

    @details
    Cette fonction est accessible uniquement au Product Owner. Elle effectue les actions suivantes :
    - Vérifie que le participant actif est un Product Owner.
    - Recherche la prochaine fonctionnalité non terminée dans le backlog.
    - Met à jour l'état de l'application pour définir la fonctionnalité suivante comme prioritaire.
    - Sauvegarde le backlog.

    Si aucune fonctionnalité suivante n'est trouvée, un message d'avertissement est affiché.

    @return
    - Redirection vers la salle de vote avec un message de succès si une fonctionnalité suivante est trouvée.
    - Redirection vers la salle de vote avec un message d'avertissement si aucune fonctionnalité n'est disponible.
    """
    pseudo_actif = session.get('pseudo_actif')
    if pseudo_actif != 'po':
        flash("Accès réservé au Product Owner.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Récupérer la prochaine fonctionnalité non terminée dans le backlog
    prochaine_fonctionnalite = next(
        (f for f in app_manager.backlog if f.statut != "Terminé"), None
    )

    if prochaine_fonctionnalite:
        app_manager.state["id_fonctionnalite"] = prochaine_fonctionnalite.id
        app_manager.sauvegarder_backlog()
        flash(f"La fonctionnalité '{prochaine_fonctionnalite.nom}' est maintenant prioritaire.", "success")
    else:
        flash("Aucune fonctionnalité suivante disponible dans le backlog.", "warning")

    return redirect(url_for('salle_de_vote'))



@app.route('/soumettre_vote', methods=['POST'])
def soumettre_vote():
    """
    @brief Enregistre un vote pour la fonctionnalité prioritaire dans la structure state.

    @details
    Cette fonction gère l'enregistrement des votes pour une fonctionnalité prioritaire. Elle réalise les étapes suivantes :
    - Vérifie que le vote a été initié par le Scrum Master.
    - Vérifie que le participant existe et qu'il n'a pas encore voté.
    - Imposent des restrictions de vote pour le Product Owner et le Scrum Master (carte café uniquement).
    - Enregistre le vote et met à jour l'état global en fonction des votes collectés.

    Gestion spécifique :
    - Si un participant vote "?", l'indicateur de discussion active est activé.
    - Si tous les participants votent "café", l'état de pause est activé.
    - Si tous les participants ont voté, un indicateur est mis à jour pour le signaler.

    @return
    Redirection vers la salle de vote avec un message approprié :
    - Succès si le vote est enregistré.
    - Erreur ou avertissement si des conditions ne sont pas respectées.
    """
    pseudo = request.form.get("pseudo")
    vote = request.form.get("vote")
    
    # Vérifier si le vote a été initié par le SM
    if not app_manager.state["indicateurs"]["vote_commence"]:
        flash("Le vote n'a pas encore été initié par le Scrum Master.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Vérifier que le participant existe
    participant = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo), None)
    if not participant:
        flash(f"Participant {pseudo} non trouvé.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Vérifier si le participant a déjà voté
    if participant["vote"] is not None:
        flash(f"{pseudo} a déjà voté.", "warning")
        return redirect(url_for('salle_de_vote'))
    
    # Vérifier les restrictions pour PO et SM (carte café uniquement)
    if participant["fonction"] in ["Product Owner", "Scrum Master"] and vote != "cafe":
        flash(f"{pseudo} ne peut voter que pour la carte café.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Enregistrer le vote
    participant["vote"] = vote

    # Gestion spéciale pour la carte "?"
    if vote == "?":
        app_manager.state["indicateurs"]["discussion_active"] = True
        flash("Un participant a voté '?'. Une discussion est nécessaire.", "warning")
        return redirect(url_for('salle_de_vote'))
    
    # Vérifier si tout les Votants ont voté
    participants_votants = [
        p for p in app_manager.state["participants"] if p["fonction"] == "Votant"
    ]
    
    # Vérifier si tout le monde a voté
    all_participants = app_manager.state["participants"]  # Tous les participants, y compris SM et PO
    
    if all(p["vote"] == "cafe" for p in all_participants):
        app_manager.sauvegarder_backlog("backlog_pause.json")
        flash("Tous les joueurs ont choisi la carte café. La réunion est suspendue.", "info")
        app_manager.state["indicateurs"]["pause_cafe"] = True
    else:
        app_manager.state["indicateurs"]["tout_le_monde_a_vote"] = True
        flash("Tous les participants ont voté.", "info")
    
   
    return redirect(url_for('salle_de_vote'))





@app.route('/acces_sm')
def acces_sm():
    """@brief Accès pour le Scrum Master à la gestion des votes.

    @details
    Cette fonction est réservée au Scrum Master et permet de gérer les votes pour la fonctionnalité prioritaire. 
    Les étapes principales sont :
    - Vérification que le participant actif est le Scrum Master.
    - Récupération de la fonctionnalité prioritaire.
    - Identification des participants attendus, connectés et manquants.
    - Vérification de l'état des votes (tout le monde a voté, votes révélés, fonctionnalité approuvée).

    La vue `acces_sm.html` affiche les informations suivantes :
    - La fonctionnalité prioritaire.
    - Les votes (révélés ou non).
    - Les participants attendus, connectés et manquants.
    - L'état des boutons pour les actions (vote, révélation, etc.).
    - L'état d'approbation de la fonctionnalité.

    @return
    - La page HTML `acces_sm.html` avec toutes les données nécessaires.
    - Redirection vers la salle de vote ou le backlog avec un message en cas de problème.
    """
    # Vérifier le pseudo actif dans la session
    pseudo_actif = session.get('pseudo_actif')
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Vérifier que le participant actif est le Scrum Master
    participant_actif = next((p for p in app_manager.state["participants"] if p["pseudo"] == pseudo_actif), None)
    if not participant_actif or participant_actif["fonction"].lower() != "scrum master":
        flash("Accès réservé au Scrum Master.", "danger")
        return redirect(url_for('salle_de_vote'))

    # Récupérer la fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire disponible.", "warning")
        return redirect(url_for('backlog'))

    # Récupérer les participants attendus
    participants_attendus = app_manager.participants_backlog(fonctionnalite_prioritaire.id)

    # Récupérer les participants connectés
    participants_connectes = [
        participant["pseudo"]
        for participant in app_manager.state["participants"]
        if participant["fonction"] == "Votant"
    ]

    # Calculer les participants manquants
    difference = set(participants_attendus) - set(participants_connectes)
    bouton_actif = len(difference) == 0  # Activer le bouton si tous les participants sont connectés

    # Vérifier si tout le monde a voté
    tout_le_monde_a_vote = app_manager.tout_le_monde_a_vote()
    votes_reveles = app_manager.state["indicateurs"]["votes_reveles"]
    if votes_reveles:
        votes = app_manager.reveler_votes()
    else:
        votes = {}
    
    # Vérifier si la fonctionnalité est approuvée
    fonctionnalite_approuvee = app_manager.state["indicateurs"].get("fonctionnalite_approuvee", False)
    print("fonctionnalite_approuvee", fonctionnalite_approuvee)
    
    return render_template(
        'acces_sm.html',
        fonctionnalite=fonctionnalite_prioritaire,
        votes=votes,
        pseudo_actif=pseudo_actif,
        participant_actif=participant_actif,
        participants_attendus=participants_attendus,
        participants_connectes=participants_connectes,
        difference=list(difference),
        bouton_actif=bouton_actif,
        tout_le_monde_a_vote=tout_le_monde_a_vote,
        votes_reveles=votes_reveles,
        fonctionnalite_approuvee=fonctionnalite_approuvee
    )


@app.route('/faciliter_discussion', methods=['POST'])
def faciliter_discussion():
    """@brief Permet au Scrum Master de faciliter une discussion.

    @details
    Cette fonction est utilisée pour activer une discussion sur une fonctionnalité prioritaire.
    Elle vérifie que le participant actif est le Scrum Master et qu'une fonctionnalité prioritaire est définie.
    Une fois ces conditions remplies, l'indicateur global `discussion_active` est activé pour signaler
    qu'une discussion est en cours.

    @conditions
    - Le participant actif doit être le Scrum Master.
    - Une fonctionnalité prioritaire doit être définie.

    @actions
    - Si toutes les conditions sont respectées, l'indicateur `discussion_active` est activé.
    - Des messages appropriés sont affichés en cas de succès ou d'erreur.

    @return
    - Redirection vers la page d'accès Scrum Master (`acces_sm`) avec un message d'information en cas de succès.
    - Redirection vers la salle de vote ou la page d'accès Scrum Master avec un message d'erreur en cas de problème.
    """
    pseudo_actif = session.get('pseudo_actif').strip()
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    if pseudo_actif != 'sm':
        flash(ACCES_RESERVE_SM, "danger")
        return redirect(url_for('acces_sm'))


    # Vérification d'une fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire disponible pour initier la discussion.", "danger")
        return redirect(url_for('acces_sm'))

    # Marquer la discussion comme active dans l'indicateur global
    app_manager.state["indicateurs"]["discussion_active"] = True
    flash("Discussion initiée avec succès. Invitez les participants à échanger.", "info")
    return redirect(url_for('acces_sm'))

@app.route('/valider_vote', methods=['POST'])
def valider_vote():
    """

    @brief Valide les votes enregistrés pour la fonctionnalité active.

    @details
    Cette fonction permet au Scrum Master de valider les votes pour la fonctionnalité prioritaire.
    Elle effectue les étapes suivantes :
    - Vérifie que le participant actif est le Scrum Master.
    - Vérifie que tous les participants votants ont soumis leurs votes.
    - Récupère la fonctionnalité prioritaire et applique les règles de validation selon son mode de vote :
      - **Unanimité** : Tous les votes doivent être identiques.
      - **Moyenne** : La carte la plus proche de la moyenne des votes est choisie.
    - Met à jour l'état de la fonctionnalité (approuvée ou non).
    - Trie et sauvegarde le backlog.
    - Passe automatiquement à la fonctionnalité suivante si disponible.

    @conditions
    - Seul le Scrum Master peut valider les votes.
    - Tous les participants doivent avoir voté pour procéder à la validation.

    @return
    - Redirection vers la page d'accès Scrum Master avec un message de succès si le vote est validé.
    - Redirection avec un message d'erreur ou d'avertissement si une condition n'est pas respectée.
    """
    pseudo_actif = session.get('pseudo_actif')
    if pseudo_actif != "sm":
        flash("Seul le Scrum Master peut valider le vote.", "danger")
        return redirect(url_for('acces_sm'))

    # Récupérer les votes des participants votants
    participants_votants = [
        p for p in app_manager.state["participants"] if p["fonction"] == "Votant"
    ]
    votes = [p["vote"] for p in participants_votants]

    if not votes or any(vote is None for vote in votes):
        flash("Tous les participants n'ont pas voté.", "warning")
        return redirect(url_for('acces_sm'))

    # Récupérer la fonctionnalité prioritaire et son mode de vote
    fonctionnalite_id = app_manager.state.get('id_fonctionnalite')
    if not fonctionnalite_id:
        flash("Aucune fonctionnalité prioritaire sélectionnée.", "danger")
        return redirect(url_for('acces_sm'))

    fonctionnalite = app_manager.get_fonctionnalite(fonctionnalite_id)
    if not fonctionnalite:
        flash("Fonctionnalité introuvable.", "danger")
        return redirect(url_for('acces_sm'))

    mode_de_vote = fonctionnalite.mode_de_vote

    # Gestion des différents modes de vote
    if mode_de_vote == "unanimite":
        # Vérifier si tous les votes sont identiques
        if len(set(votes)) == 1:
            app_manager.state["indicateurs"]["fonctionnalite_approuvee"] = True
            fonctionnalite.statut = "Terminé"
            flash(f"Vote validé avec succès. Résultat : {votes[0]}.", "success")
        else:
            app_manager.state["indicateurs"]["fonctionnalite_approuvee"] = False
            flash("Vote non approuvé. Tous les participants doivent voter la même carte.", "warning")

    elif mode_de_vote == "moyenne":
        # Calcul de la moyenne et carte la plus proche (déjà implémentée)
        moyenne = sum(int(v) for v in votes if v.isdigit()) / len(votes)
        carte_proche = min(LISTE_CARTE_NUMERIQUE, key=lambda x: abs(int(x) - moyenne))
        app_manager.state["indicateurs"]["fonctionnalite_approuvee"] = True
        fonctionnalite.statut = "Terminé"
        flash(f"Vote validé avec succès. Résultat (moyenne) : {carte_proche}.", "success")

    else:
        flash(f"Mode de vote inconnu : {mode_de_vote}.", "danger")
        return redirect(url_for('acces_sm'))

    # Trier et sauvegarder le backlog
    app_manager.trier_backlog()
    app_manager.sauvegarder_backlog()

    # Passer à la fonctionnalité suivante (si disponible)
    prochaine_fonctionnalite = next(
        (f for f in app_manager.backlog if f.statut != "Terminé"), None
    )
    if prochaine_fonctionnalite:
        app_manager.state["id_fonctionnalite"] = prochaine_fonctionnalite.id
        flash(f"Passage à la fonctionnalité suivante : {prochaine_fonctionnalite.nom}.", "info")
    else:
        flash("Aucune autre fonctionnalité disponible dans le backlog.", "warning")

    return redirect(url_for('acces_sm'))



@app.route('/reveler_votes', methods=['POST'])
def reveler_votes():
    """@brief Révèle les votes pour la fonctionnalité prioritaire.

    @details
    Cette fonction est utilisée pour révéler les votes soumis par les participants pour une fonctionnalité prioritaire.
    Elle effectue les étapes suivantes :
    - Vérifie que le participant actif est le Scrum Master.
    - Vérifie qu'une fonctionnalité prioritaire est définie.
    - Révèle les votes associés à la fonctionnalité prioritaire en cours via la méthode `reveler_votes` de `AppManager`.

    Si toutes les conditions sont remplies, les votes sont révélés et un message de succès est affiché. 
    En cas de problème, un message d'erreur ou d'avertissement est affiché.

    @conditions
    - Le participant actif doit être le Scrum Master.
    - Une fonctionnalité prioritaire doit être définie.

    @return
    - Redirection vers la page d'accès Scrum Master (`acces_sm`) avec un message de succès si les votes sont révélés.
    - Redirection avec un message d'erreur ou d'avertissement en cas de problème.
    """
    pseudo_actif = session.get('pseudo_actif').strip()
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))

    if pseudo_actif != 'sm':
        flash(ACCES_RESERVE_SM, "danger")
        return redirect(url_for('acces_sm'))

    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire trouvée pour révéler les votes.", "danger")
        return redirect(url_for('acces_sm'))

    # Récupérer les votes pour la fonctionnalité en cours
    """  votes = app_manager.state.get("votes", {}).get(fonctionnalite_prioritaire.id, {})
    if not votes:
        flash("Aucun vote à révéler pour la fonctionnalité prioritaire.", "warning")
        return redirect(url_for('acces_sm')) """

    # Révéler les votes via AppManager
    votes_reveles = app_manager.reveler_votes()
    if votes_reveles:
        flash("Votes révélés avec succès.", "success")
    else:
        flash("Problème lors de la révélation des votes.", "danger")

    return redirect(url_for('acces_sm'))

@app.route('/initier_vote', methods=['POST'])
def initier_vote():
    """@brief Démarre le vote pour la fonctionnalité prioritaire.

    @details
    Cette fonction est utilisée pour initier un vote pour la fonctionnalité prioritaire. 
    Elle effectue les étapes suivantes :
    - Vérifie que le participant actif est défini.
    - Vérifie qu'une fonctionnalité prioritaire est sélectionnée.
    - Vérifie que l'équipe est complète, c'est-à-dire que tous les participants nécessaires sont connectés.
    - Déclenche le vote via la méthode `initier_vote` de `AppManager` et met à jour l'indicateur global `vote_commence`.

    Si toutes les conditions sont respectées, le vote est initié et un message de succès est affiché.
    En cas d'erreur, un message d'erreur ou d'avertissement est affiché.

    @conditions
    - Un participant actif doit être défini dans la session.
    - Une fonctionnalité prioritaire doit être sélectionnée.
    - Tous les participants nécessaires doivent être connectés.

    @return
    - Redirection vers la page d'accès Scrum Master (`acces_sm`) avec un message de succès si le vote est initié.
    - Redirection avec un message d'erreur ou d'avertissement en cas de problème.
    """
    pseudo_actif = session.get('pseudo_actif')
    print("pseudo actif dans acces sm ",pseudo_actif )
    if not pseudo_actif:
        flash("Aucun participant actif sélectionné.", "danger")
        return redirect(url_for('salle_de_vote'))
    
    pseudo_actif = pseudo_actif.strip()

    # Vérification d'une fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire trouvée pour initier le vote.", "danger")
        return redirect(url_for('acces_sm'))

    # Vérification de l'équipe complète
    if not app_manager.is_team_complete(fonctionnalite_prioritaire):
        flash("Tous les participants nécessaires ne sont pas encore connectés.", "warning")
        return redirect(url_for('acces_sm'))

    # Initialisation du vote via AppManager
    try:
        app_manager.initier_vote(fonctionnalite_prioritaire.id)
        app_manager.state["indicateurs"]["vote_commence"] = True
        flash("Le vote a été initié avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de l'initiation du vote : {e}", "danger")

    return redirect(url_for('acces_sm'))

@app.route('/reinitialiser_vote', methods=['POST'])
def reinitialiser_vote():   
    """
    @brief Réinitialise tous les votes et remet l'état global à jour.

    @details
    Cette fonction est utilisée pour réinitialiser les votes et restaurer l'état global de l'application.
    Elle effectue les étapes suivantes :
    - Vérifie qu'une fonctionnalité prioritaire est définie.
    - Appelle la méthode `reinitialiser_votes` de `AppManager` pour réinitialiser les votes.
    - Réinitialise les indicateurs globaux à leurs valeurs par défaut (ex. vote non commencé, discussion inactive, etc.).

    En cas de succès, un message d'information est affiché pour signaler la réinitialisation des votes. 
    Si une erreur se produit, un message d'erreur est affiché.

    @conditions
    - Une fonctionnalité prioritaire doit être définie pour procéder à la réinitialisation.

    @actions
    - Réinitialise les votes des participants.
    - Réinitialise les indicateurs de l'état global.

    @return
    - Redirection vers la page d'accès Scrum Master (`acces_sm`) avec un message de succès ou d'erreur selon le cas.
    """
    # Vérification d'une fonctionnalité prioritaire
    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire trouvée pour réinitialiser les votes.", "danger")
        return redirect(url_for('acces_sm'))

    # Réinitialisation des votes via AppManager
    try:
        app_manager.reinitialiser_votes()
        # Réinitialiser les indicateurs pour revenir à l'état initial
        app_manager.state["indicateurs"]["vote_commence"] = False
        app_manager.state["indicateurs"]["votes_reveles"] = False
        app_manager.state["indicateurs"]["tout_le_monde_a_vote"] = False
        app_manager.state["indicateurs"]["discussion_active"] = False
        app_manager.state["indicateurs"]["pause_cafe"] = False
        app_manager.state["indicateurs"]["fonctionnalite_approuvee"] = False

        flash("Les votes ont été réinitialisés avec succès.", "info")
    except Exception as e:
        flash(f"Erreur lors de la réinitialisation des votes : {e}", "danger")

    return redirect(url_for('acces_sm'))


@app.route('/charger_backlog_pause', methods=['GET'])
def charger_backlog_pause():
    """
    @brief Charge le backlog spécifique à la pause café.

    @details
    Cette fonction charge un fichier de backlog spécifique, `backlog_pause.json`, 
    pour restaurer l'état de la pause café. Elle effectue les étapes suivantes :
    - Appelle la méthode `charger_backlog` de `AppManager` pour charger le fichier.
    - Affiche un message de succès si le chargement est réussi.
    - Affiche un message d'erreur en cas d'échec du chargement.

    @return
    - Redirection vers la salle de vote (`salle_de_vote`) avec un message de succès si le fichier est chargé correctement.
    - Redirection avec un message d'erreur en cas de problème lors du chargement.
    """
    try:
        app_manager.backlog = app_manager.charger_backlog("backlog_pause.json")
        flash("Backlog de la pause café chargé avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors du chargement du backlog de la pause café : {e}", "danger")
    return redirect(url_for('salle_de_vote'))


@app.route('/backlog')
def backlog():
    """
    @brief Affiche le backlog des fonctionnalités.

    @details Cette route retourne une vue contenant 
    toutes les fonctionnalités du backlog.

    @return La page HTML du backlog.
    """
    app_manager.trier_backlog()  #  backlog trié
    app_manager.sauvegarder_backlog()
    backlog = app_manager.lister_backlog()
    return render_template('backlog.html', backlog=backlog)

# Démarrer l'application Flask (le serveur en mode debbugage)
if __name__ == '__main__':
    app.run(debug=True)