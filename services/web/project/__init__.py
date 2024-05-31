import os
from flask import Flask, jsonify, send_from_directory, request
from random import shuffle
from datetime import datetime

app = Flask(__name__)

app.config['DATA_DIR']: str = os.environ.get('DATA_DIR', "data")
app.config['CACHE_SECRET']: str = os.environ.get('CACHE_SECRET', "CHANGEME")

KNOWN_REACTIONS = []
KNOWN_REACTIONS_LAST_UPDATE = 0
KNOWN_IN_FOLDER = {}
KNOWN_IN_FOLDER_LAST_UPDATE = 0
LAST_REACTION = {}


def get_data_dir():
    # We want to get it inside of the static folder
    data_dir = os.path.join(app.static_folder, app.config['DATA_DIR'])
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir


def get_reactions():
    global KNOWN_REACTIONS, KNOWN_REACTIONS_LAST_UPDATE
    # Check if we need to update the list
    # We will update the list every 5 minutes
    if datetime.now().timestamp() - KNOWN_REACTIONS_LAST_UPDATE > 300:
        KNOWN_REACTIONS = os.listdir(get_data_dir())
        KNOWN_REACTIONS_LAST_UPDATE = datetime.now().timestamp()
    return KNOWN_REACTIONS


def get_reactions_in_folder():
    global KNOWN_IN_FOLDER, KNOWN_IN_FOLDER_LAST_UPDATE
    # Check if we need to update the list
    # We will update the list every 5 minutes
    if datetime.now().timestamp() - KNOWN_IN_FOLDER_LAST_UPDATE > 300:
        KNOWN_IN_FOLDER = {}
        for reaction in get_reactions():
            reaction_dir = os.path.join(get_data_dir(), reaction)
            files = os.listdir(reaction_dir)
            if len(files) == 0:
                # Also remove it from the KNOWN_REACTIONS list
                KNOWN_REACTIONS.remove(reaction)
                continue
            KNOWN_IN_FOLDER[reaction] = files
        KNOWN_IN_FOLDER_LAST_UPDATE = datetime.now().timestamp()
    return KNOWN_IN_FOLDER


@app.route("/")
def index():
    # Just list the folders in the data directory
    returned_folders = {}
    folders = get_reactions()
    reactions = get_reactions_in_folder()
    # Get number of files in each folder
    for folder in folders:
        returned_folders[folder] = len(reactions[folder])
    data = {
        "reactions": returned_folders
    }
    return jsonify(data)


@app.route("/<string:reaction>")
def get_reaction(reaction):
    # Ensure this reaction folder exists
    if reaction not in get_reactions():
        return jsonify({"error": "Reaction not found"}), 404

    # If it is then we want a random .gif file from the folder
    reaction_dir = os.path.join(get_data_dir(), reaction)
    try:
        files = get_reactions_in_folder()[reaction]
        shuffle(files)
        # Attempt to NOT use the last reaction unless our list is only 1 long
        if len(files) > 1 and files[0] == LAST_REACTION.get(reaction):
            # Set the last reaction to the second one
            LAST_REACTION[reaction] = files[1]
            return send_from_directory(reaction_dir, files[1])
        LAST_REACTION[reaction] = files[0]
        return send_from_directory(reaction_dir, files[0])
    except KeyError:
        return jsonify({"error": "No files found in reaction folder"}), 404


@app.route("/<string:reaction>/list")
def list_reaction(reaction):
    # Ensure this reaction folder exists
    if reaction not in get_reactions():
        return jsonify({"error": "Reaction not found"}), 404

    # If it is then we want a random .gif file from the folder
    files = get_reactions_in_folder()[reaction]
    return jsonify(files)


@app.route("/cache", methods=["DELETE"])
def clear_cache():
    global KNOWN_REACTIONS, KNOWN_REACTIONS_LAST_UPDATE
    global KNOWN_IN_FOLDER, KNOWN_IN_FOLDER_LAST_UPDATE
    # Check headers for a secret
    if not request.headers.get('secret') or request.headers.get('secret') != app.config['CACHE_SECRET']:
        return jsonify({"error": "Invalid secret"}), 403
    KNOWN_REACTIONS = []
    KNOWN_REACTIONS_LAST_UPDATE = 0
    KNOWN_IN_FOLDER = {}
    KNOWN_IN_FOLDER_LAST_UPDATE = 0
    return jsonify({"message": "Cache cleared"})
