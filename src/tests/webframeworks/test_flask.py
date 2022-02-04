import unittest

import pytest
from apispec import APISpec
from flask import Flask

from src.apispec_plugins.webframeworks.flask import FlaskPlugin


@pytest.fixture
def app():
    app = Flask(__name__)
    with app.test_request_context():
        yield app


@pytest.fixture(scope='module', params=("2.0.0", "3.0.0"))
def spec(request):
    return APISpec(
        title="Test Suite",
        version="1.0.0",
        openapi_version=request.param,
        plugins=(FlaskPlugin(),),
    )


class TestFlaskPlugin(unittest.TestCase):

    pass
