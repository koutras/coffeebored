from math import *
from datetime import *
def distance(place1, place2): #dintance in km
    R = 6373 #mean radiues of the earth(km) T 39 degrees from the equator
    lon2 = radians(place2[1])
    lon1 = radians(place1[1])
    lat2 = radians(place2[0])
    lat1 = radians(place1[0])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = pow((sin(dlat/2)),2) + cos(lat1) * cos(lat2) * pow((sin(dlon/2)),2)
    c = 2 * atan2( sqrt(a), sqrt(1-a) )
    d = R * c
    return d

def minutes_passed(time_new, time_old):
    time_passed=time_new - time_old
    return  time_passed.total_seconds()/60
    
