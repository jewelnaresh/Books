import os

from flask import Flask, session, render_template, request, redirect
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
    return render_template("search.html")

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
        if result:
            return render_template("error.html", message = "username already taken")
        if password != confirmation:
            return render_template("error.html", message = "passwords do not match")

        #Creata a hash of the password
        hashnum = generate_password_hash(password)

        # register new user
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashnum)", {"username": username, "hashnum": hashnum})
        db.commit()

        # log in the user
        rows = db.execute("SELECT id from users WHERE username= :username", {"username": username}).fetchone()
        session["user_id"] = rows["id"]

        # redirect the user
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """login a user"""
    # Forget any user_id
    session.clear()

    if request.method == "POST":

        # store form data into variables
        username = request.form.get("username")
        password = request.form.get("password")

        # check the form data
        if not username:
            return render_template("error.html", message="Enter username")
        elif not password:
            return render_template("error.html", message="Enter password")
        
        # quest the DB for username and password
        rows = db.execute("SELECT username, hash FROM users WHERE username= :username", {"username": username}).fetchone()
        
        # check if password and username is correct
        if rows["username"] == username and check_password_hash(rows["hash"], password):
            return redirect("/")
        else:
            return render_template("error.html", message="Invalid username or password")

    # if access method is GET show the login page
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Logout the user"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/search")
def books():
    
    # get input from form data
    search = request.args.get("search")

    # check if input data is missing
    if not search:
        return render_template("error.html", message="Please enter search terms")
    
    # Query the search and output result
    results = db.execute("SELECT title, id FROM books WHERE isbn LIKE :q OR title LIKE :q OR author LIKE :q LIMIT 10",{"q": ('%'+search+'%')}).fetchall()
    if not results:
        return render_template("error.html", message="No results found")
    else:
        return render_template("results.html", results=results)

@app.route("/books/<string:book_id>")
def book(book_id):
    book = db.execute("SELECT isbn, title ,author, year FROM books WHERE id= :book_id", {"book_id": book_id}).fetchone()
    reviews = db.execute("SELECT rating, review FROM reviews WHERE book_id= :book_id", {"book_id": book_id}).fetchall()
    return render_template("book.html", book=book, reviews=reviews)