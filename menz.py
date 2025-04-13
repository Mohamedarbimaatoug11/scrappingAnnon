from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import psycopg2

# Fonction pour nettoyer la description
def nettoyer_description(description):
    description = description.replace('\n', ' ')
    description = description.replace('"', '""')
    return description

# Fonction pour vérifier si une date est dans la plage 01/01/2025 - 28/02/2025
def est_dans_plage_date(date_str):
    try:
        if len(date_str.split('/')[2]) == 2:  # Format JJ/MM/AA
            date_obj = datetime.strptime(date_str, '%d/%m/%y')
            if date_obj.year < 2000:
                date_obj = date_obj.replace(year=date_obj.year + 2000)
        else:  # Format JJ/MM/AAAA
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        
        debut = datetime(2025, 1, 1)  # 01/01/2025
        fin = datetime(2025, 2, 28)   # 28/02/2025
        print(f"Date analysée : {date_str} -> {date_obj.strftime('%d/%m/%Y')}")
        return debut <= date_obj <= fin
    except ValueError as e:
        print(f"Erreur de parsing de la date '{date_str}' : {e}")
        return False

# Fonction pour sauvegarder dans PostgreSQL
def save_to_postgres(data):
    try:
        conn = psycopg2.connect(
            dbname="menzili_annonces",
            user="postgres",
            password="123456789",  # Votre mot de passe
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS annonces (
                id SERIAL PRIMARY KEY,
                titre VARCHAR(255),
                lieu VARCHAR(100),
                date_publication VARCHAR(50),
                description TEXT,
                prix VARCHAR(50),
                type_bien VARCHAR(100),
                surf_terrain VARCHAR(50),
                lien TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO annonces (titre, lieu, date_publication, description, prix, type_bien, surf_terrain, lien)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['titre'], data['lieu'], data['date'], data['description'], data['prix'], data['type_bien'], data['surf_terrain'], data['lien']))

        conn.commit()
        print(f"Annonce '{data['titre']}' sauvegardée dans PostgreSQL.")
    except psycopg2.Error as e:
        print(f"Erreur PostgreSQL : {e}")
    finally:
        cursor.close()
        conn.close()

# Chemin vers msedgedriver.exe
PATH = "D:/edgedriver_win64/msedgedriver.exe"

# Configurer le pilote Edge
driver = webdriver.Edge(service=Service(PATH))

# URL de base
base_url = 'https://www.menzili.tn/immo/immobilier-tunisie'

# Ouvrir un fichier CSV pour écrire les données
with open('annonces_immobilieres.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Titre', 'Lieu', 'Date', 'Description', 'Prix', 'Type de bien', 'Surf terrain', 'Lien'])

    page_number = 1
    while True:
        url = f"{base_url}?l=0&page={page_number}&tri=1"
        print(f"Scraping de la page {page_number} : {url}")

        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'li-item-list')))

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        annonces = soup.find_all('div', class_='li-item-list')

        print(f"Nombre d'annonces trouvées sur la page {page_number} : {len(annonces)}")

        for annonce in annonces:
            lien = annonce.find('a', class_='li-item-list-title')
            if lien and 'href' in lien.attrs:
                lien = lien['href']
                if not lien.startswith('http'):
                    lien = f"https://www.menzili.tn{lien}"
            else:
                lien = "Non disponible"

            if not lien or lien == "Non disponible":
                print("Lien non trouvé ou invalide.")
                continue

            try:
                driver.get(lien)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
                annonce_source = driver.page_source
                annonce_soup = BeautifulSoup(annonce_source, 'html.parser')

                titre = annonce_soup.find('h1', itemprop='name').text.strip() if annonce_soup.find('h1', itemprop='name') else "Non disponible"

                product_title_div = annonce_soup.find('div', class_='product-title-h1')
                if product_title_div:
                    lieu_p = product_title_div.find('p')
                    if lieu_p:
                        lieu = lieu_p.get_text(strip=True).replace(lieu_p.find('i').get_text(strip=True), '').strip() if lieu_p.find('i') else lieu_p.get_text(strip=True)
                    else:
                        lieu = "Non disponible"
                else:
                    lieu = "Non disponible"

                date = annonce_soup.find('time', itemprop='datePublished')
                date_text = date.text.strip() if date else "Non disponible"

                if date_text == "Non disponible" or not est_dans_plage_date(date_text):
                    print(f"Date hors plage ou invalide pour {titre}: {date_text}")
                    driver.back()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'li-item-list')))
                    continue

                description = annonce_soup.find('div', class_='block-descr').text.strip() if annonce_soup.find('div', class_='block-descr') else "Non disponible"
                description = nettoyer_description(description)

                prix_element = annonce_soup.find('div', class_='product-price')
                if prix_element:
                    prix_p = prix_element.find('p')
                    if prix_p:
                        prix_text = prix_p.get_text(strip=True)
                        if "~" in prix_text:
                            prix = prix_text.split("~")[0].strip()
                        else:
                            prix = prix_text
                    else:
                        prix = "Non disponible"
                else:
                    prix = "Non disponible"

                # Extraction du "Type de bien"
                type_bien_elem = annonce_soup.find('a', href=lambda href: href and href.startswith('https://www.menzili.tn/immo/'))
                if type_bien_elem and type_bien_elem.find('span'):
                    type_bien = type_bien_elem.find('span').text.strip()
                else:
                    type_bien = "Non disponible"

                # Extraction corrigée de "Surf terrain"
                surf_terrain = "Non disponible"  # Valeur par défaut
                block_over_elems = annonce_soup.find_all('div', class_='block-over')  # Récupérer tous les éléments block-over
                for elem in block_over_elems:
                    span = elem.find('span')
                    if span and "Surf terrain" in span.text:
                        strong = elem.find('strong')
                        if strong:
                            surf_terrain = strong.text.strip()  # Extraire "725 m²"
                            break
                print(f"Debug - Surf terrain trouvé pour '{titre}' : {surf_terrain}")  # Débogage

                # Créer un dictionnaire pour les données de l'annonce
                annonce_data = {
                    'titre': titre,
                    'lieu': lieu,
                    'date': date_text,
                    'description': description,
                    'prix': prix,
                    'type_bien': type_bien,
                    'surf_terrain': surf_terrain,
                    'lien': lien
                }

                # Sauvegarder dans PostgreSQL
                save_to_postgres(annonce_data)

                # Écrire dans le fichier CSV
                print(f"Annonce valide trouvée : {titre} - Date : {date_text} - Type de bien : {type_bien} - Surf terrain : {surf_terrain}")
                writer.writerow([titre, lieu, date_text, description, prix, type_bien, surf_terrain, lien])

                driver.back()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'li-item-list')))
                time.sleep(2)

            except Exception as e:
                print(f"Erreur lors du traitement de l'annonce : {e}")
                continue

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'a.pag-item.btn.btn-default')
            if 'disabled' in next_button.get_attribute('class'):
                print("Fin de la pagination. Toutes les pages ont été parcourues.")
                break
            else:
                page_number += 1
        except Exception as e:
            print(f"Erreur lors de la navigation vers la page suivante : {e}")
            break

    print("Les données ont été exportées dans 'annonces_immobilieres.csv' et dans PostgreSQL.")

driver.quit()