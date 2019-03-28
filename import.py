import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# read the csv file containing books
f = open("books.csv", "r")
reader = csv.reader(f)

# create database for books
# db.execute("CREATE TABLE books (id SERIAL PRIMARY KEY, isbn INTEGER NOT NULL, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER NOT NULL)")

# add books to the database
for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn, "title": title, "author": author, "year": year})
    db.commit()