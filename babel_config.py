# -*- coding: utf-8 -*-
"""
Babel configuration for Flask application
"""

from babel.messages import frontend as babel

# Add Jinja2 extension configuration
extensions = {
    'jinja2.ext.autoescape': 'jinja2.ext.autoescape:AutoEscapeExtension',
    'jinja2.ext.with_': 'jinja2.ext.with_:WithExtension'
}

# Default configuration
default_locale = 'en'
default_timezone = 'UTC'

# Available locales
locales = ['en', 'de', 'ru']

# Message catalogs directory
catalog_dir = 'app/translations'

# Extraction configuration
extraction_method = 'python'
keywords = [
    '_', 'gettext', 'ngettext', 'lazy_gettext', '_l'
]

# Jinja2 template extraction
jinja2_options = {
    'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.with_']
}
