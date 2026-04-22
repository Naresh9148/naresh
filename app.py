from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("bank.db")

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        pin TEXT,
        balance REAL
    )
    """)
    users = [
        ("arun","1234",5000),
        ("karthik","2345",6000),
        ("lakshmi","5555",9000),
        ("vignesh","3456",4500)
    ]
    for u in users:
        cur.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", u)
    db.commit()
    db.close()

class BankAccount:
    def __init__(self, username):
        self.username = username

    def verify_pin(self, pin):
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND pin=?", (self.username, pin))
        return cur.fetchone() is not None

    def get_balance(self):
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT balance FROM users WHERE username=?", (self.username,))
        return cur.fetchone()[0]

    def deposit(self, amount):
        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, self.username))
        db.commit()
        return "Deposit successful"

    def withdraw(self, amount):
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT balance FROM users WHERE username=?", (self.username,))
        bal = cur.fetchone()[0]
        if amount > bal:
            return "Insufficient balance"
        cur.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, self.username))
        db.commit()
        return "Withdraw successful"

    def transfer(self, to_user, amount):
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT balance FROM users WHERE username=?", (self.username,))
        bal = cur.fetchone()[0]

        cur.execute("SELECT * FROM users WHERE username=?", (to_user,))
        if not cur.fetchone():
            return "User not found"

        if amount > bal:
            return "Insufficient balance"

        cur.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, self.username))
        cur.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, to_user))
        db.commit()
        return "Transfer successful"

@app.route("/", methods=["GET","POST"])
def login():
    init_db()
    if request.method == "POST":
        user = request.form["username"]
        pin = request.form["pin"]

        acc = BankAccount(user)
        if acc.verify_pin(pin):
            session["user"] = user
            return redirect("/dashboard")
        return "Invalid login"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    acc = BankAccount(user)
    return render_template("dashboard.html", user=user, balance=acc.get_balance())

@app.route("/deposit", methods=["POST"])
def deposit():
    user = session.get("user")
    amt = float(request.form["amount"])
    return BankAccount(user).deposit(amt)

@app.route("/withdraw", methods=["POST"])
def withdraw():
    user = session.get("user")
    amt = float(request.form["amount"])
    return BankAccount(user).withdraw(amt)

@app.route("/transfer", methods=["POST"])
def transfer():
    user = session.get("user")
    to_user = request.form["to"]
    amt = float(request.form["amount"])
    return BankAccount(user).transfer(to_user, amt)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)