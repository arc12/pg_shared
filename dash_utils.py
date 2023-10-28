import dash
from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("pg_shared.blueprints", "templates"),
    autoescape=select_autoescape(),
)

def create_dash_app_util(server, url_rule, url_base_pathname, top_menu_items=()):
    """Create a Dash app with customized index layout

    :param server: base Flask app
    :param url_rule: url rule as endpoint in base Flask app.
    :param url_base_pathname: url base pathname used as dash internal route prefix. Must start and end with "/". Generally = "/dash{url_rule}/"
    """
    dash_app = dash.Dash(name=__name__, server=server, url_base_pathname=url_base_pathname, assets_folder="blueprints/static")  # remap assets folder to inside pg_shared

    dash_app.index_string = env.get_template("dash_layout.html").render(top_menu_items=top_menu_items)

    dash_app.server.add_url_rule(url_rule, endpoint=url_rule, view_func=dash_app.index)
    dash_app.routes.append(url_rule)

    # dash_app._favicon = "core_static/favicon.ico"

    return dash_app

def add_dash_to_routes(app, dash_app, plaything_root):
    """Adds a dash app to the Flask routes

    :param app: Flask app
    :type app: _type_
    :param dash_app: Python module containing code for the Dash app. Will contain a create_dash() function and have a view_name public property
    :type dash_app: _type_
    :param plaything_root: URL prefix
    :type plaything_root: str
    :return: Flask app with added route
    :rtype: _type_
    """
    view_name = dash_app.view_name
    return dash_app.create_dash(app, f"{plaything_root}/{view_name}/<specification_id>", f"{plaything_root}/dash/{view_name}/")