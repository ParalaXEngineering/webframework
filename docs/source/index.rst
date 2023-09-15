.. ParalaX Web documentation master file, created by
   sphinx-quickstart on Tue Dec  6 20:41:12 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ParalaX Web's documentation!
=======================================

ParalaX's Web package is a framework intended to make the creation tool management website easier. The project has been design with modularity in mind in order to be able to be extended on different project and with more tools.
As a result, the programs consists of two parts:

* A Framework
* A set of site handlers which implement a website

The framework provide a basic site handler, which has to be inherrited from by the differente websites. Several websites are made with this tool:

* OuFNis_HW
* OuFNis_DFDIG

The first part of the documentation aims to explain de use of the framework. Then, each developped module is documented


.. toctree::
   :maxdepth: 2
   :caption: Base content:

   framework
   sitehandler
   framework_classes

   oufnis_hw

.. note::

   This project is under active development.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
