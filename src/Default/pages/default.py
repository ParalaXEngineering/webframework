from flask import Blueprint, render_template, request, session

import copy

from framework import utilities
from framework import displayer

bp = Blueprint('default', __name__, url_prefix='/default')

@bp.route('/hello', methods=['GET', 'POST'])
def hello():

    disp = displayer.Displayer()
    disp.add_generic("Default page")
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], "Title here", [displayer.BSalign.C]))
    disp.add_display_item(displayer.DisplayerItemText("Hello world"))
   

    return render_template('base_content_new.j2', content=disp.display(), target="default.hello")