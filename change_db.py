# change_db is for functions that allow the user to add, change, or delete items in database

import os
from flask import Blueprint, render_template, redirect, request, session, current_app
from werkzeug.utils import secure_filename

from helpers import apology, login_required, db_select, db_change, convert_to_binary, in_library

change_db = Blueprint('change_db', __name__)


# Upload a New Song
@change_db.route("/upload", methods=["GET", "POST"])
@login_required
def upload():

    # If user submitted the upload form
    if request.method == 'POST':

        # Get user id from session
        user_id = session["user_id"]
        
        # Get info from form
        title = request.form['title']
        artist = request.form['artist']
        description = request.form['description']
        link = request.form['link']
        file = request.files['file']
        taglist = request.form.getlist('tag')

        # Ensure required fields were submitted
        if not title or not artist or not taglist:
            return apology("Required: title, artist, at least 1 tag")

        # Process uploaded file if one was uploaded
        if file:
            file_name = secure_filename(file.filename)
            
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))
            file_path = ('static/temp_files/' + file_name)
            file_blob = convert_to_binary(file_path)
            
            # delete file once binary is extracted
            os.remove("static/temp_files/" + file_name)

        else:
            file_name = None
            file_blob = None

        # Insert song info into songs table
        # function should return last row id as song_id
        song_id = db_change('''INSERT INTO songs 
        (user_id, title, artist, description, 
        link, file_name, file_blob) 
        VALUES(?, ?, ?, ?, ?, ?, ?)''',
        (user_id, title, artist, description, link, file_name, file_blob))

        if song_id == 'error':
            return apology("Error inserting song into database")

        # Insert tags into tagged table
        for tag_id in taglist:
            db_change("INSERT INTO tagged (song_id, tag_id) VALUES(?, ?)",
            (song_id, tag_id))

        return redirect("/")

    # If user reached upload page
    else:
        # Display tags by type on upload form
        types = db_select("SELECT DISTINCT type FROM tags")
        type_list = [x['type'] for x in types]
        tags = db_select("SELECT * FROM tags")
        
        return render_template("upload.html", type_list=type_list, tags=tags)


# Edit a Song
@change_db.route("/edit", methods=["GET", "POST"])
@login_required
def edit():

    #if edit form was submitted
    if request.method == 'POST':
        
        # Get info from form
        song_id = request.form['songid']
        title = request.form['title']
        artist = request.form['artist']
        description = request.form['description']
        link = request.form['link']
        file = request.files['file']
        taglist = request.form.getlist('tag')

        # Ensure required fields were submitted
        if not title or not artist or not taglist:
            return apology("Required: title, artist, at least 1 tag")

        # Update songs table with new information (not including new file)
        db_change("UPDATE songs SET title = ?, artist = ?, description = ?, link = ? WHERE id = ?",
        (title, artist, description, link, song_id))

        # Clear tags for current song in database
        db_change("DELETE FROM tagged WHERE song_id = ?", (song_id,))

        # Insert new tags for current song
        for tag_id in taglist:
            db_change("INSERT INTO tagged (song_id, tag_id) VALUES(?, ?)",
            (song_id, tag_id))

        # Process uploaded file if a new one was uploaded
        if file:
            file_name = secure_filename(file.filename)
            
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file_name))
            file_path = ('static/temp_files/' + file_name)
            file_blob = convert_to_binary(file_path)
            
            # delete file from temp folder once binary is extracted
            os.remove("static/temp_files/" + file_name)
            
            # insert new file into directory
            db_change("UPDATE songs SET file_name = ?, file_blob = ? WHERE id = ?",
            (file_name, file_blob, song_id))

        # Remove file from song if box was checked AND new file not added
        elif request.form.get('remove_file'):
            db_change("UPDATE songs SET file_name = NULL, file_blob = NULL WHERE id = ?",
            (song_id,))
        
        return redirect("/myuploads")

    # get request (with args in URL for song id)
    else:
        song_id = request.args.get("q")

        # only allow user who uploaded song to edit
        owner_id = db_select("SELECT user_id FROM songs WHERE id = ?", 
        (song_id,))[0]['user_id']

        if owner_id != session["user_id"]:
            return apology("Not authorized")

        # Get song info & tags from song_id
        song = db_select('''SELECT songs.id, 
        songs.title, songs.artist, songs.description, 
        songs.link, songs.file_name,
        group_concat(tags.name) AS tags 
        FROM songs, tagged, tags 
        WHERE songs.id = tagged.song_id
        AND tags.id = tagged.tag_id
        AND songs.id = ?''', 
        (song_id,))[0]

        # Split tags into a list
        song['tags'] = song['tags'].split(",")

        # Display tags by type on edit form
        types = db_select("SELECT DISTINCT type FROM tags")
        type_list = [x['type'] for x in types]
        tags = db_select("SELECT * FROM tags")

        return render_template("edit.html", song=song, type_list=type_list, tags=tags)


# Delete a Song
@change_db.route("/delete", methods=["POST"])
@login_required
def delete():
    
    # Get hidden field from form
    song_id = request.form['songid']

    # only allow user who uploaded song to delete
    owner_id = db_select("SELECT user_id FROM songs WHERE id = ?", 
    (song_id,))[0]['user_id']

    if owner_id != session["user_id"]:
        return apology("Not authorized")
    
    # TODO combine into a single query
    db_change("DELETE FROM tagged WHERE song_id = ?", (song_id,))
    db_change("DELETE FROM library WHERE song_id = ?", (song_id,))
    db_change("DELETE FROM songs WHERE id = ?", (song_id,))

    return redirect("/myuploads")


# Add song to My Library
@change_db.route("/addtolibrary", methods=["POST"])
@login_required
def addtolibrary():

    user_id = session["user_id"]
    
    # Get hidden field from form
    song_id = request.form['songid']
    
    # is it already in the library ?
    if in_library(song_id):
        return apology("Already added to library")

    else:
        # add user and song info to library table
        db_change("INSERT INTO library (user_id, song_id) VALUES(?, ?)",
        (user_id, song_id))

        return redirect("/mylibrary")


# Remove song from My Library
@change_db.route("/removelibrary", methods=["POST"])
@login_required
def removelibrary():

    user_id = session["user_id"]
    
    # Get hidden field from form
    song_id = request.form['songid']
    
    # add user and song info to library table
    db_change("DELETE FROM library WHERE user_id = ? AND song_id = ?",
    (user_id, song_id))

    return redirect("/mylibrary")