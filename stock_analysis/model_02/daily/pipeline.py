
# python badass_tools_from_emily/stock_analysis/model_02/daily/pipeline.py badass_tools_from_emily/stock_analysis/model_02/daily/config.json 



import sys
sys.path.insert(0, '/home/ec2-user')


import badass_tools_from_emily.stock_analysis.model_02.daily.initialize as initialize
import badass_tools_from_emily.stock_analysis.model_02.daily.query_database_for_movers as query_database_for_movers
import badass_tools_from_emily.stock_analysis.model_02.daily.get_two_day_stocks as get_two_day_stocks
import badass_tools_from_emily.stock_analysis.model_02.daily.get_year_stocks as get_year_stocks
import badass_tools_from_emily.stock_analysis.model_02.daily.prepare_for_prediction as prepare_for_prediction

initialize.initialize()
query_database_for_movers.query_database_for_movers()
get_two_day_stocks.get_two_day_stocks()
get_year_stocks.get_year_stocks()
prepare_for_prediction.prepare_for_prediction()

