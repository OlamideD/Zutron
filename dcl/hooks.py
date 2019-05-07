# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "dcl"
app_title = "Dcl"
app_publisher = "John Vincent Fiel"
app_description = "DCL"
app_icon = "octicon octicon-file-directory"
app_color = "green"
app_email = "johnvincentfiel@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dcl/css/dcl.css"
app_include_js = "/assets/js/dcl.min.js"

# include js, css files in header of web template
# web_include_css = "/assets/dcl/css/dcl.css"
# web_include_js = "/assets/dcl/js/dcl.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "dcl.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "dcl.install.before_install"
# after_install = "dcl.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dcl.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # "Sales Order": {
    #     "before_insert": "dcl.dcl.remove_in_words" #NoneType
    # },
    # "Sales Invoice": {
    #     "before_insert": "dcl.dcl.remove_in_words"#NoneType
    # }
    # "Sales Order": {
    #     "autoname": "dcl.dcl.remove_in_words"  # NoneType
    # },
    # "Sales Invoice": {
    #     "autoname": "dcl.dcl.remove_in_words"  # NoneType
    # }
    "Sales Order": {
        "validate": "dcl.dcl.remove_in_words"
    },
    "Sales Invoice": {
        "validate": "dcl.dcl.remove_in_words"
    },
    "Delivery Note": {
        "validate": "dcl.dcl.remove_in_words"
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dcl.tasks.all"
# 	],
# 	"daily": [
# 		"dcl.tasks.daily"
# 	],
# 	"hourly": [
# 		"dcl.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dcl.tasks.weekly"
# 	]
# 	"monthly": [
# 		"dcl.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "dcl.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dcl.event.get_events"
# }


fixtures = ["Print Format", "Custom Field"]
