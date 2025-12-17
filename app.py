from flask import Flask, request, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
import psycopg
import os
from dotenv import load_dotenv
import urllib.parse

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Protection CSRF
csrf = CSRFProtect(app)

# Config DB
database_url = os.getenv("DATABASE_URL")

if database_url:
    # Si on est sur Heroku, parse DATABASE_URL
    result = urllib.parse.urlparse(database_url)
    DB_CONFIG = {
        "host": result.hostname,
        "dbname": result.path[1:],
        "user": result.username,
        "password": result.password,
        "port": result.port,
        "sslmode": "require"  # Heroku PostgreSQL
    }
else:
    # Local
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "sslmode": "disable"  # Désactive SSL pour la DB locale
    }

# Formulaire avec validation
class QuestionnaireForm(FlaskForm):
    name = StringField("Nom", validators=[DataRequired()])
    response = TextAreaField("Réponse", validators=[DataRequired()])
    consent = BooleanField("Je consens au traitement", validators=[DataRequired()])

def init_db():
    """Créer la table responses si elle n'existe pas"""
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

init_db()

@app.route("/", methods=["GET", "POST"])
def home():
    form = QuestionnaireForm()
    if form.validate_on_submit():
        name = form.name.data
        response = form.response.data
        with psycopg.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO responses (name, response) VALUES (%s, %s)",
                    (name, response)
                )
        flash("Merci pour votre participation !", "success")
        return redirect(url_for("home"))
    return render_template("form.html", form=form)

if __name__ == "__main__":
    app.run(debug=False)
