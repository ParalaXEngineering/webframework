# Generalities
The OuFNis is an interface aimed at collecting and making easy to use the different tools used in FN development. While the present interface is aimed at the DFDIG project, and that some tools are already included, it has been design with modularity in mind in order to be able to be extended on different project and with more tools.

As a result, the program is composed of two components: the main engine, and the site handler. In this case, the site handler is "OuFNis". It is possible to create any number of site that use the same engine.

At the core of the tool interface, there is several key components:

* A Process manager, that can keep track of the tools running. Some tools are just a simple action, while some are meant to run in the background.
* A Process, which offers different functionalities to execute commands localy and remotely
* A Web engine, that generate the html page of the interface.

## Structure of the files
The main folder is structured as is:

* **binaries**: all the files that are used by the tools.
* **help**: help files (in markdown format)
* **framework**: all the files that are related to the web engine, that is the helper functions (in utilities), the scheduler, the common pages, etc.
* **Site_Name**: each website (that is each distinct application) has its own folder
* **assets**: website ressources (image, javascripts, etc.).
* **templates**: the jinja files used to render the website

## Structure of the code
The entry point of the code is the main.py file, which provide the init of the website, the logger, and the scheduler (more on that later). 

The software is architectured around 3 basic concepts:

* A scheduler is in charge of managing communication with the website (by sending periodic information and status through a socket), and the basic information of the station, by periodically pinging it and recovering its temperature. At the moment, only the temperature is handled, however more information can be coded, such as CPU load. This can be done by updating the "config.json" file with more options in the "Tob Bar Information", and coding how to react to those addition directly in the scheduler.
* Each site provide a collection of modules and pages. A page is charged to prepare everything to be rendered by the web engine. A module implements the needed actions to be performed. A module is eather a process derived from the class *threaded_action*, or a simple class derived from *action*.
* A module is a process. Each tool must be derived from the base class *threaded_action* which will wrap the tool code in order to be put in a thread, and will handle destruction of the thread when needed. Moreover, the tool provide some function in order to read information from a local console and a distant one and upload a tool. This usually covers all the requirements in term of communication. A process manager logs the running tools and provide a mechanism to kill them.
* A web engine (powered by flask) handles the creation of the interface to the user.

# How-tos
## Add a new web page
A new web page can be added at two places:

* Either as a main item in the sidebar ("Low level tools" or "Programmation" in the bellow image)
* Or as a subitem ("Debug packages" or "LRU Tools" in the bellow image)

![Sidebar](/static/doc/sidebar.png "Sidebar")

In the first case, it is recommanded to create a new .py file that will handle all the subpages. To do so, a few steps must be taken:

1. Create the file.
2. Create a blueprint, which indicate to flask the entry point of the page. That is, if a blueprint as a name foo, then each pages will have the address 127.0.0.1:5000/foo.

        bp = Blueprint('foo', __name__, url_prefix='/foo')

3. Create a function for each subpage, with the decorator blueprint.route to indicate to flask the address to use.

        @bp.route('/my_func', methods=['GET', 'POST'])
        def my_func():   

4. Register the blueprint in the main.py

        app.register_blueprint(foo.bp)

5. Add the sidebar item.

        g.sidebar.append({
            "name": "My function",
            "endpoint": "foo.my_func",
            "icon": "mdi-human-greeting",
            "cat": "",
            "url": "foo.my_func"
        })

Please note that with flask and jinja, url are created by using the jinja function "url_for", and that the name of the url is "blueprint.function".

If the page already exists and just a subpage needs to be created, only the points 3. and 5. needs to be followed

## Create a new tool (tool engine)
Create a new file into the OuFNis.modules folder, and create a class that inherit Threaded_action. The simplest tool (that does nothing) is:

    from OuFNis_DFDIG.modules import threaded_action
    class HELLO_world(threaded_action.Threaded_action):
        m_default_name = "Hello World"
        
        def action(self):
            return 

The action function will in fact run in a thread, so it must be able to communicate with the user. It is possible to send updates to the "Action progress" by emiting status:

    scheduler.scheduler_obj.emit_status(self.get_name(), "Updating status", 100, "More information")

This function allows you to update the progress bar (0-99), indicate that your action is done (100), failed (101), or simply indicate something to a user (102). You can provide more information, that will be displayed with the progress bar / status.

For instance, the following code:
    scheduler.scheduler_obj.emit_status(self.get_name(), "Connection failed", 101)
    scheduler.scheduler_obj.emit_status(self.get_name(), "Operation succeed", 100)
    scheduler.scheduler_obj.emit_status(self.get_name(), "Progressing", 50, "Currently in some progress")
will produce the following information:

![Action progress](/static/doc/action_progress.png "Action progress")

Other communication means exists with the user: update a given content in the web page, or send popups:

* To send content, use the "emit_content" function, and modify the OuFNis.modules.js javascript file in order to set the content to the appropriate location. Please note that you also have to handle your html accordingly. At the moment, this function is only used with the "Running tools" page.
* Popus can have several levels of severity: see the class "logLevel" in the scheduler.

        scheduler.scheduler_obj.emit_popup(scheduler.logLevel.warning, "Hello World")

![Popup](/static/doc/popup.png "Popup")

To code your tool, most of the time, you will simply issue command and process (see documentation in the scheduler class) and parse them, but you can of course use any python code you want. Please look at the currently coded tools to understand the mechanisms used. In particular, FPGA_program is a good example on using process while MCU_program is a good example on using remote commands.

## Create a new tool (web interface)
Once your new tool is coded, you can add it to the interface. You can of course create a new page with a new template tailored to your needs, however it is possible to use the standard template which, while quiet simple, allows for a lot of cases.

The main concept is that a web page is represented by a list of dictionnaries, each dicionarries having the information of a specific tool:

* The name of the tool
* A list of inputs (select, number or nothing), associated with a button. Clicking the button will send the information of the input to the page. It is not, at the moment, possible to have several inputs for a single button (but that could be coded quiet easily)
* An optional info text (blue), warning text (yellow) or a large pannel (a grey info pannel that use all the width of the page)
* The possibility to deactivate the tool (mostly used if a tool is not compatible with the running OS)

The first step is to declare the tools that will be in the page:

    softwares = utilities.util_view_init([SW_dfnet.SW_dfnet, STANAG_tools.STANAG_tools, DB_tools.DB_tools])

Then, it is just a matter of using the view utilities in the utilities file to add the required information. The templating engine will do the rest.

A good example is the software.py file.

## Ressources
The website use the mazer template (https://github.com/zuramai/mazer), have a look at their demo to see what can be done with it. This template uses bootstrap, so the documentation of bootstrap is also a nice place to start. Finally, all the icons are from the mdi project (https://pictogrammers.github.io/@mdi/font/6.5.95/)

Coded and tested on python 3.6