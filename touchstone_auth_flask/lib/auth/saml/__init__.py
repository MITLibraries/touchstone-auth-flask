# ruff: noqa: S603

import logging
import os
import subprocess
import tempfile
from urllib.parse import urlparse
from xml.dom.minidom import Document

from flask import Request, current_app
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser

logger = logging.getLogger(__name__)

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
    """Load SAML settings for all IdP/SP interactions.

    This function overrides or adds values to DEFAULT_SAML_SETTINGS defined above.
    """
    saml_settings = DEFAULT_SAML_SETTINGS

    set_idp_sso_url_and_cert()
    set_development_sp_key_and_cert()

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


def set_idp_sso_url_and_cert() -> None:
    """Set IDP SSO URL and certificate from IdP metadata."""
    if (
        current_app.config["IDP_SSO_URL"] is None
        or current_app.config["IDP_CERT"] is None
    ):
        idp_metadata = retrieve_and_parse_idp_metadata()
        current_app.config["IDP_SSO_URL"] = idp_metadata["singleSignOnService"]["url"]
        current_app.config["IDP_CERT"] = idp_metadata["x509cert"]


def set_development_sp_key_and_cert() -> None:
    """Set SP key and certificate by generating a locally signed certificate.

    NOTE: this should be used only for development purposes and will throw an exception
     otherwise.
    """
    if current_app.config["SP_KEY"] is None or current_app.config["SP_CERT"] is None:

        if os.getenv("FLASK_ENV") not in ["development", "testing"]:
            message = "Environment variables SP_KEY and SP_CERT must be set."
            raise RuntimeError(message)

        current_app.config["SP_KEY"], current_app.config["SP_CERT"] = (
            generate_development_sp_x509_cert_and_key()
        )


def retrieve_and_parse_idp_metadata() -> dict:
    """Retrieve and parse metadata from remote IdP."""
    idp_entity_url = current_app.config["IDP_ENTITY_ID"]
    return OneLogin_Saml2_IdPMetadataParser.parse_remote(idp_entity_url)["idp"]


def generate_development_sp_x509_cert_and_key() -> tuple[str, str]:
    """Generate a locally signed certificate and return values."""
    with tempfile.NamedTemporaryFile(
        suffix=".pem"
    ) as key_file, tempfile.NamedTemporaryFile(suffix=".pem") as cert_file:
        openssl_command = [
            "openssl",
            "req",
            "-new",
            "-x509",
            "-nodes",
            "-newkey",
            "rsa:2048",
            "-keyout",
            key_file.name,
            "-days",
            "3650",
            "-out",
            cert_file.name,
            "-subj",
            "/C=US/ST=Massachusetts/L=Cambridge/O=MIT/OU=MIT Libraries/CN=localhost",
        ]
        subprocess.run(
            openssl_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            check=True,
        )
        local_key = key_file.read().decode()
        local_cert = cert_file.read().decode()
    return local_key, local_cert


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
