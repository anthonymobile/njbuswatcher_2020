from mongoengine import *

connect('bustest2', host='mongodb://localhost:27017/newtestdb')

class Bus(Document):
    lat = StringField(max_length=50)
    lon = StringField(max_length=50)
    ar = StringField(max_length=50)


insert_it = Bus(lat='trr',lon='3434',ar='fdsf44').save()
for bus in Bus.objects:
    print(bus.lat)

