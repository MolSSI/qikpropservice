import datetime
from ..factory import db
from flask import request, current_app
from flask_mongoengine import DoesNotExist

DEFAULT_TRACKING_NAME = "LiveDefault"


class TimeGuess(db.DynamicDocument):   # flexible schema, can have extra attributes
    """
    Stores average time per computation


    Attributes
    ----------
    time_per_kb: float
        time per kilobyte the operation took

    total_ops: int
        total number of operations

    """

    time_per_kb = db.FloatField()
    total_ops = db.IntField()
    tracking_name = db.StringField()

    meta = {
        'strict': True,     # allow extra fields
        'indexes': [
            "tracking_name",
        ]
    }

    def __str__(self):
        return 'Tracking Name: ' + str(self.tracking_name) \
               + ', Time Per kB (s): ' + str(self.time_per_kb) \
               + ', Total Number of measurements: ' + str(self.total_ops)


def check_time_data(tracking_name=DEFAULT_TRACKING_NAME):

    # Check if document exists
    try:
        time_data = db.timeguess.objects.get(tracking_name=tracking_name)
    except DoesNotExist:
        time_data = {"tracking_name": tracking_name,
                     "total_ops": 1,
                     "time_per_kb": 0
                     }

    return time_data


def update_estimate(operation_time, filesize_kb, tracking_name=DEFAULT_TRACKING_NAME):
    """

    operation_time: int/float
        in seconds of how long operation took
    filesize_kb: float
        Size of file in kb
    tracking_name: str, default is whatever DEFAULT_TRACKING_NAME is set to in time_guess.py
    """

    time_data = check_time_data(tracking_name=tracking_name)
    time_per_kb = time_data["time_per_kb"]
    total_ops = time_data["total_ops"]

    new_average = ((time_per_kb * total_ops) + (operation_time/filesize_kb)) / (total_ops + 1)

    time_data["time_per_kb"] = new_average
    time_data["total_ops"] += 1

    time_guess = TimeGuess(**time_data)

    time_guess.save()
