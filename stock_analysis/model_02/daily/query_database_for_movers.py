def query_database_for_movers():

    #
    # load useful libraries
    #
    import pickle
    import datetime
    from neo4j.v1 import GraphDatabase, basic_auth
    import json
    import sys

    #
    # load configuration
    #
    with open(sys.argv[1]) as f:
        config = json.load(f)

    #
    # user settings
    #
    user = config['user']
    password = config['password']
    database_lags = config['database_lags']
    runtime_output_directory = config['runtime_output_directory']

    #
    # load end date
    #
    with open(runtime_output_directory + '/end.pickle') as f:
        end = pickle.load(f)

    #
    # connect to database
    #
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
    session = driver.session()

    #
    # get volume movers known to database
    #
    cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lags) + ' RETURN volume.id AS volume, close.id AS close, r.lag as lag, r.p_log_10 as p_log_10;'
    volume_movers = {}
    result = session.run(cmd)
    for record in result:
        volume = record['volume']
        close = record['close']
        lag = str(record['lag'])
        p_log_10 = record['p_log_10']

        if not volume_movers.has_key(volume):
            volume_movers[volume] = {}
        if not volume_movers[volume].has_key(close):
            volume_movers[volume][close] = p_log_10

    with open(runtime_output_directory + '/volume_movers.json', 'w') as f:
        json.dump(volume_movers, f)











                                 




