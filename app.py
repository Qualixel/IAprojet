from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = "votre_secret_key"

# Configuration de la base de données
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Création des tables
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

# Page d'accueil
@app.route("/")
def home():
    return render_template("home.html")

# Page d'inscription
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

# Page de connexion
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

# Page des questions
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

# Déconnexion
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Démarrage de l'application
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
