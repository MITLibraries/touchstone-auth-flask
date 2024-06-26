"""touchstone_auth_flask/app.py

This Flask application serves to demonstrate how the touchstone-auth-flask library can be
imported and used in a different Flask app.  This example app is NOT included or used when
this library is installed in other projects; it is for demonstration purposes only.
"""

from flask import Flask, render_template

# NOTE: import of the touchstone_auth_flask library
from touchstone_auth_flask.lib.auth import (
    initialize_touchstone_auth,
    login_required,
)

app = Flask(__name__)

# NOTE: demonstrates initialization of the touchstone auth blueprint and helpers
initialize_touchstone_auth(app)


# NOTE: example of public, unauthenticated route
@app.route("/")
def index() -> str:
    return render_template("index.html")


# NOTE: example of an protected, authenticated route by applying @login_required
@app.route("/protected")
@login_required
def protected() -> str:
    return render_template("protected.html")


if __name__ == "__main__":
    app.run()
