import pkg_resources

__version__ = str(
    pkg_resources.get_distribution("apispec-plugins").parsed_version
)
