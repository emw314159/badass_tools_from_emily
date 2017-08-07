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
from numpy import arange
import json

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
    # load yesterday's date
    #
    with open('/opt/predictions/phoenix/end.pickle') as f:
        end = pickle.load(f)

    #
    # load predictions
    #
    df = pd.read_csv('/opt/predictions/phoenix/predictions.csv')
    
    #
    # organize the predictions for display
    #
    data['buy'] = get_and_sort_given_predictions(df, 'prediction_buy')
    data['short'] = get_and_sort_given_predictions(df, 'prediction_short')

    #
    # compute trading day
    #
    if end.weekday() == 4:
        trading_day = end + datetime.timedelta(days=3)
    elif end.weekday() == 5:
        trading_day = end + datetime.timedelta(days=2)
    else:
        trading_day = end + datetime.timedelta(days=1)
    weekday = weekday_map[trading_day.weekday()]
    data['trading_date'] = weekday + ', ' + str(trading_day)
    data['end_date'] = weekday_map[end.weekday()] + ', ' + str(end)
    return JsonResponse({'data' : data})


#
# obtain key points on the ROC
#
def get_major_ROC_points(roc):

    thresholds = roc['thresholds']
    tpr = roc['tpr']
    fpr = roc['fpr']

    last_tpr_to_report = 0.
    last_fpr_to_report = 0.
    th_list = []
    tpr_list = []
    fpr_list = []
    threshold_steps = arange(1., -0.001, -0.001)
    for s in threshold_steps:
        for i, th in enumerate(thresholds):
            if th <= s:
                break
        if i == 0:
            continue
        distance_to_last = thresholds[i-1] - s
        distance_to_next = s - thresholds[i]
        distance = thresholds[i-1] - thresholds[i]
        prop_to_last = distance_to_last / distance
        prop_to_next = distance_to_next / distance
        tpr_diff = tpr[i] - tpr[i-1]
        tpr_to_report = tpr[i-1] + (prop_to_last * tpr_diff)
        fpr_diff = fpr[i] - fpr[i-1]
        fpr_to_report = fpr[i-1] + (prop_to_last * fpr_diff)

        if tpr_to_report - last_tpr_to_report >= 0.05 or fpr_to_report - last_fpr_to_report >= 0.05:
            th_list.append(s)
            tpr_list.append(tpr_to_report)
            fpr_list.append(fpr_to_report)

        last_tpr_to_report = tpr_to_report
        last_fpr_to_report = fpr_to_report

    to_return = []
    for s, t, f in zip(th_list, tpr_list, fpr_list):
        to_return.append({
            'threshold' : s,
            'tpr' : t,
            'fpr' : f,
            })

    return to_return



#
# view to return model details
#
@api_view(['POST'])
def model_report(request):

    data = {}

    #
    # load rates and thresholds
    #
    with open('/home/ec2-user/models/phoenix/FULL_SVM_BUY_fpr_tpr_thresholds.pickle') as f:
        buy = pickle.load(f)
    with open('/home/ec2-user/models/phoenix/FULL_SVM_SHORT_fpr_tpr_thresholds.pickle') as f:
        short = pickle.load(f)

    #
    # load model version
    #
    with open('/home/ec2-user/models/phoenix/version.json') as f:
        version = json.load(f)
    

    #
    # calculate major ROC positions
    #
    buy_ROC = get_major_ROC_points(buy)
    short_ROC = get_major_ROC_points(short)

    #
    # return data structure
    #
    data = {
        'buy_ROC' : buy_ROC,
        'short_ROC' : short_ROC,
        'version' : version,
    }

    return JsonResponse({'data' : data})
