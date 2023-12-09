from os import environ, makedirs, path, listdir
import sys
import json
import uuid
import pickle

import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler

from azure.cosmos import CosmosClient
from azure.core.exceptions import ServiceRequestError

from dash import html

from pg_shared import blueprints

from flask import request, abort
from werkzeug.exceptions import HTTPException

import pandas as pd  # pandas import is responsible for slow start-up of the app so use of "keep_warm" timerTrigger functions is recommended
import markdown
from csv import DictReader

# this suppresses the spammy logging of request and response headers for the CosmosDB interactions. It may suppress more...
cosmos_logger = logging.getLogger("azure")
cosmos_logger.setLevel(logging.WARN)

# for Flask exceptions - see prepare_app()
def basic_error(e):
    if isinstance(e, HTTPException):
        # simply pass through HTTP 404 etc which will have been explicitly set via an abort()
        return e
    
    # this covers other errors, which would normally ripple through as a 500.
    logging.error("Error processing request to {}. Exception information follows:".format(request.path))
    logging.exception(e)
    msg = f"An error occurred. It has been logged.<hr/> {e.__class__.__name__} : {e}"
    return msg

def prepare_app(flask_app, url_prefix):
    """Does standard prep of the Flask app object

    :param flask_app: _description_
    :type flask_app: _type_
    """
    # required for session id (used to sign cookie)
    if "FLASK_COOKIE_KEY" not in environ:
        logging.warn("Using default cookie signing key for Flask session.")
    flask_app.secret_key = environ.get("FLASK_COOKIE_KEY", "WGFEhV5j3muB5A")

    # shared templates and CSS
    flask_app.register_blueprint(blueprints.make_core_bp(url_prefix))

    # log exceptions
    flask_app.register_error_handler(Exception, basic_error)

    return flask_app

def read_json_file(json_path: str, soft_error: bool = False) -> dict | str:
    """
    Reads JSON into a dict with logging of file not found and parse issues. Makes for more intelligable logs.

    :param json_path: _description_
    :type json_path: str
    :param soft_error: If True, parse errors will not be logged but a string of the JSONDecodeError returned rather than dict of JSON, defaults to False
    :type soft_error: bool, optional
    :return: dict of JSON or string of parsing error if relevant and soft_error is True. Failed parse or file not found returns empty dict if soft_error is False
    :rtype: dict | str
    """
    retval = dict()
    try:
        with open(json_path, 'r', encoding="utf-8") as j:
            retval = json.load(j)
    except FileNotFoundError:
        logging.critical(f"Failed to find JSON file at: {json_path}.")
    except json.decoder.JSONDecodeError as ex:  # parse
        if soft_error:
            retval = f"{ex}."
        else:
            logging.critical(f"Loading {json_path} could not be parsed. See next log.")
            logging.exception(ex)
    return retval


class Core:
    # plaything_name param locates plaything config, is used in record_activity() and should be the first URL path part
    def __init__(self, plaything_name: str):
        self.plaything_name = plaything_name

        # check env vars to determine whether running as a function app running on Azure
        # Used to use "AzureWebJobsStorage" but it now gives True for local use since adding the Timer
        self.is_function_app = "WEBSITE_CONTENTSHARE" in environ

        # set up python logging if required. Function apps log into Azure Application Insights, which requires no spec here, but for other use:
        if not self.is_function_app:
            makedirs("../Logs", exist_ok=True)
            logging.basicConfig(
                handlers=[
                    RotatingFileHandler(f'../Logs/{plaything_name}.log', maxBytes=100000, backupCount=5),
                    StreamHandler(sys.stdout)
                ],
                level=logging.INFO,  # TODO obtain from config
                format='%(asctime)s [%(levelname)s] %(message)s'
            )

        # load core config 
        self.config_base_path = "/Config" if self.is_function_app else "../Config"
        self.config_plaything_path = path.join(self.config_base_path, self.plaything_name)
        if not path.exists(self.config_base_path):
            logging.critical(f"Failed to find config base path at: {path.abspath(self.config_base_path)}")
            return
        self.core_config = read_json_file(path.join(self.config_base_path, "core_config.json"))

        # ... and available plaything specifications
        self.specification_ids = []
        if path.exists(self.config_plaything_path):
            self.specification_ids = [f[:-5] for f in listdir(self.config_plaything_path) if f.endswith(".json")]
        if len(self.specification_ids) == 0:
            logging.warning(f"No specifications found at: {self.config_plaything_path}")

        # how should the URL paths start
        self.plaything_root = "/" + self.plaything_name.lower() if self.core_config.get("plaything_name_in_path", False) else ""

        # enable timerTrigger
        self.keep_warm = self.core_config.get("keep_warm", False)
        
        # language code for built-in strings (i.e. declared in code, not the plaything specification JSON)
        # self.lang = self.core_config.get("lang", "en")

        # TODO take this from core config
        # whether to relay record_activity() to Python logger - generally for debugging
        self.relay_activity = True
        
        # set up cosmos db (read in setting and access key)
        # NOTE: must set up database and container in CosmosDB (in Azure or emulator); set plaything_name as the partition key
        self.record_activity_config = self.core_config.get("activity", {"enabled": False})
        self.record_activity_container = None
        if self.record_activity_config.get("enabled", False):
            try:
                cosmos_client = CosmosClient(environ["PLAYGROUND_COSMOSDB_URI"], credential=environ["PLAYGROUND_COSMOSDB_KEY"])
                db = cosmos_client.get_database_client(self.record_activity_config["database"])
                self.record_activity_container = db.get_container_client(self.record_activity_config["container"])
            except KeyError as ex:
                logging.error("Failed to set up activity logging. Likely cause is a mis-configuration of environment variables or defective core_config.json. "
                              f"Missing key is: {ex}")
            except ServiceRequestError as ex:
                logging.error("Failed to set up activity logging due to a ServiceRequestError when attempting a CosmosDB connection.")
        else:
            logging.warn("Activity logging is disabled. Refer to core_config.json.")

    def get_specification(self, specification_id, flask_404=True):
        """_summary_

        :param specification_id: _description_
        :type specification_id: _type_
        :param flask_404: If True, check whether the passed specification id is known and if not causes a Flask abort(404) with a suitable messsage, defaults to True
        :type flask_404: bool, optional
        :return: _description_
        :rtype: _type_
        """
        if flask_404 and specification_id not in self.specification_ids:
            msg = f"Request with invalid specification id = {specification_id} for plaything {self.plaything_name}"
            logging.warn(msg)
            abort(404, msg)
        return Specification(self.config_plaything_path, specification_id)
        
    def get_specifications(self, include_disabled=False, check_assets=[], check_optional_assets=[]):
        """
        Also performs a check of assets (conditional on parameters)

        :param include_disabled: _description_, defaults to False
        :type include_disabled: bool, optional
        :param check_assets: defaults to []. Either a list of keys in asset_map element of the specification OR a pointer to a function which will take
            the details element as input and return a list of keys. This allows for plaything-specific cases where the details determine which assets are needed.
        :type check_assets: list|callable, optional
        :param check_optional_assets: _description_, defaults to []
        :type check_optional_assets: list, optional
        :return: _description_
        :rtype: _type_
        """

        specifications = list()
        for specification_id in self.specification_ids:
            spec = Specification(self.config_plaything_path, specification_id)
            if include_disabled or spec.enabled:
                try:
                    check_assets_ = check_assets(spec.detail) if callable(check_assets) else check_assets
                except:
                    check_assets_ = []
                if len(check_assets_ + check_optional_assets) > 0:
                    spec.check_assets(check_assets_, optional_keys=check_optional_assets, update_spec=True)  # updates spec.summary in place
                specifications.append(spec)
        
        return specifications

    def record_activity(self, plaything_part, specification_id, flask_session, activity=None, referrer=None, tag=None):
        # log session id (creating as required), plaything name and part, HTTP referrer, tag + pt-specific activity.
        # stored JSON uses "_" prefixed keys for generic (non-pt-specific) parts
        # Taken from query-string (in flask request object):
        # - tag (passed along from initial referring URL) allows the person creating content with the PT to give some contextual info (e.g. could have one link for males and females with m/f as tag)
        

        if "session_id" not in flask_session:
            session_id = str(uuid.uuid1())
            flask_session["session_id"] = session_id
            logging.info(f"Create new session id: {session_id}")

        record_payload = {
            "plaything_name": self.plaything_name,
            "plaything_part": plaything_part,
            "specification_id": specification_id,
            "session_id": flask_session["session_id"],
            "referrer": referrer,
            "tag": tag
        }
        if activity is not None:
            record_payload.update(activity)

        if self.record_activity_container is not None:
            self.record_activity_container.create_item(record_payload, enable_automatic_id_generation=True)

        if self.relay_activity:
            logging.info(json.dumps(record_payload))  # no indents
        

class LangstringsBase:
    langstrings = dict()  # override in derived class
    def __init__(self, lang):
        self.lang  = lang

    def get(self, string_code):
        # get the lang string for the passed string_code, returning warning placeholders if either the string code is not known or doesnt support the lang
        return self.langstrings.get(string_code, f"!!{string_code}!!").get(self.lang, f"!!{string_code}.{self.lang}!!")


class Specification:
    def __init__(self, dir_path, specification_id):
        
        self.dir_path = dir_path
        self.specification_id = specification_id

        # read JSON with capture of parsing error
        specification = read_json_file(path.join(dir_path, f"{specification_id}.json"), soft_error=True)
        if isinstance(specification, str):
            specification = {
                "title": f"Broken JSON file for specification id = {specification_id}.",
                "summary": f"Error is: {specification}"
                }
        # and file not found or empty spec
        if len(specification) == 0:            
            specification = {"title": f"Nothing found for specification id = {specification_id}."}

        # self.specification = specification
        self.enabled = specification.get("enabled", False)
        self.title = specification.get("title", f"<missing title for {specification_id}>")
        self.summary = specification.get("summary", "")
        self.lang = specification.get("lang", "en")
        self.initial_view = specification.get("initial_view", None)
        self.detail = specification.get("detail", dict())
        self.menu_items = specification.get("menu_items", "*")
        self.asset_map = specification.get("asset_map", dict())

    def make_menu(self, menu, langstrings, base_path, current_view, query_string="", for_dash=False):
        # Somewhat messy to include so much formatting here, but using the Jinja template approach runs into problems with Dash because
        # we only get to know the specification id when a request is made (the page layout has been created on app load)

        if "menu=1" not in query_string:
            return ""

        # handle "specification" control
        use_menu_items = {}
        if isinstance(self.menu_items, list):
            for v in self.menu_items:
                if v in menu:
                    use_menu_items[v] = menu[v]
                # else ignore if the config lists a view which does not exist
        else:
            if self.make_menu_items == "*":
                use_menu_items = menu

        if len(use_menu_items) == 0:
            return ""

        # build menu HTML including highlight of active page
        if len(query_string) > 0:
            if query_string[0] != "?":
                query_string = "?" + query_string
        items = []
        for item_view, item_ls_key in use_menu_items.items():
            item_title = langstrings.get(item_ls_key)
            active = current_view == item_view
            item_path = f"{base_path}/{item_view}/{self.specification_id}{query_string}"

            link_class_name = "nav-link px-2 " + ("link-secondary" if active else "link-dark")
            if for_dash:
                items.append(html.Li(html.A(item_title, href=item_path, className=link_class_name)))
            else:
                items.append(f'<li><a href="{item_path}" class="{link_class_name}">{item_title}</a></li>')

        if for_dash:
            menu = html.Header(
                [
                    html.Span("DLP | ", className="ms-2"),
                    html.Ul(items, className="nav col-md-auto justify-content-start mb-md-0"
                    )
                ],
                className="d-flex flex-row flex-wrap align-items-center justify-content-start py-2 mb-4 border-bottom"
            )
        else:
            header = """
            <header class="d-flex flex-row flex-wrap align-items-center justify-content-start py-2 mb-3 border-bottom">    
                <span class="ms-2">DLP |</span>
                <ul class="nav col-md-auto justify-content-start mb-md-0">{items_string}</ul>
            </header>"""
            menu = header.format(items_string="\n".join(items))
        
        return menu

    def check_assets(self, required_keys=[], optional_keys=[], update_spec=False):
        """Checks the supplied keys are present (required) and that the mapped files can be found (required and optional)

        :param required_keys: _description_, defaults to []
        :type required_keys: _type_
        :param optional_keys: _description_, defaults to []
        :type optional_keys: list, optional
        :param update_spec: if True, the summary property will be modified to describe any problems found.
        :type update_spec: boolean
        :returns: dict with key = asset key and value = the problem. Only for problem cases.
        """
        problems = {k: "missing from specification" for k in required_keys if k not in self.asset_map}

        # TODO add JSON file syntax validation check

        for k in required_keys + optional_keys:
            if k in self.asset_map:
                asset_file = self._make_asset_path(k)
                if not path.exists(asset_file):
                    problems[k] = f"failed to find mapped file {asset_file}"
        
        if update_spec and (len(problems) > 0):
            self.summary = self.summary + " *** Asset map issues: " + "; ".join([f"{k} - {v}" for k, v in problems.items()]) + "."

        return problems

    def _make_asset_path(self, asset_key):
        return path.join(self.dir_path, "assets", self.asset_map.get(asset_key))

    def _asset_preload(self, asset_key, asset_type):
        """Performs checks which are useful prior to attempting to load an asset:
        - is the key present
        - is the mapped file present
        - does the file have the correct extension

        :param asset_key: key in specification asset_map
        :type asset_key: str
        :param asset_type: file type extension expected. do not include "."
        :type asset_type: str
        :return: Path to asset file if all checks pass, otherwise None.
        :rtype: str|None
        """
        if asset_key not in self.asset_map:
            logging.error(f"Failed to find asset key {asset_key} for specification {self.specification_id}.")
            return None

        asset_file = self._make_asset_path(asset_key)
        if not path.exists(asset_file):
            logging.error(f"Failed to find file {asset_file} for asset key {asset_key} for specification {self.specification_id}.")
            return None
        
        if path.splitext(asset_file)[1].lower()[1:] != asset_type.lower():
            logging.error(f"Asset file {asset_file} for asset key {asset_key} for specification {self.specification_id} was of the wrong type; expected {asset_type}.")
            return None
        
        return asset_file
    
    def load_asset_dataframe(self, asset_key, dtypes=None):
        asset_file = self._asset_preload(asset_key, "csv")
        if asset_file is None:
            return None

        return pd.read_csv(asset_file, dtype=dtypes)

    def load_asset_records_dict(self, asset_key):
        """Reads a CSV file and returns a list of dicts, where each dict represents one row and uses for its keys the entries in the first line.

        All values are strings.

        :param asset_key: _description_
        :type asset_key: _type_
        :return: _description_
        :rtype: _type_
        """
        asset_file = self._asset_preload(asset_key, "csv")
        if asset_file is None:
            return None
        
        with open(asset_file, 'r', newline='') as f:
            reader = DictReader(f)
            records = list(reader)
        
        return records

    def load_asset_markdown(self, asset_key, render=False, replacements=None):
        """Loads a markdown file by its asset_map key and optionally renders.

        :param asset_key: key to member of specification "asset_map"
        :type asset_key: str
        :param render: Whether to convert the markdown to HTML, defaults to False
        :type render: bool, optional
        :param replacements: Dict containing replacements to use in .format() method of the markdown, defaults to None
        :type replacements: dict|None, optional
        :return: markdown or html
        :rtype: str
        """
        asset_file = self._asset_preload(asset_key, "md")
        ret_val = None
        if asset_file is not None:
            with open(asset_file, 'r') as f:
                md = f.read()
            
            if render:
                if replacements is None:
                    ret_val = markdown.markdown(md)
                else:
                    ret_val = markdown.markdown(md.format(**replacements))
            else:
                ret_val = md
        return ret_val

    def load_asset_object(self, asset_key):
        # un-pickles something
        asset_file = self._asset_preload(asset_key, "pickle")
        if asset_file is None:
            return None
    
        with open(asset_file, 'rb') as f:
            return pickle.load(f)
        
    def load_asset_json(self, asset_key):
        # arbitrary JSON, parsed to a dict
        asset_file = self._asset_preload(asset_key, "json")
        if asset_file is None:
            return None
    
        return read_json_file(asset_file)
