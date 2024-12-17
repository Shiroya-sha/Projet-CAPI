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

# Fonction utilitaire pour récupérer les données utilisateur
def get_user_data():
    """
    @brief Vérifie la validité de la session et retourne les données utilisateur.
    @return Les données utilisateur si la session est valide, sinon redirection vers login.
    """
    session_id = session.get('session_id')
    if not session_id:
        flash("Veuillez vous connecter.", "danger")
        return redirect(url_for('login'))

    
    # Récupérer les données du participant via AppManager
    participant = next((p for p in app_manager.state["participants"] if p["session_id"] == session_id), None)
    if not participant:
        flash("Session invalide ou expirée.", "danger")
        return redirect(url_for('login'))

    # Retourner les données du participant
    return participant

# Route par défaut
@app.route('/')
def home():
    """
    @brief Point d'entrée de l'application.
    Redirige les utilisateurs vers la page de connexion
    @return Redirection vers la page de connexion.
    """
    return redirect(url_for('login'))

# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    @brief Gestion de la connexion des participants.
    @return Page de connexion ou redirection vers la salle de vote après authentification.
    """
    if request.method == 'POST':
        pseudo = request.form['pseudo'].strip().lower()
        
        # Générer un ID de session unique
        session_id = str(uuid.uuid4())  
        print("session_id login ", session_id)

         # Vérifier si le pseudo est valide
        fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
        participants_backlog = fonctionnalite_prioritaire.participants if fonctionnalite_prioritaire else []
              
       # Autoriser uniquement PO, SM ou participants du backlog
        if pseudo not in ["po", "sm"] and pseudo not in participants_backlog:
            flash(f"Le pseudo '{pseudo}' n'est pas autorisé à se connecter pour cette session.", "danger")
            return redirect(url_for('login'))
        
        try:
            app_manager.ajouter_participant(pseudo, session_id)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for('login'))

        # Stocker la session et rediriger vers la salle de vote
        session['session_id'] = session_id
        session.modified = True
        response = redirect(url_for('salle_de_vote'))
        response.set_cookie('session_id', session_id)
        return response

    return render_template('login.html')

# Route de déconnexion
@app.route('/logout')
def logout():
    """
    @brief Déconnecte un utilisateur.

    @return Redirection vers la page de connexion.
    """
    session_id = request.cookies.get('session_id')

    if session_id:
        # Supprimer l'utilisateur de state["participants"] basé sur session_id
        app_manager.logout_participant(session_id)

    # Effacer la session Flask
    session.clear()
    
    # Rediriger vers la page de connexion
    return redirect(url_for('login'))

# Route pour la salle de vote
@app.route('/salle_de_vote')
def salle_de_vote():
    """
    @brief Affiche la salle de vote pour les participants connectés.
    @return La page HTML de la salle de vote.
    """
    user_data = get_user_data()
    if not user_data:
        # Si aucune donnée utilisateur n'est retournée, rediriger vers la salle de vote
        return redirect(url_for('login'))

    fonctionnalite_prioritaire = app_manager.afficher_fonctionnalite_prioritaire()
    if not fonctionnalite_prioritaire:
        flash("Aucune fonctionnalité prioritaire.", "warning")
        return redirect(url_for('backlog'))

    # Récupérer les participants connectés
    participants = app_manager.state["participants"]
 
    # Récupérer le pseudo actif
    pseudo_actif = session.get('pseudo_actif', None)
    
    return render_template(
        'salle_de_vote.html',
        participants=participants,
        cartes=CARTES_VOTE,
        fonctionnalite=fonctionnalite_prioritaire,
        pseudo_actif=pseudo_actif,
    )

# activation si on clique sur l'avatar
@app.route('/set_pseudo_actif', methods=['POST'])
def set_pseudo_actif():
    """
    Définit le participant actif basé sur le pseudo sélectionné.
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

@app.route('/backlog')
def backlog():
    # Page de gestion du backlog.
    #user_data = get_user_data()
    # if not user_data['is_po']:
    #     flash(ACCES_RESERVE_PO, "danger")
    #     return redirect(url_for('salle_de_vote')) """ """ """ """

    # Récupérer le pseudo actif depuis la session
    #pseudo_actif = session.get('pseudo_actif')
    
    backlog = app_manager.lister_backlog()
    return render_template('backlog.html', backlog=backlog)



@app.route('/afficher_ajout_fonctionnalite')
def afficher_ajout_fonctionnalite():
    """
    Affiche la page pour ajouter une nouvelle fonctionnalité.
    Accessible uniquement pour le Product Owner.
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
    erreurs = {}
    pseudo_actif = session.get('pseudo_actif')
    if not pseudo_actif or pseudo_actif.lower() != "po":
        flash("Accès réservé au Product Owner.", "danger")
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

# Démarrer l'application Flask (le serveur en mode debbugage)
if __name__ == '__main__':
    app.run(debug=True)