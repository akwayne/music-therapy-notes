import os
from flask import Flask, render_template, session
from flask_session import Session

from user_auth import user_auth
from view_db import view_db
from change_db import change_db
from helpers import login_required, in_library, has_file, file_type, db_select

UPLOAD_FOLDER = os.path.join('static', 'temp_files')

# Configure app & connect blueprints
app = Flask(__name__)
app.register_blueprint(user_auth)
app.register_blueprint(view_db)
app.register_blueprint(change_db)

# Custom Filters
app.jinja_env.filters["in_library"] = in_library
app.jinja_env.filters["has_file"] = has_file
app.jinja_env.filters["file_type"] = file_type

# Configurations for file uploads
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# FROM FINANCE: Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# FROM FINANCE: Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Home page
@app.route("/")
@login_required
def index():
        
    return render_template("index.html")