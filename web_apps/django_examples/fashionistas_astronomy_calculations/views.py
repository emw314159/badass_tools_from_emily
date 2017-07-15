# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.template import loader
from rest_framework.decorators import api_view
#from rest_framework.response import Response

import pytz
from datetime import datetime
import ephem

#
# index
#
def index(request):
    template = loader.get_template('fac_index.html')
    return HttpResponse(template.render({}, request))

# #
# # view to return JSON containing a list of all time zones
# #
# @api_view(['GET', 'POST'])
# def get_all_timezones(request):
#     data_to_return = {'all_timezones' : pytz.all_timezones}
#     #return JsonResponse(data_to_return)
#     return Response(data_to_return)

#
# view to return solar noon
#
@api_view(['POST'])
def solar_noon(request):
    data_to_return = {}
    if request.method == 'POST':

        #
        # calculate solar noon in UTC
        #
        o = ephem.Observer()
        o.lat, o.long = str(request.data['latitude']), str(request.data['longitude'])
        sun = ephem.Sun()
        sunrise = o.previous_rising(sun, start=ephem.now())
        noon = o.next_transit(sun, start=sunrise)

        #
        # convert to timezone
        #
        user_timezone = request.data['timezone']
        hours_to_offset = float(user_timezone.replace('GMT', '')) / 100.
        days_to_offset = hours_to_offset / 24.
        noon = float(noon)
        local_noon = noon + days_to_offset

        #
        # set data to return
        #
        data_to_return['utc_noon'] = str(ephem.Date(noon)).split(' ')[1]
        data_to_return['local_noon'] = str(ephem.Date(local_noon)).split(' ')[1]

    return JsonResponse(data_to_return)


    

    


