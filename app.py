# Forcer le redéploiement sur Railway
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

# 📌 Création de l'application Flask
app = Flask(__name__)
app.secret_key = "votre_secret_key"  # Changez ceci pour plus de sécurité

# 📌 Configuration de Flask-Mail pour Gmail
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "votre_email@gmail.com"  # Remplacez par votre adresse Gmail
app.config["MAIL_PASSWORD"] = "votre_mot_de_passe"  # Remplacez par un mot de passe d'application Gmail
app.config["MAIL_DEFAULT_SENDER"] = "votre_email@gmail.com"

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# 📌 Connexion à la base de données
def get_db():
    db_path = os.path.join(os.getcwd(), "database.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# 📌 Création des tables
def create_tables():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()

# 📌 Page d'accueil
@app.route("/")
def home():
    return render_template("home.html")

# 📌 Page d'inscription
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            return redirect("/login")
        except:
            return "Erreur : cet email existe déjà."
    return render_template("register.html")

# 📌 Page de connexion
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/questions")
        return "Identifiants incorrects."
    return render_template("login.html")

# 📌 Mot de passe oublié
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if user:
            # Générer un token sécurisé
            token = serializer.dumps(email, salt="password-reset-salt")
            reset_url = f"http://127.0.0.1:5000/reset_password/{token}"

            # Envoyer l'email
            msg = Message("Réinitialisation de votre mot de passe",
                          recipients=[email])
            msg.body = f"Bonjour,\n\nCliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_url}\n\nCe lien expirera dans 30 minutes."
            mail.send(msg)

        return "Si un compte est associé à cet email, un lien de réinitialisation a été envoyé."

    return render_template("forgot_password.html")

# 📌 Réinitialisation du mot de passe
@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=1800)  # Expiration 30 min
    except:
        return "Lien invalide ou expiré."

    if request.method == "POST":
        new_password = generate_password_hash(request.form["password"])
        conn = get_db()
        conn.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))
        conn.commit()
        return "Votre mot de passe a été réinitialisé. <a href='/login'>Se connecter</a>"

    return render_template("reset_password.html")

# 📌 Page des questions
@app.route("/questions", methods=["GET", "POST"])
def questions():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    if request.method == "POST":
        question = request.form["question"]
        response = request.form["response"]
        conn.execute("INSERT INTO responses (user_id, question, response) VALUES (?, ?, ?)",
                     (session["user_id"], question, response))
        conn.commit()

    user_responses = conn.execute("SELECT * FROM responses WHERE user_id=?", (session["user_id"],)).fetchall()
    return render_template("questions.html", responses=user_responses)

# 📌 Déconnexion
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# 📌 Fonction pour Gunicorn
def create_app():
    create_tables()
    return app

# 📌 Démarrage de l'application avec le bon port pour Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Utilisation du port défini par Railway
    app.run(host="0.0.0.0", port=port)
