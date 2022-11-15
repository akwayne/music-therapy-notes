# user_auth is for authorization tasks relating to login, logout, register

from flask import Blueprint, render_template, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, db_select, db_change, clean_temp_folder, login_required

user_auth = Blueprint('user_auth', __name__)


# Login page
@user_auth.route("/login", methods=["GET", "POST"])
def login():
    
    # Forget any logged-in user
    session.clear()

    # If user submitted login form
    if request.method == 'POST':

        # Get info from form
        username = request.form['username']
        password = request.form['password']

        # Ensure all fields were submitted
        if not username or not password:
            return apology("Please fill in all fields")

        # Find username in database
        user_row = db_select("SELECT * FROM users WHERE username = ?", (username,))

        # Check that username and password are correct
        if len(user_row) != 1 or not check_password_hash(user_row[0]['hash'], password):
            return apology("Invalid username and/or password")

        # Set session to current user
        session["user_id"] = user_row[0]['id']
        session["username"] = username

        return redirect("/")
    
    # If user reached login page
    else:
        return render_template("login.html")


# Logout page
@user_auth.route("/logout")
def logout():

    # Clear items from temp folder
    clean_temp_folder()
    
    # Forget user id to log out
    session.clear()

    return redirect("/")


# Registration page
@user_auth.route("/register", methods=["GET", "POST"])
def register():

    # Forget any logged in user
    session.clear()

    # If user submitted registration form
    if request.method == 'POST':

        # Get info from form
        username = request.form['username']
        password = request.form['password']
        confirmation = request.form['confirmation']

        # Ensure that all fields were submitted
        if not username or not password or not confirmation:
            return apology("Please fill in all fields")

        # Match password and confirmation
        if password != confirmation:
            return apology("Passwords must match")

        # Hash password
        hash = generate_password_hash(password)

        # Insert new user IF username is not already taken
        attempt = db_change("INSERT INTO users (username, hash) VALUES(?, ?)", (username, hash))
        if attempt == 'error':
            return apology("Username not available")

        return redirect("/")
    
    # If user reached registration page
    else:
        return render_template("register.html")


# Change Password page
@user_auth.route("/updatepass", methods=["GET", "POST"])
@login_required
def updatepass():

    # If user submitted a new password via form
    if request.method == 'POST':
        
        # Get user_id and form info
        user_id = session["user_id"]
        current_password = request.form['current-password']
        new_password = request.form['new-password']
        confirmation = request.form['confirmation']

        # Ensure all fields were submitted
        if not current_password or not new_password or not confirmation:
            return apology("Please fill in all fields")

        # Check that old password is correct
        current_hash = db_select("SELECT hash FROM users WHERE id = ?", (user_id,))[0]['hash']
        if not check_password_hash(current_hash, current_password):
            return apology("Incorrect password")

        # Match new password and confirmation
        if new_password != confirmation:
            return apology("Passwords must match")

        # Hash password
        new_hash = generate_password_hash(new_password)

        # Insert new password for this user
        db_change("UPDATE users SET hash = ? WHERE id = ?", (new_hash, user_id))

        return redirect("/myaccount")

    # If user reached page to update password
    else:
        
        return render_template("updatepass.html")