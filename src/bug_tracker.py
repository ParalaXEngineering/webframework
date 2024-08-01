from flask import Blueprint, render_template, request

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import displayer
from submodules.framework.src import site_conf
from submodules.framework.src import User_defined_module

from redminelib import Redmine

bp = Blueprint("bug", __name__, url_prefix="/bug")


@bp.route("/bugtracker", methods=["GET", "POST"])
def bugtracker():
    param = utilities.util_read_parameters()
    disp = displayer.Displayer()
    # disp.add_generic("Changelog", display=False)
    User_defined_module.User_defined_module.m_default_name = "Bug Tracker"
    disp.add_module(User_defined_module.User_defined_module)

    redmine = Redmine(param["redmine"]["address"]["value"], username=param["redmine"]["user"]["value"], password=param["redmine"]["password"]["value"], requests={"verify": False})
    project_id = site_conf.site_conf_obj.m_app["name"].lower().replace('_', '-')
    issues = redmine.issue.filter(project_id=project_id)
    versions = redmine.version.filter(project_id=project_id)
    version_name = site_conf.site_conf_obj.m_app["version"].lower().replace('_', '-')

    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())["Bug Tracker"]
        if len(data_in["description"]) < 5:
            return render_template("failure.j2", message="Please provide a meaningfull description of the issue")
        if len(data_in["subject"]) < 5:
            return render_template("failure.j2", message="Please provide a meaningfull subject of the issue")

        version_redmine = 0
        for version in versions:
            if version.name == version_name:
                version_redmine = version.id

        try:
            redmine.issue.create(
                subject=data_in["subject"],
                description=data_in["description"] + '\r\n' + "Added by OuFNis User " + access_manager.auth_object.get_user(),
                project_id=project_id,
                custom_fields=[{"id": 10, "value": version_redmine}, {"id": 11, "value": "-"}, {"id": 16, "value": "-"}, {"id": 20, "value": "-"}, {"id": 20, "value": "-"}],
                uploads=[{'path': 'website.log', 'description': 'Website log'}, {'path': 'root.log', 'description': 'Root log'}]
            )
        except Exception as e:
            return render_template("failure.j2", message=f"Issue creation failed with the following message: {e}")

    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 7, 1], subtitle="Current issues")
    )

    for issue in issues:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 7, 1], subtitle=""))
        disp.add_display_item(displayer.DisplayerItemText(str(issue.subject)), 0)
        disp.add_display_item(displayer.DisplayerItemText(str(issue.description)), 1)
        disp.add_display_item(displayer.DisplayerItemIconLink("", "", "eye", issue.url, color=displayer.BSstyle.SUCCESS), 2)
        print(issue.description)

    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle="Create a new issue")
    )
    disp.add_display_item(displayer.DisplayerItemText("Enter subject"), 0)
    disp.add_display_item(displayer.DisplayerItemInputString("subject"), 1)
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle="")
    )
    disp.add_display_item(displayer.DisplayerItemText("Enter Description"), 0)
    disp.add_display_item(displayer.DisplayerItemInputString("description"), 1)

    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
    )
    disp.add_display_item(displayer.DisplayerItemButton("create", "Submit"))

    return render_template("base_content.j2", content=disp.display(), target="bug.bugtracker")
