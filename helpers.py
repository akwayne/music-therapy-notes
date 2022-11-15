import os
from flask import redirect, render_template, session, current_app
import sqlite3
from functools import wraps

# Global set to store viewed temp files
viewed_files = set()

# FROM FINANCE: Function to display error page
def apology(message):
    return render_template("apology.html", message=message)


# FROM FINANCE: Decorator function to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# Function to query the database with SELECT
def db_select(query, variables=None):
    
    # Open database
    connection = sqlite3.connect("musictherapy.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # Execute query
    try:
        if variables == None:
            cursor.execute(query)
        
        else:
            cursor.execute(query, variables)
    
        # Copy rows from cursor
        rows = cursor.fetchall()

        # Transfer rows into a list of dictionaries
        dict_list = []
        for row in rows:
            dict_list.append({key: row[key] for key in row.keys()})

        # Close connection
        connection.commit()
        connection.close()

        return dict_list

    except:
        # End connection if something goes wrong
        connection.rollback()
        connection.close()

        return 'error'


# Function to query the database to make a change
def db_change(query, variables=None):

    # Open database
    connection = sqlite3.connect("musictherapy.db")
    cursor = connection.cursor()

    # Execute query
    try:
        if variables == None:
            cursor.execute(query)
        
        else:
            cursor.execute(query, variables)
        
        # Retrieve last row
        lastrowid = cursor.lastrowid

        # Close connection
        connection.commit()
        connection.close()

        return lastrowid

    except:
        # End connection if something goes wrong
        connection.rollback()
        connection.close()
        
        return 'error'


# Function to convert uploaded file to BLOB
def convert_to_binary(file_path):
    with open(file_path, 'rb') as file:
        binary = file.read()
    return binary


# Function to convert blob file for viewing
def write_file(file_name, file_blob):
    with open(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name), 'wb') as file:
        file.write(file_blob)

    return


# Function to determine if a song is in a user's library or not
def in_library(song_id):
    
    user_id = session["user_id"]
    
    rows = db_select("SELECT * FROM library WHERE user_id = ? AND song_id = ?",
    (user_id, song_id))

    if len(rows) == 0:
        return False

    else:
        return True


# Function to determine if a song has a file attached or not
def has_file(song_id):

    song = db_select("SELECT * FROM songs WHERE id = ?",
    (song_id,))[0]

    if song['file_name'] == None:
        return False

    else:
        return True


# Function to determine if uploaded file is image or PDF
def file_type(file_name):
    if file_name.endswith('.pdf'):
        return 'pdf'
    else:
        return 'image'


# Periodically deletes images from temp folder
def clean_temp_folder():
    for file_name in viewed_files:
        os.remove("static/temp_files/" + file_name)
    viewed_files.clear()
    return