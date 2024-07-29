from django.test import TestCase
from django.test import Client

def test_landing_page():
    """ Test that landing page is redirected.
    """
    c = Client()
    response = c.get("/")
    assert response.status_code in [301, 302, 308]
    