from flask import current_app
from flask.views import MethodView

from apispec import BasePlugin, yaml_utils
from apispec.exceptions import APISpecError
from apispec_plugins import utils as spec_utils


class FlaskPlugin(BasePlugin):
    """APISpec plugin for Flask"""

    def __init__(self):
        self.spec = None

    def init_spec(self, spec):
        super().init_spec(spec)
        self.spec = spec

    @staticmethod
    def _rule_view(view, app=None):
        if app is None:
            app = current_app

        view_funcs = app.view_functions
        endpoint = next(endpoint for endpoint, view_func in view_funcs.items() if view_func == view)
        if not endpoint:
            raise APISpecError(f"Could not find endpoint for view {view}")

        # WARNING: Assume 1 rule per view function for now
        rule = next(app.url_map.iter_rules(endpoint=endpoint))
        return rule

    def path_helper(
            self,
            operations=None,
            view=None,
            app=None,
            **kwargs
    ):
        """Path helper hook to set path specs from a Flask view."""
        rule = self._rule_view(view, app=app)
        if hasattr(view, 'view_class') and issubclass(view.view_class, MethodView):
            for method in view.methods:
                method_name = method.lower()
                method = getattr(view.view_class, method_name)
                operations[method_name] = spec_utils.load_specs_from_docstring(method.__doc__)
        return rule.rule
