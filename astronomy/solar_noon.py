#
# import useful libraries
#
import ephem
import pytz
from datetime import datetime

#
# calculate solar noon
#
def solar_noon(latitude, longitude, timezone):
    
    #
    # calculate solar noon in UTC
    #
    o = ephem.Observer()
    o.lat, o.long = str(latitude), str(longitude)
    sun = ephem.Sun()
    sunrise = o.previous_rising(sun, start=ephem.now())
    noon = o.next_transit(sun, start=sunrise)

    #
    # convert to timezone
    #
    hours_to_offset = float(timezone.replace('GMT', '')) / 100.
    days_to_offset = hours_to_offset / 24.
    noon = float(noon)
    local_noon = noon + days_to_offset

    #
    # create data structure to return
    #
    data_to_return = {
        'utc_noon' : str(ephem.Date(noon)).split(' ')[1],
        'local_noon' : str(ephem.Date(local_noon)).split(' ')[1],
    }

    return data_to_return

