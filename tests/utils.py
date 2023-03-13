from apispec import APISpec
from apispec.utils import build_reference


def get_paths(spec: APISpec) -> dict:
    return spec.to_dict()["paths"]


def get_schemas(spec):
    if spec.openapi_version.major < 3:
        return spec.to_dict()["definitions"]
    return spec.to_dict()["components"]["schemas"]


def get_responses(spec):
    if spec.openapi_version.major < 3:
        return spec.to_dict()["responses"]
    return spec.to_dict()["components"]["responses"]


def get_parameters(spec):
    if spec.openapi_version.major < 3:
        return spec.to_dict()["parameters"]
    return spec.to_dict()["components"]["parameters"]


def get_headers(spec):
    if spec.openapi_version.major < 3:
        return spec.to_dict()["headers"]
    return spec.to_dict()["components"]["headers"]


def get_schema(spec: APISpec, base: dict) -> dict:
    if spec.openapi_version.major >= 3 and "content" in base:
        return base["content"]["application/json"]["schema"]
    return base["schema"]


def build_ref(spec: APISpec, component_type, component_name) -> dict:
    return build_reference(component_type, spec.openapi_version.major, component_name)
