import os


class Config:
    TESTING = False
    DEBUG = False
    ENV = os.getenv("FLASK_ENV", default="production")
    SECRET_KEY = os.getenv("SECRET_KEY")
    AUTH_DEFAULT_VIEW = os.getenv("AUTH_DEFAULT_VIEW", default="index")
    IDP_ENTITY_ID = os.getenv("IDP_ENTITY_ID")
    IDP_SSO_URL = os.getenv("IDP_SSO_URL")
    IDP_CERT = os.getenv("IDP_CERT")
    SP_ENTITY_ID = os.getenv("SP_ENTITY_ID")
    SP_ACS_URL = os.getenv("SP_ACS_URL")
    SP_SECURITY_ASSERTIONS_ENCRYPTED = os.getenv(
        "SP_SECURITY_ASSERTIONS_ENCRYPTED", default=True  # noqa: PLW1508
    )
    SP_CERT = os.getenv("SP_CERT")
    SP_KEY = os.getenv("SP_KEY")
    URN_UID = os.getenv("URN_UID", default="urn:oid:1.3.6.1.4.1.5923.1.1.1.6")
    VALID_DOMAINS = os.getenv(
        "VALID_DOMAINS",
        default="cdn.libraries.mit.edu,cdn.dev1.mitlibrary.net,cdn.stage.mitlibrary.net",
    )


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"
    SECRET_KEY = "iamasecret"  # noqa: S105
    IDP_ENTITY_ID = "http://localhost:8080/simplesaml/saml2/idp/metadata.php"
    SP_ENTITY_ID = os.getenv("SP_ENTITY_ID", default="http://localhost:5000/saml")
    SP_ACS_URL = os.getenv("SP_ACS_URL", default="http://localhost:5000/saml/?acs")
    SP_SECURITY_ASSERTIONS_ENCRYPTED = os.getenv(
        "SP_SECURITY_ASSERTIONS_ENCRYPTED", default=False  # noqa: PLW1508
    )
    URN_UID = os.getenv("URN_UID", default="email")


class TestingConfig(Config):
    TESTING = True
    ENV = "testing"
    SECRET_KEY = "testing"  # noqa: S105
    IDP_ENTITY_ID = "http://example.com/shibboleth"
    IDP_SSO_URL = "http://example.com/idp/profile/SAML2/Redirect/SSO"
    IDP_CERT = "fakeIdPCert"
    SP_ENTITY_ID = "http://example.com/saml"
    SP_ACS_URL = "http://example.com/saml?acs"
