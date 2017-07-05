
import html as ht
import pandas as pd
#import statsmodels.formula.api as smf
import numpy as np


def main():


    #
    # load data frame and start and HTML file
    #
    df = pd.read_csv('data/dataframe.csv')
    f = open('output/test_df.html', 'w')
    ht.start_HTML(f, 'Emily\'s HTML Automation Examples')


    #
    # demonstrate dataframe to HTML code
    #
    headers = ['sequence(target+3\'+5\')', 'log2 fold change, KBM7', 'seed', 'motif_scores', 'motif_scores_seed', 'regression_score']

    style = {
        'sequence(target+3\'+5\')' : ('monospace'),
        'log2 fold change, KBM7' : ('float', 3),
        'seed' : ('monospace'),
        'motif_scores' : ('float', 3),
        'motif_scores_seed' : ('float', 3),
        'regression_score' : ('float', 3),
    }

    f.write('<h1>Pandas Dataframe to HTML Table Example:</h1>')
    f.write(ht.dataframe_to_table_HTML(df.iloc[range(0, 20),:], 'emily-df', headers=headers, style=style))


    #
    # demonstrate correlation matrix to HTML code
    #
    f.write('<h1>Numpy Correlation Matrix to HTML Heat Map</h1>\n')
    df2 = df.ix[:,['result_KBM7', 'folding_dG', 'motif_scores', 'motif_scores_seed', 'be_seed_5', 'be_seed_6', 'se_seed_5', 'se_full']]
    df2m = df2.as_matrix()
    corr_matrix = np.corrcoef(df2m, rowvar=0)
    corr_html = ht.correlationsHeatMapHTML(corr_matrix, list(df2.columns.values), 'corr')
    f.write(corr_html.getHTML() + '\n')

   
    #
    # End and close out the HTML
    #
    ht.end_and_close_HTML(f)


if __name__ == "__main__":
    main()

