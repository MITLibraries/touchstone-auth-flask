from urllib.parse import urlparse
from xml.dom.minidom import Document

from flask import Request, current_app
from onelogin.saml2.auth import OneLogin_Saml2_Auth

DEFAULT_SAML_SETTINGS: dict = {
    "strict": True,
    "debug": False,
    "sp": {
        "entityId": "",
        "assertionConsumerService": {
            "url": "",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
        },
        "x509cert": "",
        "privateKey": "",
    },
    "idp": {
        "entityId": "",
        "singleSignOnService": {
            "url": "",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
        "x509cert": "",
    },
    "security": {
        "requestedAuthnContext": False,
        "signMetadata": True,
        "authnRequestsSigned": True,
        "wantAssertionsEncrypted": True,
        "wantAssertionsSigned": True,
    },
}


def get_saml_auth_obj(request: Request) -> OneLogin_Saml2_Auth:
    """Get OneLogin_Saml2_Auth object."""
    saml_settings = load_saml_settings()
    req = prepare_flask_request(request)
    return OneLogin_Saml2_Auth(req, saml_settings)


def load_saml_settings() -> dict:
    """Load SAML settings for use in metadata generation and communication with the IdP

    This method overrides or adds values to what exists in the saml/settings.json file
    """
    saml_settings = DEFAULT_SAML_SETTINGS

    saml_settings["debug"] = True

    saml_settings["sp"]["entityId"] = current_app.config["SP_ENTITY_ID"]
    saml_settings["sp"]["assertionConsumerService"]["url"] = current_app.config[
        "SP_ACS_URL"
    ]
    saml_settings["sp"]["x509cert"] = current_app.config["SP_CERT"]
    saml_settings["sp"]["privateKey"] = current_app.config["SP_KEY"]

    saml_settings["idp"]["entityId"] = current_app.config["IDP_ENTITY_ID"]
    saml_settings["idp"]["singleSignOnService"]["url"] = current_app.config["IDP_SSO_URL"]
    saml_settings["idp"]["x509cert"] = current_app.config["IDP_CERT"]

    saml_settings["security"]["wantAssertionsEncrypted"] = current_app.config.get(
        "SP_SECURITY_ASSERTIONS_ENCRYPTED", False
    )

    return saml_settings


def prepare_flask_request(request: Request) -> dict:
    """Return a dictionary in a format that OneLogin_Saml2_Auth uses during init"""
    url_data = urlparse(request.url)
    return {
        "https": "on" if request.scheme == "https" else "off",
        "http_host": request.host,
        "server_port": url_data.port,
        "script_name": request.path,
        "get_data": request.args.copy(),  # type: ignore[no-untyped-call]
        "post_data": request.form.copy(),  # type: ignore[no-untyped-call]
    }


def parse_saml_xml_response(auth_obj: OneLogin_Saml2_Auth) -> Document:
    """Parse raw SAML XML response from IdP after login is complete.

    This is expecting a OneLogin_Saml2_Auth object, like g.auth, that is hydrated with
    POST data from the IdP response.
    """
    response = auth_obj.response_class(
        auth_obj._settings,  # noqa: SLF001
        auth_obj._request_data["post_data"]["SAMLResponse"],  # noqa: SLF001
    )
    return response.get_xml_document()
