import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import re

# Fonction pour charger et préparer les données
def load_data(file_path='annonces_immobilieres.csv'):
    # Charger le fichier CSV
    df = pd.read_csv(file_path)
    
    # Renommer la colonne 'Date' si nécessaire
    df = df.rename(columns={"Date": "date"})
    
    # Convertir la colonne 'date' en format datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format='%d/%m/%y', errors="coerce")
        df = df.dropna(subset=["date"])  # Supprimer les lignes avec des dates invalides
    
    # Nettoyer et convertir la colonne 'Prix' en valeurs numériques
    def clean_price(price):
        if pd.isna(price) or price == "Non disponible":
            return None, None
        # Déterminer le type de prix
        price_type = "Vente"  # Par défaut
        if "/ Mois" in price:
            price_type = "Location"
        elif df.loc[df["Prix"] == price, "Description"].str.contains("prix affiché est celui de m²", na=False).any():
            price_type = "Par m²"
        
        # Supprimer tout ce qui n'est pas un chiffre
        price_cleaned = re.sub(r'[^\d]', '', str(price))
        try:
            return float(price_cleaned), price_type
        except:
            return None, None
    
    # Appliquer le nettoyage des prix et créer une colonne pour le type de prix
    if "Prix" in df.columns:
        df[["Prix_clean", "Type_prix"]] = pd.DataFrame(df["Prix"].apply(clean_price).tolist(), index=df.index)
        df = df.dropna(subset=["Prix_clean"])  # Supprimer les lignes avec des prix invalides
    
    # Extraire la ville depuis la colonne 'Lieu'
    def extract_city(lieu):
        if pd.isna(lieu) or lieu == "Non disponible":
            return "Inconnu"
        # Supposer que la ville est le dernier élément après la dernière virgule
        return lieu.split(',')[-1].strip()
    
    df["Ville"] = df["Lieu"].apply(extract_city)
    
    return df

# Charger les données
df = load_data()

# Initialiser l'application Dash
app = dash.Dash(__name__)

# Créer les visualisations
# 1. Distribution des prix (séparée par type de prix)
df_vente = df[df["Type_prix"] == "Vente"]
df_location = df[df["Type_prix"] == "Location"]
df_par_m2 = df[df["Type_prix"] == "Par m²"]

# Histogramme pour les prix de vente
if not df_vente.empty:
    fig_prix_vente = px.histogram(df_vente, x="Prix_clean", title="Distribution des prix de vente (en TND)", nbins=20)
else:
    fig_prix_vente = px.histogram(title="Aucune donnée pour les prix de vente")

# Histogramme pour les prix de location
if not df_location.empty:
    fig_prix_location = px.histogram(df_location, x="Prix_clean", title="Distribution des prix de location (en TND/mois)", nbins=20)
else:
    fig_prix_location = px.histogram(title="Aucune donnée pour les prix de location")

# Histogramme pour les prix par m²
if not df_par_m2.empty:
    fig_prix_par_m2 = px.histogram(df_par_m2, x="Prix_clean", title="Distribution des prix par m² (en TND/m²)", nbins=20)
else:
    fig_prix_par_m2 = px.histogram(title="Aucune donnée pour les prix par m²")

# 2. Répartition des annonces par ville
fig_ville = px.bar(df, x="Ville", title="Nombre d'annonces par ville", color="Ville")

# 3. Évolution du nombre d'annonces dans le temps
if not df.empty:
    df_evolution = df.groupby("date").size().reset_index(name="count")
    fig_evolution = px.line(df_evolution, x="date", y="count", title="Évolution des annonces dans le temps")
else:
    fig_evolution = px.line(title="Aucune donnée disponible")

# 4. NOUVEAU : Répartition des annonces par type de prix
fig_type_prix = px.pie(df, names="Type_prix", title="Répartition des annonces par type de prix")

# 5. NOUVEAU : Prix moyen par ville, séparé par type de prix
df_prix_moyen = df.groupby(["Ville", "Type_prix"])["Prix_clean"].mean().reset_index()
fig_prix_moyen = px.bar(df_prix_moyen, x="Ville", y="Prix_clean", color="Type_prix",
                        title="Prix moyen par ville et type de prix",
                        labels={"Prix_clean": "Prix moyen (TND)"},
                        barmode="group")

# 6. NOUVEAU : Nuage de points Prix vs Date
fig_scatter = px.scatter(df, x="date", y="Prix_clean", color="Type_prix",
                         title="Prix vs Date de publication",
                         labels={"Prix_clean": "Prix (TND)", "date": "Date"},
                         hover_data=["Titre", "Ville"])

# 7. NOUVEAU : Boîte à moustaches des prix par ville
fig_box = px.box(df, x="Ville", y="Prix_clean", color="Type_prix",
                 title="Distribution des prix par ville et type de prix",
                 labels={"Prix_clean": "Prix (TND)"},
                 points="all")  # Afficher tous les points pour un petit dataset

# Définir la mise en page du tableau de bord
app.layout = html.Div(children=[
    html.H1("Tableau de Bord des Annonces Immobilières", style={'textAlign': 'center'}),
    
    # Première rangée : Histogrammes des prix
    html.Div([
        dcc.Graph(figure=fig_prix_vente, style={'width': '30%'}),
        dcc.Graph(figure=fig_prix_location, style={'width': '30%'}),
        dcc.Graph(figure=fig_prix_par_m2, style={'width': '30%'})
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'flex-wrap': 'wrap'}),
    
    # Deuxième rangée : Répartition par type de prix et Prix moyen par ville
    html.Div([
        dcc.Graph(figure=fig_type_prix, style={'width': '45%'}),
        dcc.Graph(figure=fig_prix_moyen, style={'width': '45%'})
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'flex-wrap': 'wrap'}),
    
    # Troisième rangée : Annonces par ville et Évolution dans le temps
    html.Div([
        dcc.Graph(figure=fig_ville, style={'width': '45%'}),
        dcc.Graph(figure=fig_evolution, style={'width': '45%'})
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'flex-wrap': 'wrap'}),
    
    # Quatrième rangée : Nuage de points et Boîte à moustaches
    html.Div([
        dcc.Graph(figure=fig_scatter, style={'width': '45%'}),
        dcc.Graph(figure=fig_box, style={'width': '45%'})
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'flex-wrap': 'wrap'})
])

# Lancer l'application
if __name__ == '__main__':
    app.run(debug=True)