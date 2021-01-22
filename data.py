from pymongo import MongoClient

def get_db_connection():
    """Connection au cluster distant mongo atlas. Retour d'un objet client utilisable pour du requêtage."""
    client = MongoClient("mongodb+srv://amaury:motdepasse@moncluster.xximx.mongodb.net/<MonCluster>?retryWrites=true&w=majority")
    return client


def envoi_promesse_base(dico):
    """Envoi d'une promesse depuis un dico constitué via les inputs html gérés dans la fonction gestion_formulaire."""
    client = get_db_connection()
    client.db.promesses_de_dons.insert_one(dico)
    client.close()

def recup_promesses_base():
    """Récupération et return sous forme de liste de dictionnaires de toutes les promesses depuis la base."""
    client = get_db_connection()
    promesses = []
    for p in client.db.promesses_de_dons.find({}, {"_id":0}):
        promesses.append(p)
    client.close()
    return promesses