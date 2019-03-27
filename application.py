import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Project 1: TODO"

@app.route("/register", methods=["GET","POST"])
def register():
    """Register a user"""
    if request.method == "POST":

        # get form data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check the form data
        if not username or not password or not confirmation:
            return render_template("error.html", message = "Please fill out all the fields")
        result = db.execute("SELECT username FROM users WHERE username= :name", {"name": username}).fetchall()
        db.commit()
        if result:
            return render_template("error.html", message = "username already taken")
        if password != confirmation:
            return render_template("error.html", message = "passwords do not match")

        #Creata a hash of the password
        hashnum = generate_password_hash(password)

        # register new user
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashnum)", {"username": username, "hashnum": hashnum})

        #log in the user and redirect
        session["user_id"] = username
        return redirect("/")
    else:
        return render_template("register.html")
