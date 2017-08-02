
def get_two_day_stocks():

    #
    # load useful libraries
    #
    import json
    import datetime
    import sys
    import pickle
    import pandas_datareader as pdr

    from badass_tools_from_emily.misc import chunk


    #
    # load configuration
    #
    with open(sys.argv[1]) as f:
        config = json.load(f)

    #
    # user settings
    #
    runtime_output_directory = config['runtime_output_directory']
    volume_threshold = config['volume_threshold']

    #
    # load end date
    #
    with open(runtime_output_directory + '/end.pickle') as f:
        end = pickle.load(f)

    #
    # load volumes that move
    #
    with open(runtime_output_directory + '/volume_movers.json') as f:
        volume_movers = json.load(f)

    #
    # find volumes that moved in chunks
    #
    def find_volumes_that_moved_in_chunks(volume_list, n, start, end, volumes_that_moved_yesterday):

        errors = []
        chunks = chunk(volume_list, n)

        print
        print len(chunks)
        print

        for i, c in enumerate(chunks):

            print i

            try:
                panel = pdr.get_data_yahoo(symbols=c, start=start, end=end)

                for symbol in c:
                    df = panel.minor_xs(symbol)
                    df = df.sort_index()
                    d_volume = [(100. * (j - i) / i) for i, j in zip(df['Volume'][0:-1], df['Volume'][1:])]
                    if d_volume[-1] >= volume_threshold:
                        volumes_that_moved_yesterday.append(symbol)
            except:
                errors.extend(c)

        return errors

    #
    # get two day stocks
    #
    volumes_that_moved_yesterday = []
    volume_list = sorted(volume_movers.keys())
    start = (end + datetime.timedelta(days=-8))

    errors = find_volumes_that_moved_in_chunks(volume_list, 200, start, end, volumes_that_moved_yesterday)
    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print

    errors = find_volumes_that_moved_in_chunks(errors, 10, start, end, volumes_that_moved_yesterday)
    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print

    errors = find_volumes_that_moved_in_chunks(errors, 1, start, end, volumes_that_moved_yesterday)
    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print

    with open(runtime_output_directory + '/volumes_that_moved_yesterday.json', 'w') as f:
        json.dump(volumes_that_moved_yesterday, f)
