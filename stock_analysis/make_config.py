

import json



configuration = {
    'output_directory' : '/home/ec2-user/badass_tools_from_emily/stock_analysis/output',
    'quote_data_directory' : '/home/ec2-user/badass_tools_from_emily/stock_analysis/quote_data',

    'user' : 'neo4j',
    'password' : 'aoeuI444',
    'volume_threshold' : 500000,
    'database_lags' : 2,
    'runtime_output_directory' : '/home/ec2-user/badass_tools_from_emily/stock_analysis/runtime/output',
    'runtime_output_directory_year' : '/home/ec2-user/badass_tools_from_emily/stock_analysis/runtime/output/year',

    'seed' : 23423,
    'bad_cutoff_percentile' : 40.,
    'good_cutoff_percentile' : 95.,
    'number_of_vfolds_to_run' : 5,
    'cost' : 0.125, 
    'gamma' : 0.5, 

    'lead_variable' : 'price_percent_diff_1_to_2',

    'formula' : 'y ~ spearman_r + spearman_r_p + pearson_r + pearson_r_p + close_lag_0 + close_lag_1 + close_lag_2 + close_lag_3 + close_lag_4 + close_lag_5 + close_percent_12_week_high + close_percent_4_week_high + close_percent_52_week_high + close_percent_diff_volume + p_log_10 + same_industry + same_sector + same_stock + volume_lag_0 + volume_lag_1 + volume_lag_2 + volume_lag_3 + volume_lag_4 + volume_lag_5 + volume_percent_12_week_high + volume_percent_4_week_high + volume_percent_52_week_high + volume_percent_diff_volume + C(weekday)',

    'factor_options' : {'weekday' : ['M', 'Tu', 'W', 'Th', 'F']},
}



with open('config.json', 'w') as f:
    json.dump(configuration, f)


