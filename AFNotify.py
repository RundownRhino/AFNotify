import json
import logging
import time
import sys

from requests import get, RequestException

status_links = {"eu": r"https://eu.acolytefight.io/status", "us": r"https://us.acolytefight.io/status"}
request_period = 300  # seconds (5 minutes)
to_notify = True  # whether to enable desktop notifications
notification_dur = 10  # seconds - note that the program can't be shut down when the notification is showing
thresholds = {
    "eu": 4}  # how many players to notify about. Omit a server to ignore. No requests are made to ignored servers.
log_all = True  # whether to log all the numbers

if to_notify:
    from pynotifier import Notification  # type:ignore

# configure logging to log into a file and add some data
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    filemode="a",
    filename="AFNotifyLog.txt",
    level=logging.INFO  # change to DEBUG for tons of debug stuff
)
# also log to console if run in it:
logging.getLogger().addHandler(logging.StreamHandler())

logging.critical("Process started.")

# ignore servers with no thresholds:
status_links = {k: v for k, v in status_links.items() if k in thresholds}
if not status_links:
    raise ValueError("Nothing to watch for!")

logging.critical("Starting to watch.")


# handling of uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

while True:
    counts = {}
    for key, link in status_links.items():
        # noinspection PyBroadException
        try:
            response = get(link)
        except RequestException:
            logging.exception(f"Failed getting a response from server {key}.")
            continue
        # noinspection PyBroadException
        try:
            if response.status_code == 200:
                data = response.json()
                count = data["numPlayers"]
                counts[key] = count
        except:  # KeyError, most likely, but catch and log all
            logging.exception(f"Failed handling a response from server {key}.")
            logging.debug(f"Response content: {repr(response.content)}")

    if log_all:
        logging.info(f"Fetched counts: {json.dumps(counts)}")

    if to_notify:
        for k, count in counts.items():
            if count >= thresholds[k]:
                Notification(
                    title="AFNotify Alert",
                    description=f'{count} players are currently on {k.upper()}!',
                    duration=notification_dur,
                    urgency=Notification.URGENCY_NORMAL
                ).send()
                break  # don't send more than one notification, even if there's several servers
    time.sleep(request_period)
