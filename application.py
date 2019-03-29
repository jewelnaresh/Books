import os
import requests

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
        row = db.execute("SELECT id, username, hash FROM users WHERE username= :username", {"username": username}).fetchone()
        
        # check if password and username is correct
        if row["username"] == username and check_password_hash(row["hash"], password):
            session["user_id"] = row.id
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

    # query the database for book and review details and display it to the user
    book = db.execute("SELECT id, isbn, title ,author, year FROM books WHERE id= :book_id", {"book_id": book_id}).fetchone()
    reviews = db.execute("SELECT rating, review FROM reviews WHERE book_id= :book_id", {"book_id": book_id}).fetchall()

    # get the goodreads data
    KEY = "1nstTnBgfGhKbOwVncSc0Q"
    goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": book.isbn})
    g = goodreads.json()
    return render_template("book.html", book=book, reviews=reviews, gr=g)

@app.route("/review")
def review():

    # get review form data
    rating = request.args.get("rating")
    review = request.args.get("review")
    book_id = request.args.get("book_id")

    # query to check if user has already given a review
    result = db.execute("SELECT id FROM reviews WHERE user_id= :user_id AND book_id= :book_id", {"user_id": session["user_id"], "book_id": book_id}).fetchone()

    # if user had already given a review show an error message
    if result:
        return render_template("error.html", message="You have already give a review")

    # add the review form data
    db.execute("INSERT INTO reviews (rating, review, book_id, user_id) VALUES (:rating, :review, :book_id, :user_id)", {"rating": rating, "review": review, "book_id": book_id, "user_id": session["user_id"]})
    db.commit()

    # redirect user to the current page
    return redirect("/books/" + book_id)