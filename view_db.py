# view_db is for functions that allow user to read and search for items in the database

from asyncore import write
from flask import Blueprint, render_template, redirect, request, session
from helpers import apology, login_required, db_select, write_file, viewed_files

view_db = Blueprint('view_db', __name__)


# Search page
@view_db.route("/search", methods=["GET", "POST"])
@login_required
def search():
    
    # if search form was submitted
    if request.method == 'POST':

        # Display tags by type on search form
        types = db_select("SELECT DISTINCT type FROM tags")
        type_list = [x['type'] for x in types]
        tags = db_select("SELECT * FROM tags")
        
        # Get info from form, text and list of TAG ID NUMBERS
        searched_text = request.form['search-text']
        searched_tags = request.form.getlist('tag', type=int)

        # Search by title or artist, from text submission
        # if no text submitted, then it shows all songs
        rows = db_select("SELECT id FROM songs WHERE title LIKE ? OR artist LIKE ?",
        ('%'+searched_text+'%', '%'+searched_text+'%'))
        text_song_ids = [dict['id'] for dict in rows]

        # Search by tags ONLY IF user checked at least 1 tag
        if len(searched_tags) != 0:

            # Get a list of song ids that match ALL tags selected
            list_length = len(searched_tags)

            rows = db_select('''SELECT song_id, 
            COUNT(tag_id) AS count
            FROM tagged 
            WHERE tag_id IN (%s)
            GROUP BY song_id''' 
            %','.join('?'*list_length), searched_tags)
        
            # Add song ids only if they show up for each tag in tag list
            tagged_song_ids = [x['song_id'] for x in rows if x['count'] == list_length]

            # combine text and tag searches
            song_ids = [x for x in text_song_ids if x in tagged_song_ids]

        # if no tags were checked off on form
        else:
            song_ids = text_song_ids

        # Get song info from song ids
        songs = []
        for id in song_ids:
            song = db_select('''SELECT songs.id, 
            songs.title, songs.artist, songs.description,
            group_concat(tags.name) AS tags 
            FROM songs, tagged, tags 
            WHERE songs.id = tagged.song_id
            AND tags.id = tagged.tag_id
            AND songs.id = ?''', 
            (id,))[0]

            # Split tags into a list
            song['tags'] = song['tags'].split(",")

            songs.append(song)

        return render_template("search-result.html", songs=songs, type_list=type_list, tags=tags, searched_text=searched_text, searched_tags=searched_tags)

    # if user gets to search page with GET request
    else:
        # Display tags by type on search form
        types = db_select("SELECT DISTINCT type FROM tags")
        type_list = [x['type'] for x in types]
        tags = db_select("SELECT * FROM tags")
          
        return render_template("search.html", type_list=type_list, tags=tags)


# View song details
@view_db.route("/song")
@login_required
def song():

    # get song id
    song_id = request.args.get("q")

    # Get song info & tags from song_id
    song = db_select('''SELECT songs.id, songs.user_id, 
    songs.title, songs.artist, 
    songs.description, songs.link,
    songs.file_name, songs.file_blob,
    group_concat(tags.name) AS tags 
    FROM songs, tagged, tags 
    WHERE songs.id = tagged.song_id
    AND tags.id = tagged.tag_id
    AND songs.id = ?''', 
    (song_id,))[0]

    # Split tags into a list, description into list
    song['tags'] = song['tags'].split(",")
    song['description'] = song['description'].split("\n")

    # Save file to temp files for viewing
    if song['file_name']:
        write_file(song['file_name'], song['file_blob'])

        # add to viewed files set
        viewed_files.add(song['file_name'])

        # update file name to include path for viewing
        file_path = ("temp_files/" + song['file_name'])

    else:
        # if no file, this variable will be empty
        file_path = None

    return render_template("song.html", song=song, file_path=file_path)


# My Uploads
@view_db.route("/myuploads")
@login_required
def myuploads():

    # Get user id
    user_id = session["user_id"]

    # Get list of uploads for this user from db
    songs = db_select('''SELECT songs.id, 
    songs.title, songs.artist,
    group_concat(tags.name) AS tags 
    FROM songs, tagged, tags 
    WHERE songs.id = tagged.song_id
    AND tags.id = tagged.tag_id
    AND songs.user_id = ?
    GROUP BY songs.id''', 
    (user_id,))

    if len(songs) == 0:
        return apology("You have not uploaded any songs")

    # Split tags into lists
    for song in songs:
        song['tags'] = song['tags'].split(",")

    return render_template("myuploads.html", songs=songs)


# My Library
@view_db.route("/mylibrary")
@login_required
def mylibrary():

    # Get user id
    user_id = session["user_id"]

    # Get list of uploads for this user from db
    songs = db_select('''SELECT songs.id, 
    songs.title, songs.artist,
    group_concat(tags.name) AS tags
    FROM songs, tagged, tags, library
    WHERE songs.id = tagged.song_id
    AND tags.id = tagged.tag_id
    AND songs.id = library.song_id
    AND library.user_id = ?
    GROUP by songs.id''',
    (user_id,))

    # Ensure that library is not empty
    if len(songs) == 0:
        return apology("You have not added any songs to your library")

    # Split tags into lists
    for song in songs:
        song['tags'] = song['tags'].split(",")

    return render_template("mylibrary.html", songs=songs)