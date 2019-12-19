import os
import sys

from flask import Flask, Blueprint, render_template, request, redirect, jsonify
from flaskwebgui import FlaskUI


from pathlib import Path
env_path = Path('.') / '.flaskenv'
from dotenv import load_dotenv
load_dotenv(env_path)


app = Flask(__name__, template_folder="templates", static_folder="static")
ui = FlaskUI(app)

# print("====================")
# print(path)
# sys.path.append(path)
# print("====================")
# print(sys.path)


# Import the hwi views from specter
from hwi.hwi import hwi_blueprint
app.register_blueprint(hwi_blueprint, url_prefix='/hwi')



@app.route("/")
def index():
    return render_template("signer/index.html")


if __name__ == '__main__':
    # app.run(debug=True)
    ui.run()

