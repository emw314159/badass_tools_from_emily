#
# initiate database connection
#
def initiate_database_connection(user, password):
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
    session = driver.session()
    return driver, session

#
# find volume info in database
#
def find_volume_info_in_database(volume, volume_to_close, close_to_volume)
    volume_to_close[volume] = {}

    #
    # find the related "close" stocks
    #
    cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lags) + ' AND volume.id = \'' + volume + '\' RETURN volume.id AS volume, close.id AS close, r.p_log_10 AS p_log_10;'

    result = session.run(cmd)

    for record in result:
        close = record['close']
        p_log_10 = record['p_log_10']
        volume_to_close[volume][close] = p_log_10

        if not close_to_volume.has_key(close):
            close_to_volume[close] = {}
        close_to_volume[close][volume] = p_log_10
