Framework
*********

Description
###########

The base framework consists mainly of:

* A webengine, based on flask and jinja templates, generating html code from user functions.
* A scheduler :meth:`scheduler.Scheduler` , which will run every now and then to provide communication with the user's webclient; through socketio. This scheduler is responsible for refreshing some portions of the website, such as the buttons, the modals, etc.
* A thread manager :meth:`threaded_manager.Threaded_manager` , which register and maintain in memory a set of thread. It is responsible for registering and deleting them.
* A set of thread actions :meth:`threaded_action.Threaded_action` , which, once registered in the thread manager, offers a basic framework to do asynchronous work while the user still can use the website. The user can define as many thread as he wants, which can do a variety of work. From nowon, the term **module** will be used.
* A site conf :meth:`site_conf.Site_conf` which provides the basic site information. It should be overwritten by the child class

In addition, the framework provides different functionalities:

* An updater, that can check on a FTP server the presence of updates and apply them.
* An access manager :meth:`access_manager.Access_manager` in order to support login of different users and authorizations. This access manager shall not be access directly by a site handler: everything is configured through the settings of the application
* A set of helper functions :func:`utilities` . They range from easily listing serial ports to helper function to display stuff in the web engine.

Finally, the framework will auto-generate some pages that are always present in a website:

* An optional login page
* A mendatory setting page.

In addition to the framework, each website can have other items:
* A ressource folder, where files usefull for the website can be stored (for instance, binary files for different tools)
* A package folder, which is a compressed version of a base ressource folder, for easy sharing. The framework provide different helpers to generate those packages and manage them
* A download folder, for user inputs
* A docs folder, containing this documentation


File structure
##############
The ParalaX's Web basic file structure is:
::

    | ParalaX's Web
    | ├── docs (documentation sources)
    | ├── packages 
    | │   ├── website1
    | │   ├── website2
    | ├── ressources 
    | ├── packages 
    | │   ├── website1
    | │   ├── website2
    | ├── src (python sources)
    | │   ├── framework (framework python sources)
    | │   ├── website1 (First site handler)
    | │   ├── website2 (second site handler)
    | │   ├── ... (Any amount of site handlers)
    | │   ├── ... (Any amount of site handlers)
    | │   ├── templates (Jinja templates)
    | │   ├── main.py (Access point)
    | ├── webengine (website ressources)
    | │   ├── assets (css, js of the javascript)
