import logging
import requests
from os import environ

def timer_main(timer, core, plaything_name):
    """Generic handler for use in main() of the *Timer trigger functions

    :param timer: _description_
    :type timer: _type_
    :param core: _description_
    :type core: _type_
    :param plaything_name: _description_
    :type plaything_name: _type_
    """
    if core.keep_warm:
        if timer.past_due:
            logging.info('The timer is past due!')
        
        url_base = environ.get("PLAYGROUND_PING_URL_BASE", None)  # e.g. = "https://dlpg-test1.azurewebsites.net"

        if url_base is None:
            logging.error(f"Environ PLAYGROUND_PING_URL_BASE is not set; abort pinging {plaything_name}.")
            exit(1)  # make sure this shows up in the monitor as a fai.
        else:
            url = f"{url_base}/{plaything_name}/ping"
            try:
                req = requests.get(url, timeout=20)
                logging.info(f"Ping {url} from timerTrigger => HTTP {req.status_code}, Content: {req.text}")
            except requests.exceptions.ConnectTimeout:
                logging.warn(f"Request to {url} from timerTrigger timed out (connection).")
                exit(1)
            except requests.exceptions.ReadTimeout:
                logging.warn(f"Request to {url} from timerTrigger timed out (read).")
                exit(1)
