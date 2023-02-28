import http
import http.client

from apispec import BasePlugin, yaml_utils
from apispec.exceptions import APISpecError
from flask import current_app
from flask.views import MethodView

from apispec_plugins import utils as spec_utils
from apispec_plugins.base import types


class FlaskPlugin(BasePlugin):
    """APISpec plugin for Flask"""

    def __init__(self, default_media="application/json"):
        self.spec = None
        self.default_media = default_media

    def init_spec(self, spec):
        super().init_spec(spec)
        self.spec = spec

    @staticmethod
    def _rule_view(view, app=None):
        if app is None:
            app = current_app

        view_funcs = app.view_functions
        endpoint = next(
            endpoint for endpoint, view_func in view_funcs.items() if view_func == view
        )
        if not endpoint:
            raise APISpecError(f"Could not find endpoint for view {view}")

        # TODO: assume 1 rule per view function for now
        rule = next(app.url_map.iter_rules(endpoint=endpoint))
        return rule

    def path_helper(self, operations=None, view=None, app=None, **kwargs):
        """Path helper hook to set path specs from a Flask view."""
        path = kwargs.pop("path", None)
        if path:
            return path

        rule = self._rule_view(view, app=app)

        # populate properties for operations
        operations.update(yaml_utils.load_operations_from_docstring(view.__doc__))
        if hasattr(view, "view_class") and issubclass(view.view_class, MethodView):
            for method in view.methods:
                if method in rule.methods:
                    method_name = method.lower()
                    method = getattr(view.view_class, method_name)
                    operations[method_name] = spec_utils.load_method_specs(method)
        return spec_utils.path_parser(rule.rule, **kwargs)

    def operation_helper(self, path=None, operations=None, **kwargs):
        """Operation helper hook to process operation properties."""

        for op in operations.values():
            if type(op) is dict:
                for code in op.get("responses", {}):

                    # handle error codes only
                    if (
                        not op["responses"][code]
                        and isinstance(code, int)
                        and code >= 400
                    ):

                        description = http.client.responses[code]
                        schema_name = description.replace(" ", "")
                        op["responses"][code] = schema_name

                        http_schema_name = types.HTTPResponse.__name__
                        if http_schema_name not in self.spec.components.schemas:
                            self.spec.components.schema(
                                component_id=http_schema_name,
                                component=spec_utils.dataclass_schema_resolver(
                                    types.HTTPResponse
                                ),
                            )

                        if schema_name not in self.spec.components.responses:
                            component = {"schema": http_schema_name}
                            if self.spec.openapi_version.major >= 3:
                                component = {"content": {self.default_media: component}}
                            self.spec.components.response(
                                component_id=schema_name, component=component
                            )
