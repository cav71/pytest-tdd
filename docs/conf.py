# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pytest-tdd'
copyright = '2025, A. Cavallo'
author = 'A. Cavallo'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = []

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "myst_parser",
    "sphinx_tabs.tabs",
    "sphinx_design",
    "myst_parser",
]


myst_enable_extensions = [
    "colon_fence",
    "tasklist",
    "fieldlist",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
html_theme_options = {
    "show_toc_level": 2,
    "show_navbar_depth": 2,
}

def setup(app):
    from types import ModuleType
    from sphinx.application import Sphinx
    from sphinx.ext.autodoc import Options
    #def docstring(app: Sphinx, what: str, name: str, obj: ModuleType, options: Options, lines: list[str]):
    #    if lines:
    #        lines[0] = f"{lines[0]}X"
    #    pass
    #app.connect('autodoc-process-docstring', docstring)
