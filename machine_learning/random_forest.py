
#
# import useful libraries
#
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import badass_tools_from_emily.misc as em

#
# plot feature importances
#
def plot_feature_importances(fi_dict, title, output_file, figsize=[11, 6], color='purple'):
    headers = []
    values = []
    for h in fi_dict.keys():
        headers.append(h)
        values.append(fi_dict[h])
    dict_to_sort = {
        'headers' : headers,
        'values' : values,
    }
    sorted_dict = em.sort_lists_by_rank_of_another_list(dict_to_sort, 'values')
    plt.figure(figsize=figsize)
    plt.barh(range(0, len(sorted_dict['headers'])), sorted_dict['values'], align='center', color=color)
    plt.yticks(range(0, len(sorted_dict['headers'])), sorted_dict['headers'])
    plt.title(title)
    plt.xlabel('Mean Decrease Impurity')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
