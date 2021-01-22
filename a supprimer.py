from app import db, User

# Ajout à la main d'un utilisateur en base

# Création de la table "user" dans la database "login.db" sur la base du modèle défini dans la classe User grâce au create_all() :
db.create_all()

# Création d'un objet utilisateur :
utilisateur = User(username = "Toto", password ="motdepasse", priviledge = "Admin")

# Ajout de l'utilisateur en base et commit :
db.session.add(utilisateur)
db.session.commit()
db.session.close()