# coding=utf-8

"""
    PyMatcha - A Python Dating Website
    Copyright (C) 2018-2019 jlasne/ynacache
    <jlasne@student.42.fr> - <ynacache@student.42.fr>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import os

import peewee

from flask import Flask, url_for, redirect, request

from flask_admin import Admin, AdminIndexView, helpers, expose

from werkzeug.security import generate_password_hash

import flask_login as login

if os.environ.get("FLASK_ENV", None) == "dev":
    os.environ["FLASK_DEBUG"] = "1"
    os.environ["FLASK_SECRET_KEY"] = "ThisIsADevelopmentKey"

if bool(int(os.environ.get("CI", 0))):
    os.environ["DB_HOST"] = "pymatchadb-tests.cvesmjtn6kz7.eu-west-3.rds.amazonaws.com"


if "FLASK_DEBUG" not in os.environ:
    raise EnvironmentError("FLASK_DEBUG is not set in the server's environment. Please fix and restart the server.")

if "FLASK_SECRET_KEY" not in os.environ:
    raise EnvironmentError(
        "FLASK_SECRET_KEY is not set in the server's environment. Please fix and restart the server."
    )

if "DB_USER" not in os.environ:
    raise EnvironmentError("DB_USER is not set in the server's environment. Please fix and restart the server.")

if "DB_PASSWORD" not in os.environ:
    raise EnvironmentError("DB_PASSWORD is not set in the server's environment. Please fix and restart the server.")

if "DB_HOST" not in os.environ:
    raise EnvironmentError("DB_HOST is not set in the server's environment. Please fix and restart the server.")


application = Flask(__name__)
application.debug = os.environ.get("FLASK_DEBUG", 1)
application.secret_key = os.environ.get("FLASK_SECRET_KEY", "ThisIsADevelopmentKey")

app_db = peewee.MySQLDatabase(
    "PyMatcha",
    password=os.environ.get("DB_PASSWORD", None),
    user=os.environ.get("DB_USER", None),
    host=os.environ.get("DB_HOST", None),
    port=int(os.environ.get("DB_PORT", 3306)),
)

login_manager = login.LoginManager()
login_manager.init_app(application)


# Create user loader function
@login_manager.user_loader
def load_user(user_id):
    return User.get(id=user_id)


from PyMatcha.forms.user_access import LoginForm, RegistrationForm


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        return super(MyAdminIndexView, self).index()

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for(".index"))
        link = "<p>Don't have an account? <a href=\"" + url_for(".register_view") + '">Click here to register.</a></p>'
        self._template_args["form"] = form
        self._template_args["link"] = link
        return super(MyAdminIndexView, self).index()

    @expose("/register/", methods=("GET", "POST"))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = User.create(
                first_name="test", last_name="test", username=str(form.username.data), email=str(form.email.data)
            )

            user.password = generate_password_hash(form.password.data)

            user.save()

            login.login_user(user)
            return redirect(url_for(".index"))
        link = '<p>Already have an account? <a href="' + url_for(".login_view") + '">Click here to log in.</a></p>'
        self._template_args["form"] = form
        self._template_args["link"] = link
        return super(MyAdminIndexView, self).index()

    @expose("/logout/")
    def logout_view(self):
        login.logout_user()
        return redirect(url_for(".index"))


application.config["FLASK_ADMIN_SWATCH"] = "simplex"
admin = Admin(
    application,
    name="PyMatcha Admin",
    template_mode="bootstrap3",
    index_view=MyAdminIndexView(),
    base_template="my_master.html",
)

from PyMatcha.models.user import User, UserAdmin

admin.add_view(UserAdmin(User))

from PyMatcha.routes.views.home import home_bp
from PyMatcha.routes.api.ping_pong import ping_pong_bp

application.register_blueprint(home_bp)
application.register_blueprint(ping_pong_bp)

if bool(int(os.environ.get("CI", 0))):
    User.drop_table()
    User.create_table()
