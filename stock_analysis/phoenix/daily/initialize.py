
def initialize():

    #
    # load useful libraries
    #
    import json
    import datetime
    import pickle
    import sys
    import os

    #
    # load configuration
    #
    with open(sys.argv[1]) as f:
        config = json.load(f)

    #
    # user settings
    #
    runtime_output_directory = config['runtime_output_directory']

    # remove runtime output directory
    os.system('rm -R ' + runtime_output_directory)
    os.system('mkdir ' + runtime_output_directory)

    #
    # establish yesterday's date
    #
    now = datetime.datetime.now()

    if now.weekday() == 0:
        dt = -3
    elif now.weekday() == 6:
        dt = -2
    else:
        dt = -1

    end = (now + datetime.timedelta(days=dt)).date()
    with open(runtime_output_directory + '/end.pickle', 'w') as f:
        pickle.dump(end, f)

