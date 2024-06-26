import logging
import typing

from flask import (
    Response,
    current_app,
    g,
    make_response,
    redirect,
    render_template,
    url_for,
)

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from touchstone_auth_flask.lib.auth import User


def set_current_user_flask_g(user: "User") -> None:
    g.user = user


def logout_local_testing_idp() -> Response:
    """Manually delete cookies from SimpleSAML server on logout if development context."""
    response = make_response(redirect(url_for(current_app.config["AUTH_DEFAULT_VIEW"])))
    response.delete_cookie("PHPSESSIDIDP")
    response.delete_cookie("SimpleSAMLAuthTokenIdp")
    return response


def handle_saml_auth_error(error_message: str) -> str:
    logger.warning(error_message)
    return render_template("error.html", error_message=error_message)
