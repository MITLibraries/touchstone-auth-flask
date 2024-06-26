"""touchstone_auth_flask/lib/auth/__init__.py"""

import logging
import os

from flask import (
    Blueprint,
    Flask,
    Response,
    current_app,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.wrappers import Response as WerkzeugResponse

from touchstone_auth_flask.lib.auth.saml import get_saml_auth_obj
from touchstone_auth_flask.lib.auth.utils import (
    handle_saml_auth_error,
    logout_local_testing_idp,
    set_current_user_flask_g,
)
from touchstone_auth_flask.lib.config import Config, DevelopmentConfig, TestingConfig

logger = logging.getLogger(__name__)

login_manager = LoginManager()

touchstone_auth_bp = Blueprint(
    "touchstone_auth_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
)


def initialize_touchstone_auth(
    flask_app: Flask,
    url_prefix: str | None = "/auth",
) -> None:
    """Register Touchstone auth functionality with the primary Flask app.

    This function provides a single point of entry for registering the Touchstone auth
    Flask blueprint, initializing flask-login, and updating the calling Flask app config.
    """
    flask_app.register_blueprint(touchstone_auth_bp, url_prefix=url_prefix)
    login_manager.init_app(flask_app)
    match os.getenv("FLASK_ENV"):
        case "development":
            flask_app.config.from_object(DevelopmentConfig)
        case "testing":
            flask_app.config.from_object(TestingConfig)
        case _:
            flask_app.config.from_object(Config)


class User(UserMixin):
    def __init__(self, email: str):
        self.id = email
        self.email = email


@login_manager.user_loader
def load_user(user_id: str) -> User:
    """Flask-Login decorator to load user from session stored in cookie."""
    user = User(email=user_id)
    set_current_user_flask_g(user)
    return user


@touchstone_auth_bp.before_request
def before_request() -> None:
    """Convenience placement of OneLogin_Saml2_Auth object in Flask global g."""
    g.auth = get_saml_auth_obj(request)


@login_manager.unauthorized_handler
def unauthorized() -> WerkzeugResponse:
    """Redirect to login route if unauthorized attempt at protected route."""
    return redirect(f"{url_for("touchstone_auth_bp.login")}?next={request.url}")


################################
# Flask-Login and Debug Routes
################################


@touchstone_auth_bp.route("/login", methods=(["GET"]))
def login() -> WerkzeugResponse:
    next_url = request.args.get("next")
    saml_login_url = url_for("touchstone_auth_bp.saml_login")
    if next_url:
        saml_login_url = f"{saml_login_url}?next={next_url}"
    return redirect(saml_login_url)


@touchstone_auth_bp.route("/logout")
def logout() -> WerkzeugResponse:
    logout_user()
    if current_app.debug:
        return logout_local_testing_idp()
    return redirect(url_for(current_app.config["AUTH_DEFAULT_VIEW"]))


@touchstone_auth_bp.route("/whoami")
@login_required
def whoami() -> str:
    return render_template("whoami.html")


################################
# SAML Auth Routes
################################


@touchstone_auth_bp.route("/saml/login", methods=(["GET"]))
def saml_login() -> WerkzeugResponse:
    next_page = request.args.get(
        "next",
        url_for(current_app.config["AUTH_DEFAULT_VIEW"]),
    )
    return redirect(g.auth.login(return_to=next_page))


@touchstone_auth_bp.route("/saml/acs", methods=(["POST"]))
def acs() -> WerkzeugResponse | str:
    g.auth.process_response()
    errors = g.auth.get_errors()

    if not g.auth.is_authenticated():
        error_message = f"User returned from IdP with no authentication: {errors}"
        return handle_saml_auth_error(error_message)

    if errors:
        error_message = f"Errors occurred processing IdP response: {errors}"
        return handle_saml_auth_error(error_message)

    # parse user information from SAML response
    session["samlUserdata"] = g.auth.get_attributes()
    session["samlNameId"] = session["samlUserdata"][current_app.config["URN_UID"]][0]
    session["samlSessionIndex"] = g.auth.get_session_index()

    # login user for flask-login session
    user = User(email=session["samlNameId"])
    login_user(user)
    set_current_user_flask_g(user)

    redirect_url = request.form["RelayState"]
    return redirect(redirect_url)


@touchstone_auth_bp.route("/saml/metadata/")
def saml_metadata() -> Response:
    """Metadata route for this auth app as service provider (SP)."""
    settings = g.auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        response = make_response(metadata, 200)
        response.headers["Content-Type"] = "text/xml"
    else:
        response = make_response(", ".join(errors), 500)

    return response
