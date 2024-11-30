# Point d'entrée de l'application Flask
'''
 le fichier principal de votre application Flask. 
 **Ce fichier va initialiser l'application Flask
 **configurer les routes
 **importer les autres modules 
 ce fichier doit rester propre et mettre toutes les routes dans le fichier routes.py
 
 l'objet session de flask est un dictionnaire qui stocke toutes les données nécessaires pour ce projet:
 exemple:
 session = {
    '_flashes': [('message', 'rtrtrt a voté pour la 8'), ('message', 'bcgd a voté pour la 8')], 
    'tout_le_monde_a_vote': True, 
    'votant_actuel': None, 
    'participants': ['rtrtrt', 'bcgd', 'sds'], 
    'votes': {'bcgd': '8', 'rtrtrt': '8', 'sds': None}}>
 }
'''
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import numpy as np
import json
from models.fonctionnalites import Fonctionnalites

# créer l'application Flask
app = Flask(__name__)

# Secret key simple pour le développement local
app.secret_key = "dev_mdp_123" 

app.config['SERVER_NAME'] = '127.0.0.1:5000'

# liste des participants
#participants = []

fonctionnalites = []  #   Sera chargé depuis backlog.json dans une version complète

@app.after_request
def add_header(response):
    # Forcer le navigateur à ne pas utiliser de cache
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


# page index
@app.route('/')
def index():
    #return render_template('index.html')
    # initialisation
    if "participants" not in session:
        session["participants"] = [] #liste de participants
    
    session['votes'] = {
                participant : None for participant in session['participants']
            }
    if "votant_actuel" not in session:
            session["votant_actuel"] = None
        
    if "tout_le_monde_a_vote" not in session:
        session["tout_le_monde_a_vote"] = False

        # initialisation de l'acte de révéler le vote par le PO
    if "revelerVote" not in session:
        session["revelerVote"] = False
         
            
    return render_template('login.html')
 

# page de login
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
    
        pseudo = request.form['pseudo']
        
        if pseudo == "PO":  # identifier le PO
            session['is_po'] = True
        else:
            session['is_po'] = False
            
        # ajouter le participant à la session
        if pseudo not in session["participants"] and pseudo != 'PO':
            session["participants"].append(pseudo)
        
        print(session['participants'])
        

        
        # Conserver les modifications de la session
        session.modified = True  # Important pour sauvegarder les modifications
        
        
        return index()
    
    else:         
    
        # Si la méthode est GET, on affiche  la page de login
        return render_template('login.html')
        #return render_template('home.html') 

@app.route('/logout')
def logout():
    
     # Réinitialiser la liste des participants globale
    global participants
    participants = []  # Vider la liste des participants
    session.clear()
    session.modified = True  # Indiquer que la session a été modifiée
    print("maaaaaaa session ", session)
    return index()

@app.route('/home', methods=['POST','GET'])
def home():
    pass

@app.route('/backlog_produit', methods=['POST','GET'])
def backlog_produit():
    pass

# Démarrer l'application Flask (le serveur en mode debbugage)
# Cela permet de recharger automatiquement le serveur lorsqu’il détecte des modifications dans le code, ce qui est pratique en développement.

if __name__ == '__main__':
    app.run(debug=True)
    
    
 
                
