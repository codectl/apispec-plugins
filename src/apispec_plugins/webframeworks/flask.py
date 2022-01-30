from flask import current_app
from flask.views import MethodView

from apispec import BasePlugin, yaml_utils
from apispec.exceptions import APISpecError


class FlaskPlugin(BasePlugin):
    """APISpec plugin for Flask"""

    def init_spec(self, spec):
        super().init_spec(spec)

    @staticmethod
    def _rule_view(view, app=None):
        if app is None:
            app = current_app

        endpoint = None
        for ept, view_func in app.view_functions.items():
            if view_func == view:
                endpoint = ept
        if not endpoint:
            raise APISpecError(f"Could not find endpoint for view {view}")

        # WARNING: Assume 1 rule per view function for now
        rule = next(app.url_map.iter_rules(endpoint=endpoint))
        return rule

    def path_helper(
            self,
            view=None,
            app=None,
            **kwargs
    ):
        """Path helper that allows passing a Flask view function."""
        rule = self._rule_view(view, app=app)
        # if hasattr(view, 'view_class') and issubclass(view.view_class, MethodView):
        #     for method in view.methods:
        #         if method in rule.methods:
        #             method_name = method.lower()
        #             method = getattr(view.view_class, method_name)
        #             operations[method_name] = yaml_utils.load_yaml_from_docstring(
        #                 method.__doc__
        #             )
        return rule.rule
