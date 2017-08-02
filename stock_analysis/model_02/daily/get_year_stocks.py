
def get_year_stocks():

    #
    # load useful libraries
    #
    import json
    import datetime
    import sys
    import pickle
    import pandas_datareader as pdr
    import os

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
    runtime_output_directory_year = config['runtime_output_directory_year']

    #
    # create repository directory
    #
    os.system('rm -R ' + runtime_output_directory_year)
    os.system('mkdir ' + runtime_output_directory_year)

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
    # load list of volumes that moved yesterday
    #
    with open(runtime_output_directory + '/volumes_that_moved_yesterday.json') as f:
        volumes_that_moved_yesterday = json.load(f)

    #
    # get data in chunks
    #
    def test_moved_in_chunks(stock_list, n, start, end):

        errors = []
        chunks = chunk(stock_list, n)

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
                    with open(runtime_output_directory_year + '/' + symbol + '.pickle', 'w') as f:
                        pickle.dump(df, f)
            except:
                errors.extend(c)

        return errors


    #
    # pull year for volumes, close for volumes that moved
    #
    unique_symbols = {}
    for volume in volumes_that_moved_yesterday:
        unique_symbols[volume] = None
        for close in volume_movers[volume].keys():
            unique_symbols[close] = None

    start = (end + datetime.timedelta(days=-400))

    errors = test_moved_in_chunks(unique_symbols.keys(), 200, start, end)
    print
    print 'length(errors) = ' + str(len(errors))
    print

    errors = test_moved_in_chunks(errors, 10, start, end)
    print
    print 'length(errors) = ' + str(len(errors))
    print

    errors = test_moved_in_chunks(errors, 1, start, end)
    print
    print 'length(errors) = ' + str(len(errors))
    print

    with open(runtime_output_directory + '/unique_symbols.json', 'w') as f:
        json.dump(unique_symbols, f)








