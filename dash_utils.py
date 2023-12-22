import dash
from jinja2 import Environment, PackageLoader, select_autoescape

from datetime import datetime as dt, timedelta, date
from dash import html, dcc

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

def add_dash_to_routes(app, dash_app, plaything_root, with_specification_id=True):
    """Adds a dash app to the Flask routes

    :param app: Flask app
    :type app: _type_
    :param dash_app: Python module containing code for the Dash app. Will contain a create_dash() function and have a view_name public property
    :type dash_app: _type_
    :param plaything_root: URL prefix. Used for playthings AND for "analytics things"
    :type plaything_root: str
    :param with_specification_id: Whether to include the <specification_id> placeholder. Required for playthings but forbidden for "analytics things".
    :type with_specification_id: bool
    :return: Flask app with added route
    :rtype: _type_
    """
    view_name = dash_app.view_name
    url_rule = f"{plaything_root}/{view_name}" + ("/<specification_id>" if with_specification_id else "")
    return dash_app.create_dash(app, url_rule, f"{plaything_root}/dash/{view_name}/")

# ------ Date Range Selection ------
# These two go together
def date_range_control(start_date_, end_date_, hide_pickers=False, hide_week=False, hide_month=False):
    return html.Div(
        [
            html.Div("Date Range", className="menu-title mb-2"),
            html.Div(
                [
                    dcc.DatePickerSingle(
                        id="date-start",
                        month_format="DD-MMM-YYYY",
                        display_format="DD-MMM-YYYY",
                        date=start_date_,
                        disabled=hide_pickers
                    ),
                    dcc.DatePickerSingle(
                        id="date-end",
                        month_format="DD-MMM-YYYY",
                        display_format="DD-MMM-YYYY",
                        date=end_date_,
                        disabled=hide_pickers
                    )
                ]
            ),
            html.Div(
                [
                    html.Button("-d", id="minus-day", className="btn btn-primary ms-1"),
                    html.Button("Yesterday", id="range-yesterday", className="btn btn-primary"),
                    html.Button("Today", id="range-today", className="btn btn-primary"),
                    html.Button("+d", id="plus-day", className="btn btn-primary me-1")
                ],
                className="btn-group mt-2", role="group"
            ),
            html.Div(
                [
                    html.Button("-w", id="minus-week", className="btn btn-primary ms-1"),
                    html.Button("7 Days", id="range-7days", className="btn btn-primary"),
                    html.Button("+w", id="plus-week", className="btn btn-primary me-1")
                ],
                hidden=hide_week,
                className="btn-group mt-2", role="group"
            ),
            html.Div(
                [
                    html.Button("-m", id="minus-month", className="btn btn-primary ms-1"),
                    html.Button("Last Month", id="range-lastmonth", className="btn btn-primary"),
                    html.Button("Current Month", id="range-thismonth", className="btn btn-primary"),
                    html.Button("+m", id="plus-month", className="btn btn-primary me-1")
                ],
                hidden=hide_month,
                className="btn-group mt-2", role="group"
            )
        ]
    )


def compute_range(context, start_date, end_date):  # date parameters are existing values, used by +/- controls
    ref_date = dt.utcnow().date()  # today's DATE as UTC; time component effectively 00:00:00
    start_date = dt.strptime(start_date, "%Y-%m-%d").date()  # want a date object not a time object
    end_date = dt.strptime(end_date, "%Y-%m-%d").date()

    if context == "range-7days":
        # last 7 days (6 full days + today)
        return ref_date - timedelta(days=6), ref_date
    elif context == "range-yesterday":
        # not including today
        ref_date -= timedelta(days=1)
        return ref_date, ref_date
    elif context == "range-lastmonth":
        # exclusively the last completed month
        if ref_date.month > 1:
            sd = date(ref_date.year, ref_date.month - 1, 1)
            ed = date(ref_date.year, ref_date.month, 1) - timedelta(days=1)
        else:
            sd = date(ref_date.year - 1, 12, 1)
            ed = date(ref_date.year - 1, 12, 31)
        return sd, ed
    elif context == "range-thismonth":
        # exclusively the current month, no matter how incomplete
        sd = date(ref_date.year, ref_date.month, 1)
        return sd, ref_date
    # plus/minus
    elif context == "minus-day":
        return start_date - timedelta(days=1), end_date - timedelta(days=1)
    elif context == "plus-day":
        return start_date + timedelta(days=1), end_date + timedelta(days=1)
    elif context == "minus-week":
        return start_date - timedelta(days=7), end_date - timedelta(days=7)
    elif context == "plus-week":
        return start_date + timedelta(days=7), end_date + timedelta(days=7)
    elif context == "minus-month":
        # these re-align dates to 1 month span starting on the 1st of a month
        if start_date.month == 1:
            return date(start_date.year - 1, 12, 1), date(start_date.year, 1, 1) - timedelta(days=1)
        else:
            return date(start_date.year, start_date.month - 1, 1), date(start_date.year, start_date.month, 1) - timedelta(days=1)
    elif context == "plus-month":
        if start_date.month == 12:
            return date(start_date.year + 1, 1, 1), date(start_date.year + 1, 2, 1) - timedelta(days=1)
        elif start_date.month == 11:
            return date(start_date.year, start_date.month + 1, 1), date(start_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            return date(start_date.year, start_date.month + 1, 1), date(start_date.year, start_date.month + 2, 1) - timedelta(days=1)
    else:
        # default to today
        return ref_date, ref_date


# ------ Single Day Selection -------
# These two go together and NB they are DIFFERENT to the Weather App, which is forewards from today, whereas this is today and backwards.
def day_control(for_date=None):
    if for_date is None:
        for_date = dt.now().date()
    return html.Div(
        [
            html.Div("Date:", className="menu-title"),
            dcc.DatePickerSingle(
                id="for_date",
                month_format="DD-MMM-YYYY",
                display_format="DD-MMM-YYYY",
                date=for_date
            ),
            html.Div(
                [
                    html.Button("-d", id="minus-day", className="btn btn-primary ms-1"),
                    html.Button("Yesterday", id="yesterday", className="btn btn-primary"),
                    html.Button("Today", id="today", className="btn btn-primary"),
                    html.Button("+d", id="plus-day", className="btn btn-primary me-1")
                ],
                className="btn-group", role="group"
            )
        ]
    )


def compute_day(context, for_date):  # date parameters is existing value, used by +/- controls
    ref_date = dt.now().date()
    for_date = dt.strptime(for_date, "%Y-%m-%d").date()  # want a date object not a time object

    if context == "yesterday":
        new_date = ref_date - timedelta(days=1)
    # plus/minus
    elif context == "minus-day":
        new_date = for_date - timedelta(days=1)
    elif context == "plus-day":
        new_date = for_date + timedelta(days=1)
    else:
        # default to today
        new_date = ref_date

    plus_day_disabled = ref_date == new_date

    return [new_date, plus_day_disabled]