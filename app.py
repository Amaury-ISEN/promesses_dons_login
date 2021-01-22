# Pour gérer le print à des fins de debugging :
from __future__ import print_function
import sys

# Import du module re pour regarder les expressions régulières et vérifier que le mail saisi est correct : 
import re

from data import *

# Si on run directement via le présent script, il faut installer importer SSL :
# import SSL

from flask import Flask, render_template, request, redirect, flash, url_for, session
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash


from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Length

from flask_sqlalchemy import SQLAlchemy

# Création de l'app flask à partir du présent script :
app = Flask(__name__)
# Création de la clé secrète, nécessaire entre autre aux messages flask() :
# La lettre b avant le string signifie qu'on créée un Byte literal (ASCII uniquement)
app.config['SECRET_KEY'] = b'_5#y2L"F4Q8z\n\xec]/'
# Configuration de l'URI pour la db d'utilisateurs :
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///C:/Users/utilisateur/Documents/microsoft_ia/Projets individuels/Promesse_de_don_login/login.db"
# Clé de configuration pour pratiquer la redirection "next" dans la route de login.
app.config['USE_SESSION_FOR_NEXT'] = True

# Instanciation de la BDD d'utilisateurs :
db = SQLAlchemy(app)

# Instanciation du gestionnaire de login et affectation de notre app :
login_manager = LoginManager()
login_manager.init_app(app)
# Setting de la login view càd la page de login qui est appelée en cas de login required si on est pas logué, par ex.
login_manager.login_view='login'
# Personnalisation du message flask flash par défaut quand une page requiert de se connecter : 
login_manager.login_message = u"Veuillez vous connecter pour accéder à cette page."


# Création d'une classe qui définit le contenu du formulaire de login :
class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Se rappeler de moi')

# Création d'une classe User pour les objets utilisateurs, la classe hérite de UserMixin pour avoir tous les attributs nécessaires :
# db.Model est la classe de base pour les modèles SQLAlchemy, elle est stockée dans l'instance SQLAlchemy.
class User(UserMixin, db.Model):
    # (Il faut que l'id s'appelle "id" sinon UserMixin ne fonctionne pas bien au niveau du get_id().)
    # On crée les colonnes/attributs de notre table d'utilisateurs :
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(50))
    priviledge = db.Column(db.String(30))

@login_manager.user_loader
@app.route('/turlututu')
def load_user(user_id):
    """Retourne l'objet python SQLAlchemy utilisateur qui correspond à l'id passé en paramètre user_id."""
    return User.query.get(int(user_id))


@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/sign_up')
def sign_up():
    return render_template("sign_up.html")


# La route utilisée lors de la validation du form dans la page sign up :
@app.route('/signMeUp', methods=['POST'])
def signMeUp():
    # Création de la table "user" dans la database "login.db" sur la base du modèle défini dans la classe User grâce au create_all() :
    db.create_all()

    username = request.form['username']
    password = request.form['password']

    # Vérification que le nom d'utilisateur est libre :
    user = User.query.filter_by(username=username).first()
    if user:
        return "Veuillez choisir un autre nom."

    # Création d'un objet utilisateur :
    utilisateur = User(username = username, password = password, priviledge = "Admin")

    # Ajout de l'utilisateur en base et commit :
    db.session.add(utilisateur)
    db.session.commit()
    db.session.close()

    return "Vous êtes inscrit et pouvez vous connecter !"

# La route utilisée lors de l'inscrimtion dans la page log in :
@app.route('/logMeIn', methods=['POST'])
def logMeIn():
    se_rappeler = True
    username = request.form['username']
    password = request.form['password']

    # On récupère l'objet utilisateur qui correspond aux infos renseignées par l'utilisateur dans le formulaire HTML :
    user = User.query.filter_by(username=username, password=password).first()

    # Si l'utilisateur n'est pas trouvé avec les infos renseignées en formulaire, on retourne un message d'erreur :
    if not user:
        return "<h1>Cet utilisateur n'a pas été trouvé.</h1>"

    login_user(user, remember=se_rappeler)

    # Si next est dans la session on affecte sa valeur à une variable next pour pouvoir faire la redirection après login :
    if 'next' in session:
        next = session['next']
        # Redirection vers l'url next :
        return redirect(next)

    return "Vous êtes connecté, "+str(current_user.username)+" !"


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "Vous êtes déconnecté !"

##############
##  ROUTES  ##
##############

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/promesse_don')
def promesse_don():
    return render_template('promesse_don.html')

@app.route('/recapitulatif')
@login_required
def recapitulatif():
    """Page de récapitulatif des dons."""
    promesses = recup_promesses_base()
    total = 0
    for p in promesses:
        total += p['somme']
    return render_template('recapitulatif.html', promesses=promesses, total=total)


@app.route('/gestion_formulaire', methods=['POST'])
def gestion_formulaire():
    """Méthode de gestion des inputs du formulaire avec récupération et vérification de leur contenu et appel de la méthode d'envoi en base."""

    # Création du dictionnaire qui va recueillir le contenu des champs renseignés par l'utilisateur :
    dico = {"nom":'', "prenom":'', "adresse":'', "mail":'', "somme":''}
    
    # Remplissage :
    dico["nom"] = request.form.get('nom')
    dico["prenom"] = request.form.get('prenom')
    dico["adresse"] = request.form.get('adresse')
    dico["mail"] = request.form.get('mail')
    dico["somme"] = request.form.get('somme')

    # Tous les tests suivants peuvent paraître redondants avec les attributs HTML des inputs dans promesse_don.html mais ça
    # évite les risques de piratage et d'envoi de mauvaises données par modification du code HTML de la page.
      
    # Récupération de l'état de la case à cocher CGU :
    CGUAcceptees = request.form.get('CGUAcceptees')

    # Nativement, une checkbox html renvoie le string "on" si elle est cochée, sinon elle renvoie None :
    if CGUAcceptees != "on":
        flash("Veuillez accepter les CGU.")
        return render_template('promesse_don.html')

    # Vérif qu'aucun champ ne contient un string vide :
    if '' in dico.values():
        print(dico)
        flash("Veuillez remplir tous les champs.")
        return render_template('promesse_don.html')

    # Vérification que le mail est ok avec le module re, la méthode match renvoie None si le pattern n'est pas reconnu :
    if re.match(r"[^@]+@[^@]+\.[^@]+", dico["mail"]) == None:
        flash("Veuillez renseigner une adresse mail valide.")
        return render_template('promesse_don.html')

    # Vérif que la somme est bien un nombre :
    if dico["somme"].isnumeric() == False:
        flash("Veuillez renseigner un nombre sans espace pour le montant du don.")
        return render_template('promesse_don.html')

    elif dico["somme"] < 1:
        flash("Veuillez renseigner un nombre positif.")
        return render_template('promesse_don.html')

    else:
        # Troncation du nombre en le passant en int, on pourrait aussi utiliser le module maths pour garder 2 décimales :
        dico["somme"] = int(dico["somme"])
    
    # Si l'interpréteur arrive jusqu'ici, c'est que toutes les conditions sont ok pour envoi en base :
    
    envoi_promesse_base(dico)
    flash("Votre promesse de don a bien été enregistrée, merci pour votre générosité !")
    return render_template('promesse_don.html')






"""
# Lancement hors console de notre appli (vérifie que le script main correspond au script en cours donc que __main__ est app.py :
if __name__ == '__main__':
    # Equivaut à un "flask run" avec "set FLASK_ENV=development" :
    app.run(debug=True)

# INFO : quand on lance via cette technique, il faut que la version de python employée supporte SSL et donc il faut l'avoir installée.
"""