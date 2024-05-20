import json
from bson.objectid import ObjectId
import datetime
from dateutil import tz

class JSONEncoder(json.JSONEncoder):
    def __init__(self):
        super().__init__(ensure_ascii=False)

    # pylint: disable=method-hidden
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return int(o.replace(tzinfo=tz.gettz("UTC")).timestamp())

        return json.JSONEncoder().default(o)