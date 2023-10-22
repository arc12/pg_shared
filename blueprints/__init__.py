from flask import Blueprint

def make_core_bp(static_prefix: str|None = None):
    static_url_path = "/core_static" if static_prefix is None else f"/{static_prefix}/core_static"
    return Blueprint("core", __name__, template_folder="templates", static_folder="static", static_url_path=static_url_path)
