import requests
import pytz
from datetime import datetime, timedelta
import json

# now = datetime.now(pytz.timezone('Europe/Zurich')).strftime('%Y-%m-%d %H:%M:%S %z')

url = 'http://api.thingspeak.com/channels/2755053/bulk_update.json'


myobj = ({
	"write_api_key": "S8MPZ4SE50EMGGA6",
	"updates": [{
			"created_at": '2024-11-21 18:6:27 +0100',#datetime.now(pytz.timezone('Europe/Zurich')).strftime('%Y-%m-%d %H:%M:%S %z'),
			"field1": "1.0",
			"field2": "2.0",
            "field3": "39.3"
		},
		{
			"created_at": '2024-11-21 18:6:28 +0100',#(datetime.now(pytz.timezone('Europe/Zurich'))+ timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S %z'),
			"field1": "100.1",
			"field2": "200.2",
            "field3": "399.2",
			"status": "well done"
		}
	]
})




 
x = requests.post(url, json = myobj)

print(x.reason)
print(x.text)
