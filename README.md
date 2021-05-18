# GG-API

Version 1.0

#### Installation

1. Cloner le répertoire GitHub

   ```bash
   git clone https://github.com/bastion-gaming/DB-API
   cd DB-API/
   ```

2. Création et activation d'un environnement virtuel

   ```bash
   python3 -m pip install --user virtualenv
   python3 -m venv env
   source env/bin/activate
   ```

3. Installation des dépendances

   ```bash
   python requirements.py
   ```



#### Exécution

Depuis le dossier **/DB-API**

###### Debug

```bash
uvicorn api.main:app --reload
```

###### Production

```bash
uvicorn api.main:app --host 0.0.0.0 --port 5195
```
