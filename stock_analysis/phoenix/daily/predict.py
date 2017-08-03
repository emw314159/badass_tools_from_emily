import sys
sys.path.insert(0, '/home/ec2-user')



def predict():

    #
    # import useful standard libraries
    #
    import pprint as pp
    import pickle
    import pandas as pd
    import sys
    import json
    import os

    #
    # import my libraries
    #
    import badass_tools_from_emily.machine_learning.machine_learning as ml

    #
    # load configuration
    #
    with open(sys.argv[1]) as f:
        config = json.load(f)

    #
    # user settings
    #
    runtime_output_directory = config['runtime_output_directory']
    buy_model_file = config['buy_model_file']
    short_model_file = config['short_model_file']
    formula = config['formula']
    factor_options = config['factor_options']
    predictions_directory = config['predictions_directory']

    #
    # load data frame to score
    #
    predict_df = pd.read_csv(runtime_output_directory + '/to_score.csv')
    predict_df['y'] = 1

    #
    # prepare to run prediction
    #
    y, X = ml.categorize(formula, factor_options, predict_df)

    with open(buy_model_file + '.pickle') as f:
        buy_model = pickle.load(f)
    with open(short_model_file + '.pickle') as f:
        short_model = pickle.load(f)

    #
    # predict and save
    #
    prediction = buy_model.predict(X)
    predict_df['prediction_buy'] = prediction
    prediction = short_model.predict(X)
    predict_df['prediction_short'] = prediction
    predict_df.to_csv(runtime_output_directory + '/predictions.csv', index=False)

    #
    # copy to predictions directory
    #
    os.system('rm -R ' + predictions_directory)
    os.system('mkdir ' + predictions_directory)
    os.system('cp ' + runtime_output_directory + '/predictions.csv ' + predictions_directory)
    os.system('cp ' + runtime_output_directory + '/end.pickle ' + predictions_directory)


if __name__ == '__main__':
    predict()
