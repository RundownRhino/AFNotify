from requests import get
from pynotifier import Notification
import logging, time

status_links = {"eu": r"https://eu.acolytefight.io/status", "us": r"https://us.acolytefight.io/status"}
request_period = 300  # seconds (5 minutes)
notification_dur = 10  # seconds - note that the program can't be shut down when the notification is showing
thresholds = {
    "eu": 4}  # how many players to notify about. Omit a server to ignore. No requests are made to ignored servers.
log_all = True  # whether to log all the numbers

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
while True:
    counts = {}
    for key, link in status_links.items():
        response = get(link)
        try:
            if response.status_code == 200:
                data = response.json()
                count = data["numPlayers"]
                counts[key] = count
        except:  # KeyError, most likely, but catch and log all
            logging.exception(f"Failed handling a response from server {key}.")
            logging.debug(f"Response content: {response.content}")

    if log_all:
        logging.info(f"Fetched counts: {counts}")

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
