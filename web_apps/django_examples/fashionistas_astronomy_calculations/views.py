# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.template import loader
from rest_framework.decorators import api_view


#
# index
#
def index(request):
    template = loader.get_template('fac_index.html')
    return HttpResponse(template.render({}, request))

#
# view to return solar noon
#
@api_view(['POST'])
def solar_noon(request):
    solar_noon = {}
    if request.method == 'POST':

        solar_noon = sn.solar_noon(str(request.data['latitude']), str(request.data['longitude']), request.data['timezone'])

    return JsonResponse(solar_noon)


