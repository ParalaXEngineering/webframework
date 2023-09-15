from flask import Blueprint, render_template, request, session, send_file

from framework import utilities
from framework import access_manager

import os
import sys

bp = Blueprint('common', __name__, url_prefix='/common')
@bp.route('/download', methods=['GET'])
def download():
    """Page that handle a download request by serving the file through flask
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        path = os.path.join(os.path.dirname(sys.executable), "..", "ressources", sys.argv[1], "downloads", request.args.to_dict()["file"])
    else:

        path = os.path.join(os.path.join("..", "ressources", sys.argv[1], "downloads"), request.args.to_dict()["file"])
    return send_file(path, as_attachment=True)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page
    """
    config = utilities.util_read_parameters()
    users = config["access"]["users"]["value"]

    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())
        authorized = access_manager.auth_object.set_user(data_in["user"], data_in["password"])

        if authorized:
            return render_template('index.j2')
        else:
            return render_template('failure.j2', message="Bad password")

    return render_template('login.j2', target="common.login", users=users)
