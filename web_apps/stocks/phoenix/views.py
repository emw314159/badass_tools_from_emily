# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.template import loader
from rest_framework.decorators import api_view

import pandas as pd
import pickle
import datetime

#
# weekday map
#
weekday_map = {
    0 : 'Monday',
    1 : 'Tuesday',
    2 : 'Wednesday',
    3 : 'Thursday',
    4 : 'Friday',
    5 : 'Saturday',
    6 : 'Sunday',
}

#
# index
#
def index(request):
    template = loader.get_template('phoenix_index.html')
    return HttpResponse(template.render({}, request))

#
# index
#
def info(request):
    template = loader.get_template('phoenix_model_info.html')
    return HttpResponse(template.render({}, request))


#
# get and sort given prediction
#
def get_and_sort_given_predictions(df, column):
    score_to_symbol = {}
    for symbol, score in zip(df['symbol'], df[column]):
        if not score_to_symbol.has_key(score):
            score_to_symbol[score] = {}
        score_to_symbol[score][symbol] = None
    score_list = sorted(score_to_symbol.keys())
    score_list.reverse()
    return_list = []
    for score in score_list:
        for symbol in sorted(score_to_symbol[score].keys()):
            return_list.append({
                'score' : score,
                'symbol' : symbol,
            })
    return return_list
    


#
# view to return data
#
@api_view(['POST'])
def report(request):

    data = {}

    #
    # load predictions
    #
    df = pd.read_csv('/home/ec2-user/predictions/phoenix/predictions.csv')
    
    #
    # organize the predictions for display
    #
    data['buy'] = get_and_sort_given_predictions(df, 'prediction_buy')
    data['short'] = get_and_sort_given_predictions(df, 'prediction_short')

    #
    # load yesterday's date
    #
    with open('/home/ec2-user/predictions/phoenix/end.pickle') as f:
        end = pickle.load(f)

    #
    # compute trading day
    #
    trading_day = end + datetime.timedelta(days=1)
    weekday = weekday_map[trading_day.weekday()]
    data['date'] = weekday + ', ' + str(trading_day)

    return JsonResponse({'data' : data})
