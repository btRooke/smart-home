from utilities import *
from time import sleep

DELAY = 60 # in seconds

"""
Session cookie expires (full stop) after FINAL_COOKIE_EXPIRY_DAYS.
Session cookie also expires if it hasn't been interacted with in
COOKIE_EXPIRY_IF_NO_INTERACTION_DAY i.e. if an API command hasn't been called
using it.
"""

FINAL_COOKIE_EXPIRY_DAYS = 7
COOKIE_EXPIRY_IF_NO_INTERACTION_DAYS = 2

while True:
    # Checking active sessionIDs

    with DBConnection() as conn:
        query = "SELECT sessionID, sessionCreationTime, lastRequestTime FROM session;"
        session_records = conn.call(query)

    session_records = [{"id": record[0], "creation_time": record[1], "last_request_time": record[2]} for record in session_records]

    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for record in session_records:
        # Checking FINAL_COOKIE_EXPIRY_DAYS

        creation_date = datetime.datetime.strptime(record["creation_time"], "%Y-%m-%d %H:%M:%S")
        delta = datetime.timedelta(days = FINAL_COOKIE_EXPIRY_DAYS)
        expiry_date = creation_date + delta

        if expiry_date > current_date:
            with DBConnection() as conn:
                query = "DELETE FROM session WHERE sessionID={};"
                query = query.format(record["session_id"])
                conn.call(query)
                continue

        # Checking COOKIE_EXPIRY_IF_NO_INTERACTION_DAYS

        delta = current_date - datetime.datetime.strptime(record["creation_time"], "%Y-%m-%d %H:%M:%S")
        if delta.days > COOKIE_EXPIRY_IF_NO_INTERACTION_DAYS:
            with DBConnection() as conn:
                query = "DELETE FROM session WHERE sessionID={};"
                query = query.format(record["session_id"])
                conn.call(query)
                continue


    sleep(60)
