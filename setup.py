from setuptools import setup

setup(
    name="touchstone-auth-flask",
    version="0.1.1",
    package_dir={"touchstone_auth_flask.lib": "touchstone_auth_flask/lib"},
    install_requires=[
        "docker",
        "flask",
        "flask-login",
        "python3-saml",
    ],
    entry_points={
        "console_scripts": [
            "simple_saml_server = touchstone_auth_flask.lib.utils.simple_saml_server"
            ":run_simple_saml_server",
        ],
    },
)
