#     Copyright 2020 getcarrier.io
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from functools import wraps
from typing import Optional
from json import loads

from flask import session, redirect, url_for, current_app, request
from werkzeug.exceptions import NotFound
from requests import get
from galloper.constants import APP_HOST

from galloper.config import Config


class SessionProject:
    PROJECT_CACHE_KEY = Config().PROJECT_CACHE_KEY

    @staticmethod
    def set(project_id: int) -> None:
        session[SessionProject.PROJECT_CACHE_KEY] = project_id

    @staticmethod
    def pop() -> Optional[int]:
        return session.pop(SessionProject.PROJECT_CACHE_KEY, default=None)

    @staticmethod
    def get() -> Optional[int]:
        return session.get(SessionProject.PROJECT_CACHE_KEY)


class SessionUser:
    USER_CACHE_KEY = Config().USER_CACHE_KEY

    @staticmethod
    def set(user_session: dict) -> None:
        session[SessionUser.USER_CACHE_KEY] = user_session

    @staticmethod
    def pop() -> Optional[int]:
        return session.pop(SessionUser.USER_CACHE_KEY, default=None)

    @staticmethod
    def get() -> Optional[int]:
        return session.get(SessionUser.USER_CACHE_KEY)


def project_required(func):
    from galloper.database.models.project import Project

    @wraps(func)
    def decorated_function(*args, **kwargs):
        project_id = SessionProject.get()
        if is_user_part_of_the_project(project_id):
            try:
                project = Project.query.get_or_404(project_id)
                return func(project, *args, **kwargs)
            except NotFound:
                ...

        return redirect(url_for("projects.list"))

    return decorated_function


def is_user_part_of_the_project(project_id):
    user_data = SessionUser.get()
    if not user_data:
        headers = {}
        for header in request.headers:
            if header[0].lower() in ["cookie", "authorization"]:
                headers[header[0]] = header[1]
        headers["Content-Type"] = "application/json"
        user_data = get(f"{APP_HOST}/forward-auth/me", headers=headers).json()
        current_app.logger.info(user_data)
    if Config().SUPERADMIN_GROUP in user_data["groups"]:
        return True
    else:
        # check permission
        if f"/{project_id}" in user_data["groups"]:
            return True
    return False
