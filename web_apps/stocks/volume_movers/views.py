# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.template import loader
from rest_framework.decorators import api_view
from numpy import mean, median

import json

# Create your views here.

#
# index
#
def index(request):
    template = loader.get_template('volume_movers_index.html')
    return HttpResponse(template.render({}, request))

#
# view to return data
#
@api_view(['POST'])
def volume_movers_report(request):

    with open('/home/ec2-user/badass_tools_from_emily/stock_analysis/runtime/output/report.json') as f:
        data = json.load(f)
        for e in data:
            e['mean'] = mean(e['all_scores'])
            e['median'] = median(e['all_scores'])

    return JsonResponse({'data' : data})


