import unittest
import pytest


@pytest.fixture(scope='module', params=("2.0.0", "3.0.0"))
def spec(request):
    return APISpec(
        title="Swagger Petstore",
        version="1.0.0",
        openapi_version=request.param,
        plugins=(FlaskPlugin(),),
    )


class TestFlaskPlugin(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client()
        self.ctx = self.app.config['APPLICATION_CONTEXT']
