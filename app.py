# Point d'entrée de l'application Flask
'''
 le fichier principal l'application Flask. 
 **Ce fichier va initialiser l'application Flask
 **configurer les routes
 **importer les autres modules 
 l'objet session de flask est un dictionnaire qui stocke toutes les données nécessaires pour ce projet:

'''

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
import numpy as np
import json

from models.app_manager import AppManager
import os
import uuid
from constantes import *

# Chemin vers le fichier backlog.json
#BACKLOG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'backlog.json')

# créer l'application Flask
app = Flask(__name__)

# Secret key pour le développement local
app.secret_key = CLE_SECRETE

app.config['SERVER_NAME'] = NOM_SERVEUR

# Initialisation d'AppManager avec chargement du backlog
app_manager = AppManager()

# les participants
participants = ["lina","hugo"]

# supprimer le cache du navigateur
@app.after_request
def add_header(response):
    """Désactiver le cache pour éviter les valeurs obsolètes."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# injecter les variables globales dans les templates 
@app.context_processor
def inject_globals():
    """
    Injecte les variables globales dans les templates.
    """
    session_id = request.cookies.get('session_id')
    user_data = app_manager.get_data_participant(session_id) if session_id else {}

    # Si user_data n'est pas défini ou est vide, injecter des valeurs par défaut
    if not user_data:
        return {
            'is_sm': False, # identifier le scrum master
            'is_po': False, # identifier le product ownner
        }

    # Sinon, injecter les valeurs réelles
    return {
        'is_sm': user_data.get('is_sm', False),
        'is_po': user_data.get('is_po', False),
    }


def get_user_data():
    """
    Vérifie la validité de la session et renvoie les données utilisateur actuelles.
    """
    # Récupérer le session_id depuis le cookie
    session_id = request.cookies.get('session_id')
    if not session_id:
        flash("Veuillez vous connecter.", "danger")
        return redirect(url_for('login'))

    # Appeler la méthode AppManager pour récupérer les données utilisateur
    user_data = app_manager.get_data_participant(session_id)
    print("user data " , user_data)
    print("session_id user data " , session_id)
    if not user_data:
        flash("Session invalide ou expirée.", "danger")
        return redirect(url_for('login'))

    return user_data

# Route par défaut
@app.route('/')
def home():
    """
    Point d'entrée de l'application.
    Redirige les utilisateurs en fonction de leur rôle et de leur état de connexion.
    """
    # Vérification et récupération des données utilisateur
    user_data = get_user_data()
    if isinstance(user_data, Response):  # Redirection si non connecté
        return user_data

    # Mise à jour des indicateurs globaux (injection pour les templates)
    is_sm = user_data.get('is_sm', False)
    is_po = user_data.get('is_po', False)
    session['is_sm'] = is_sm
    session['is_po'] = is_po
    session.modified = True
    return redirect(url_for('salle_de_vote'))

# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gestion de la connexion des participants.
    """
    if request.method == 'POST':
        pseudo = request.form['pseudo']
        
        # Générer un ID de session unique
        session_id = str(uuid.uuid4())  
        print("session_id login " , session_id)
              
        # Autoriser uniquement PO, SM ou participants dans le backlog
        if pseudo.lower() not in [PO.lower(), SM.lower()] and pseudo not in participants:
            flash(f"Le pseudo '{pseudo}' n'est pas autorisé à se connecter pour cette session.", "danger")
            return redirect(url_for('login'))
        
        try:
            app_manager.ajouter_participant(pseudo, session_id)
            print("session_id login :", session_id)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for('login'))

        # Enregistrer l'état de la session
        session['session_id'] = session_id        
        session.modified = True  # Marquer la session comme modifiée pour Flask
        
        # Stocker le session_id dans un cookie
        response = redirect(url_for('salle_de_vote'))
        response.set_cookie('session_id', session_id)  # Définir le cookie avec le session_id
        return response
        
        # Rediriger vers la salle de vote
        return redirect(url_for('salle_de_vote'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnexion de l'utilisateur."""
    session_id = request.cookies.get('session_id')

    if session_id:
        # Supprimer l'utilisateur de state["participants"] basé sur session_id
        app_manager.logout_participant(session_id)

    # Effacer la session Flask
    session.clear()
    
    # Rediriger vers la page de connexion
    return redirect(url_for('login'))

@app.route('/salle_de_vote')
def salle_de_vote():
    """
    Affiche la salle de vote pour les participants.
    """
    return render_template('salle_de_vote.html')

# Démarrer l'application Flask (le serveur en mode debbugage)
# Cela permet de recharger automatiquement le serveur lorsqu’il détecte des modifications dans le code, ce qui est pratique en développement.

if __name__ == '__main__':
    app.run(debug=True)
    
    
 
                
