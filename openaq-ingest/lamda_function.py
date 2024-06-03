import pg8000.native
import json
import os

try:
    con = pg8000.native.Connection(
        os.getenv('db_user') ,
        password=os.getenv('db_passwd'), 
        host=os.getenv('db_host'), 
        port=os.getenv('db_port'), 
        database=os.getenv('db_database'))
    print("connection made")
except:
   print("connection error") 

def lambda_handler(event, context):
    delete_old_readings()
    for r in event['Records']:
        message = json.loads(json.loads(r['body'])['Message'])
        create_location(message)
        create_reading(message)    
    
def create_location(message):
    con.run('INSERT INTO "Locations" VALUES (:id, :location, :lat, :lon, :country, :city) ON CONFLICT DO NOTHING',
                id=message['locationId'],
                location=message['location'],
                lat=message['coordinates']['latitude'],
                lon=message['coordinates']['longitude'],
                country=message['country'],
                city=message['city']
                )

def create_reading(message):
    con.run('INSERT INTO "Readings" VALUES (:location_id, :parameter, :value, :unit, :timestamp)',
                location_id=message['locationId'],
                parameter=message['parameter'],
                value=message['value'], 
                unit=message['unit'],
                timestamp=message['date']['utc'])
    
def delete_old_readings():
    con.run('DELETE FROM "Readings" WHERE timestamp < NOW() - INTERVAL \'24 hours\'')
    
# def get_parameters():
#     con.run('DELETE FROM "Parameters"')
#     url = "https://api.openaq.org/v2/parameters?limit=100&page=1&offset=0&sort=asc&order_by=id"
#     headers = {"accept": "application/json"}
#     response = requests.get(url, headers=headers)
#     for param in response.json()['results']:
#         con.run('INSERT INTO "Parameters" VALUES (:id, :parameter)',
#                 id=param['name'],
#                 parameter=param['description'])