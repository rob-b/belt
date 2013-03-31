import unittest
import py.test
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound, HTTPServerError
from httpretty import HTTPretty, httprettified
from ..utils import pypi_url


pypi_base_url = 'https://pypi.python.org/packages'


class TestView(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.add_settings({'local_packages': '/tmp'})

    def tearDown(self):
        testing.tearDown()

    @httprettified
    def test_returns_404_if_package_not_on_pypi(self):
        from ..views import download_package

        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8', 'flake8-2.0.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='Missed it!', status=404)
        request = testing.DummyRequest()
        request.matchdict = {'package': 'flake8', 'kind': 'source',
                             'letter': 'f', 'version': 'flake8-2.0.tar.gz'}
        with py.test.raises(HTTPNotFound):
            download_package(request)

    @httprettified
    def test_returns_500_when_server_error(self):
        from ..views import download_package

        url = pypi_url(pypi_base_url, 'source', 'f', 'flake8', 'flake8-2.0.tar.gz')
        HTTPretty.register_uri(HTTPretty.GET, url, body='Yikes!', status=500)
        request = testing.DummyRequest()
        request.matchdict = {'package': 'flake8', 'kind': 'source',
                             'letter': 'f', 'version': 'flake8-2.0.tar.gz'}

        with py.test.raises(HTTPServerError):
            download_package(request)
