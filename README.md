# Convertisseur PDF vers EPUB

Une application web simple et rapide pour convertir vos fichiers PDF en format EPUB, développée avec Python et FastAPI. L'application extrait le texte et les images des fichiers PDF pour générer des livres électroniques (e-books) au format EPUB.

## Fonctionnalités

- **Conversion de PDF en EPUB** : Convertissez n'importe quel fichier PDF en un fichier EPUB lisible sur la plupart des liseuses.
- **Extraction d'images** : Les images contenues dans le PDF d'origine sont automatiquement extraites et intégrées au fichier EPUB final.
- **Nettoyage automatique** : Ignore automatiquement les numéros de page pour rendre la lecture plus fluide sur la liseuse.
- **Interface web simple** : Une interface utilisateur claire pour uploader facilement vos fichiers PDF.

## Technologies utilisées

- **[FastAPI](https://fastapi.tiangolo.com/)** : Framework web backend rapide et moderne.
- **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/en/latest/)** : Bibliothèque très performante pour l'extraction de texte et d'images des PDF.
- **[EbookLib](https://github.com/aerkalov/ebooklib)** : Bibliothèque pour gérer et créer des fichiers EPUB.
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)** : Pour générer du HTML propre et valide à intégrer dans l'EPUB.

## Prérequis

- Python 3.7+

## Installation

1. **Cloner le projet ou télécharger les fichiers** dans un dossier.
2. **Créer un environnement virtuel (recommandé)** :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```
3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

## Démarrage rapide

Pour lancer le serveur de développement en local, exécutez la commande suivante à la racine du projet :

```bash
uvicorn main:app --reload
```

Le serveur sera accessible par défaut à l'adresse : **http://127.0.0.1:8000**

## Utilisation

1. Ouvrez votre navigateur web et allez sur [http://127.0.0.1:8000](http://127.0.0.1:8000).
2. Cliquez sur le bouton pour sélectionner un fichier PDF depuis votre ordinateur.
3. Lancez la conversion. Le fichier EPUB sera automatiquement téléchargé une fois l'opération terminée.
