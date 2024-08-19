# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

# -- Project information -----------------------------------------------------

project = "DSMS Documentation"
copyright = "2024, Materials Informatics Team at Fraunhofer IWM"
author = "Materials Informatics, Fraunhofer IWM"
release = "v1.0.0"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = [
    "myst_parser",  # Markdown support
    "sphinx.ext.autodoc",  # Include documentation from docstrings
    "sphinx.ext.napoleon",  # Google-style docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.graphviz",  # Add support for graphviz
    "sphinxcontrib.plantuml",  # Add support for plantuml
    "sphinx_copybutton",  # Add copy button to code blocks
    "nbsphinx",  # Add support for Jupyter Notebooks
    "IPython.sphinxext.ipython_console_highlighting",  # Add syntax highlighting for IPython
    "sphinx.ext.autosectionlabel",  # Add support for autolabeling sections
    "sphinx_panels",  # Add support for panels
    "sphinx_markdown_tables",  # Add support for markdown tables
    "sphinxcontrib.redoc",  # Add support for redoc
]

master_doc = "index"
myst_enable_extensions = ["colon_fence"]

plantuml = "java -jar lib/plantuml.jar"
plantuml_output_format = "svg_img"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
html_static_path = ["assets"]


def setup(app):
    app.add_css_file("custom.css")


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_book_theme"
html_logo = "assets/images/DSMS_logo.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#   "style_nav_header_background": "#4472c4",  : Blue of DSMS
#   "style_nav_header_background": "#109193",  : Green of DSMS
html_static_path = ["_static"]
templates_path = ["_templates"]
html_theme_options = {
    "use_download_button": True,
}

nbsphinx_allow_errors = True
nbsphinx_execute = "never"

# -- Options for LaTeX output -------------------------------------------------
latex_documents = [
    (
        "index",
        "dsms_docs.tex",
        "DSMS docs",
        ("Materials Informatics team at Fraunhofer IWM"),
        "manual",
        "false",
    )
]
latex_logo = "assets/images/DSMS_logo.png"
latex_elements = {"figure_align": "H"}

nbsphinx_allow_errors = True

suppress_warnings = ["myst.mathjax"]
