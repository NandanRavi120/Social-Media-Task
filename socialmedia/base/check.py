import datetime
import json

current_time = datetime.datetime.now()

expiration_time = current_time + datetime.timedelta(minutes=2)

expiration_time_iso = expiration_time.isoformat()

data = {
    'expiration_time': expiration_time_iso
}

json_data = json.dumps(data)