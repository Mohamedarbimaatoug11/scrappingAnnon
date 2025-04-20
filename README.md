<<<<<<< HEAD
# Menzili Scraper et API

Ce projet est une application Python qui scrape des annonces immobilières sur le site [Menzili.tn](https://www.menzili.tn) et expose les données via une API RESTful construite avec Flask. Les données sont sauvegardées dans un fichier CSV (`annonces_immobilieres.csv`) et dans une base de données PostgreSQL.

## Fonctionnalités

- **Scraping** : Récupère les annonces immobilières publiées entre le 01/01/2025 et le 28/02/2025 sur Menzili.tn.
- **Stockage** : Sauvegarde les données dans un fichier CSV et une base de données PostgreSQL.
- **API** : Fournit des endpoints pour accéder aux annonces et déclencher un nouveau scraping.

## Prérequis

- Python 3.12 ou supérieur
- PostgreSQL (installé et configuré)
- Microsoft Edge (pour le scraping avec Selenium)
- `msedgedriver.exe` (compatible avec votre version de Microsoft Edge) ou `webdriver-manager` (recommandé)

## Installation

1. **Clonez le dépôt  :**
   ```bash
   git clone <url-du-depot>
   cd menzili-scraper-api
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
## API Endpoints
- `GET /annonces`: Returns all listings.
- `POST scrape-form`: Triggers a new scraping session.

## Database
- Data is stored in a PostgreSQL database. Use PgAdmin to view the `annonces` table.
=======
# scrappingAnnon
>>>>>>> 52156865228ce96614f63f2a192275120fc7250d
