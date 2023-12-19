import threading
import traceback
from submodules.framework.src import scheduler
from submodules.framework.src import displayer


class Workflow:
    m_type = "worfklow"
    m_default_name = "Workflow Instance"

    def __init__(self):
        """Definition of the steps of the module:
        display: a list of functions that return a dictionnary as provided by the util_view helper functions
        worker: a list of function that configure the module (for instance by setting the input variables, etc.)
        """
        self.m_name = None

        self.m_steps = {"display": [], "workers": [], "skippers": [], "submenus": []}

        # Current step in the workflow
        self.m_current_step = 0

        # Optional variable that can be used to force a next step from the child object. If not used, set to -1
        self.m_next_step = -1

        # Data from the POST information that is used by the workers
        self.m_data_in = None

        # Internal thread
        self.m_thread_worker = None

    def get_name(self) -> str:
        """Return the name of this instance workflow

        :return: The name of the current workflow
        :rtype: str
        """
        if self.m_name:
            return self.m_name

        return self.m_default_name

    def change_name(self, name: str):
        """Change the name of the instance of the module

        :param name: The new name
        :type name: str
        """
        self.m_name = name

    def prepare_workflow(self, data_in: dict) -> bool:
        """Test if the data_in structure that is returned from a POST request contains information relative to this workflow

        :param data_in: The data taken directly from the data_in of a POST request, transformed by util_post_to_json
        :type data_in: dict
        :return: True if there is data relative to the workflow, false otherwise
        :rtype: bool
        """
        # Step 0
        if not data_in:
            self.m_current_step = 0
            return True

        self.m_data_in = data_in
        if self.m_default_name in data_in:
            data_in = data_in[self.m_default_name]
            self.m_data_in = data_in
            if "workflow_skip" in data_in:
                self.m_current_step = int(data_in["current_step"]) + 1
                return True
            elif "workflow_next" in data_in:
                if "next_step" in data_in:
                    self.m_current_step = int(data_in["next_step"])
                else:
                    self.m_current_step = int(data_in["current_step"]) + 1

                return True

        return False

    def prepare_worker(self):
        """Prepare the worker for its job by setting the arguments necessary"""
        # Step 0
        if not self.m_data_in:
            self.m_current_step = 0
            self.m_data_in = {}

        if len(self.m_steps["workers"]) < self.m_current_step:
            return

        if "workflow_skip" in self.m_data_in:
            try:
                # Start the worker in a thread
                self.m_thread_worker = threading.Thread(
                    target=self.m_steps["skippers"][self.m_current_step], daemon=True
                )
                self.m_thread_worker.start()
            except Exception as e:
                traceback_str = traceback.format_exc()
                self.m_logger.warning("Skipper workflow failed: " + str(e))
                self.m_logger.info("Traceback was: " + traceback_str)

                scheduler.scheduler_obj.emit_popup(
                    scheduler.logLevel.warning, "Skipper failed with error " + str(e)
                )
        else:
            try:
                # Start the worker in a thread
                self.m_thread_worker = threading.Thread(
                    target=self.m_steps["workers"][self.m_current_step], daemon=True
                )
                self.m_thread_worker.start()
            except Exception as e:
                traceback_str = traceback.format_exc()
                self.m_logger.warning("Worker workflow failed: " + str(e))
                self.m_logger.info("Traceback was: " + traceback_str)
                scheduler.scheduler_obj.emit_popup(
                    scheduler.logLevel.warning, "Worker failed with error " + str(e)
                )
        return

    def add_display(self, disp: displayer) -> dict:
        """Initialize the view and populate it with the necessary information to handle the workflow

        :return: The dictionnary of the view
        :rtype: displayer
        """

        # Not authorized
        if not disp:
            return disp

        if len(self.m_steps["submenus"]) < self.m_current_step:
            submenu = "No title"
        else:
            submenu = self.m_steps["submenus"][self.m_current_step]

        # Check that we have a displayer
        disp.add_module(self, submenu)
        if len(self.m_steps["display"]) >= self.m_current_step:
            # Ask it to populate
            disp = self.m_steps["display"][self.m_current_step](disp)

        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [12],
                subtitle="",
                alignment=[displayer.BSalign.R],
            )
        )

        if self.m_current_step < len(self.m_steps["display"]) - 1:
            disp.add_display_item(
                displayer.DisplayerItemHidden("current_step", str(self.m_current_step))
            )
            if self.m_next_step != -1:
                disp.add_display_item(
                    displayer.DisplayerItemHidden("next_step", str(self.m_next_step))
                )

            disp.add_display_item(
                displayer.DisplayerItemButton("workflow_next", "Next"),
                0,
                disabled=False,
            )
            disp.add_display_item(
                displayer.DisplayerItemButton("workflow_skip", "Skip"),
                0,
                disabled=False,
            )

        return disp
