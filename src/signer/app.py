import os
import sys

from flask import Flask, Blueprint, render_template, request, redirect, jsonify
from flaskwebgui import FlaskUI #get the FlaskUI class

from pathlib import Path
env_path = Path('.') / '.flaskenv'
from dotenv import load_dotenv
load_dotenv(env_path)


app = Flask(__name__, template_folder="templates", static_folder="specter/static")

# Feed it the flask app instance 
ui = FlaskUI(app)

# print("====================")
# print(path)
# sys.path.append(path)
# print("====================")
# print(sys.path)


# Import the hwi views from specter
from specter.views.hwi import hwi_views
app.register_blueprint(hwi_views, url_prefix='/hwi')



@app.route("/")
def index():
    return render_template("index.html")


# call the 'run' method
ui.run()

