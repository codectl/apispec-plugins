from flask import current_app
from flask.views import MethodView

from apispec import BasePlugin, yaml_utils
from apispec.exceptions import APISpecError


class FlaskPlugin(BasePlugin):
    """APISpec plugin for Flask"""

    @staticmethod
    def _rule_for_view(view, app=None):
        if app is None:
            app = current_app

        view_funcs = app.view_functions
        endpoint = None
        for ept, view_func in view_funcs.items():
            if view_func == view:
                endpoint = ept
        if not endpoint:
            raise APISpecError(f"Could not find endpoint for view {view}")

        # WARNING: Assume 1 rule per view function for now
        rule = app.url_map._rules_by_endpoint[endpoint][0]
        return rule

    def path_helper(self, operations, *, view, app=None, **kwargs):
        """Path helper that allows passing a Flask view function."""
        rule = self._rule_for_view(view, app=app)
        operations.update(yaml_utils.load_operations_from_docstring(view.__doc__))
        if hasattr(view, "view_class") and issubclass(view.view_class, MethodView):
            for method in view.methods:
                if method in rule.methods:
                    method_name = method.lower()
                    method = getattr(view.view_class, method_name)
                    operations[method_name] = yaml_utils.load_yaml_from_docstring(
                        method.__doc__
                    )
        return rule.rule
