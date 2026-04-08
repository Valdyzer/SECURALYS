# Projet SECURALYS

Ce projet est composé d'une interface web (Frontend) et d'une API de traitement de données (Backend en Python/FastAPI).

## Structure du projet
- `/frontend` : HTML5, CSS3, JavaScript
- `/backend` : Python 3 (librairies FastAPI, Uvicorn)
- `/Hardware` : C++

---

## 🚀 Installation et Lancement

### 1. Configuration du Backend (Python)

Il est recommandé d'utiliser un environnement virtuel pour éviter les conflits de versions.

#### **Sur macOS / Linux**
1. Ouvrez un terminal dans le dossier `backend`.

2. Créez l'environnement virtuel
   ```bash
   python3 -m venv venv
   
3. Activez-le
   ```bash
   source venv/bin/activate
   
4. Installez les dépendances
   ```bash
   pip install fastapi uvicorn serial sqlalchemy
   
5. Lancez le serveur
   ```bash
   uvicorn main:app --reload --port 8000


#### **Sur Windows**
1. Ouvrez un terminal (PowerShell ou CMD) dans le dossier `backend`.

2. Créez l'environnement virtuel
   ```bash
    python -m venv venv
    
3. Activez-le
   - PowerShell : `.\venv\Scripts\Activate.ps1`
   - CMD : `.\venv\Scripts\activate.bat`
   
5. Installez les dépendances
   ```bash
    pip install fastapi uvicorn   

6. Lancez le serveur
   ```bash
   python -m uvicorn main:app --reload --port 8000


### 2. Configuration du Frontend

Une fois le backend lancé sur le port 8000, vous devez ouvrir l'interface utilisateur.

- **Option recommandée (VS Code) :**
Installez l'extension **Live Server**, faites un clic droit sur `index.html` et sélectionnez `Open with Live Server`.

- **Option rapide :**
Double-cliquez simplement sur le fichier `index.html` (Note : certaines requêtes JS peuvent être bloquées selon le navigateur).
