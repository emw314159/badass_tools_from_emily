
#
# import useful libraries
#
import requests
import pprint as pp
import json

#
# user settings
#
words = ['ceo', 'cfo', 'cto', 'cdo', 'chairman', 'chairwoman', 'chair', 'president', 'chief executive officer', 'and', 'businessman', 'businesswoman', 'executive', 'num_employees', 'employees', 'apple', '{{small', '*', 'chief design officer', 'chief operating officer', 'product', 'products', '{{plainlist', 'ref name', 'coo', 'chief financial officer', 'area_served', '{{startplainlist\n*', '{{startplainlist']

url_part_1 = 'https://en.wikipedia.org/w/api.php?action=query&titles='
url_part_2 = '&format=json&prop=revisions&rvprop=content'

output_directory = 'output'



#
# load names
#
with open(output_directory + '/symbol_to_name.json') as f:
    symbol_to_name = json.load(f)


people_dict = {}

for i, symbol in enumerate(sorted(symbol_to_name.keys())):
    
    print i

    try:

        name = symbol_to_name[symbol].keys()[0]

        name = name.replace(', Inc.', '')
        name = name.replace(' Corporation', '')
        name = name.replace(' Limited', '')

        url = url_part_1 + name.replace(' ', '%20') + url_part_2


        people_dict[symbol] = {}
        
        r = requests.get(url)
        
        page = r.json()['query']['pages'].keys()[0]
        data = r.json()['query']['pages'][page]




        document = data['revisions'][0]['*'].split('key_people')[1].split('=')[1]
        document = document.replace('industry', '')
        document = document.replace('{{unbulleted list', '').replace('}}', '')
        document = document.replace('<small>', '').replace('</small', '')
        
        document = document.replace('<br/>', '|').replace('<br />', '|')
        document = document.replace('>', '').replace('<', '')
        document = document.replace('(', '').replace(')', '')
        document = document.replace('[[', '|').replace(']]', '|')
        document = document.replace('&', '|')

        document = [x.strip() for x in document.split('|') if x.strip() != '']
    

        new_document = {}
        for d in document:
            word_to_test = d.lower().replace(',', '').strip()
            if not word_to_test in words:
                new_short_list = []
                short_list = word_to_test.split(' ')
                for s in short_list:
                    if not s.lower().replace(',', '').strip() in words:
                        if s.lower().find('employee') == -1:
                            new_short_list.append(s.strip())

                if len(new_short_list) != 0:
                    new_document[' '.join(new_short_list)] = None

        people_dict[symbol] = new_document

    except:
        continue


#
# save first pass of the dictionary
#
with open(output_directory + '/people_first_pass.json', 'w') as f:
    json.dump(people_dict, f)




    




