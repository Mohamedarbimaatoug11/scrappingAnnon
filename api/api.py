from flask import Flask, jsonify, render_template_string
import pandas as pd
import os
import logging

app = Flask(__name__)

# Configurez les logs
logging.basicConfig(level=logging.DEBUG)

# Définir le chemin du fichier CSV
CSV_FILE_PATH = 'C:/Users/COOLBOX/Desktop/menzeli/annonces_immobilieres.csv'  # Chemin absolu

# Charger les données scraped au démarrage
def load_data():
    app.logger.debug(f"Tentative de chargement du fichier : {CSV_FILE_PATH}")
    if os.path.exists(CSV_FILE_PATH):
        try:
            df = pd.read_csv(CSV_FILE_PATH)
            app.logger.info(f"Fichier '{CSV_FILE_PATH}' chargé avec succès. {len(df)} lignes trouvées.")
            return df
        except Exception as e:
            app.logger.error(f"Erreur lors du chargement du fichier CSV : {e}")
            return pd.DataFrame()
    else:
        app.logger.error(f"Le fichier '{CSV_FILE_PATH}' n'existe pas dans {os.getcwd()}.")
        return pd.DataFrame()

# Charger les données une seule fois au démarrage
df = load_data()

@app.route('/', methods=['GET'])
def home():
    """
    Endpoint par défaut pour la racine de l'API.
    """
    return jsonify({"message": "Bienvenue sur l'API Menzili ! Utilisez /annonces pour voir les annonces ou /scrape-form pour lancer un scraping."})

@app.route('/annonces', methods=['GET'])
def get_annonces():
    """
    Endpoint pour retourner toutes les annonces.
    """
    app.logger.debug("Requête reçue pour /annonces")
    if df.empty:
        app.logger.warning("Aucune donnée disponible dans df.")
        return jsonify({"error": "Aucune donnée disponible. Vérifiez que le fichier CSV existe et est valide."}), 404
    return jsonify(df.to_dict(orient='records'))

@app.route('/scrape-form', methods=['GET'])
def scrape_form():
    """
    Affiche un formulaire HTML pour déclencher un scraping via POST.
    """
    html = """
    <html>
    <body>
        <h1>API Menzili - Déclencher un Scraping</h1>
        <form method="POST" action="/scrape">
            <button type="submit">Lancer le Scraping</button>
        </form>
        <p><a href="/annonces">Voir les annonces</a></p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Endpoint pour déclencher une nouvelle session de scraping.
    """
    app.logger.debug("Requête reçue pour /scrape")
    # TODO: Appelez ici votre fonction de scraping (par exemple, depuis menz.py)
    # Exemple : success = scrape_all_pages(CSV_FILE_PATH)
    global df
    df = load_data()  # Recharge les données après le scraping
    return jsonify({"message": "Scraping completed"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)