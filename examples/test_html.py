
import html as ht
import pandas as pd
import statsmodels.formula.api as smf
import numpy as np


def main():
    df = pd.read_csv('df_first_WITH_SCORES.csv')
    f = open('output/test_df.html', 'w')
    ht.start_HTML(f, 'Emily\'s HTML Automation', 'DataFrame to HTML Example:')
    headers = ['sequence(target+3\'+5\')', 'log2 fold change, KBM7', 'seed', 'motif_scores', 'motif_scores_seed', 'regression_score']

    style = {
        'sequence(target+3\'+5\')' : ('monospace'),
        'log2 fold change, KBM7' : ('float', 3),
        'seed' : ('monospace'),
        'motif_scores' : ('float', 3),
        'motif_scores_seed' : ('float', 3),
        'regression_score' : ('float', 3),
    }


    #formula = 'result_KBM7 ~ folding_dG + motif_scores + motif_scores_seed + be_seed_5 + be_seed_6 + se_full + se_seed_5'
    #model = smf.ols(formula=formula, data=df).fit()
    #print dir(model)
    #print model.cov_params()
    #print model.summary()
     
    df2 = pd.DataFrame()
    df2['Intercept'] = len(list(df['result_KBM7'])) * [1]
    df2['folding_dG'] = list(df['folding_dG'])
    df2['motif_scores'] = list(df['motif_scores'])
    df2['motif_scores_seed'] = list(df['motif_scores_seed'])
    df2['be_seed_5'] = list(df['be_seed_5'])
    df2['be_seed_6'] = list(df['be_seed_6'])
    df2['se_seed_5'] = list(df['se_seed_5'])
    df2['se_full'] = list(df['se_full'])
    df2m = df2.as_matrix()
    corr_matrix = np.corrcoef(df2m, rowvar=0)
    corr_html = ht.correlation_matrix_HTML(corr_matrix, list(df2.columns.values))
    

   

    f.write(ht.dataframe_to_table_HTML(df.iloc[range(0, 20),:], 'emily-df', headers=headers, style=style))
    ht.end_and_close_HTML(f)


if __name__ == "__main__":
    main()

