
import requests
import pprint as pp


words = ['ceo', 'cfo', 'cto', 'cdo', 'chairman', 'chairwoman', 'chair', 'president', 'chief executive officer', 'and', 'businessman', 'businesswoman', 'executive']



symbols = {
    'ANET' : 'https://en.wikipedia.org/w/api.php?action=query&titles=Arista%20Networks&format=json&prop=revisions&rvprop=content',
    'F' : 'https://en.wikipedia.org/w/api.php?action=query&titles=Ford%20Motor%20Company&format=json&prop=revisions&rvprop=content',
}

people_dict = {}

for symbol in symbols:

    url = symbols[symbol]
    people_dict[symbol] = {}

    r = requests.get(url)

    page = r.json()['query']['pages'].keys()[0]
    data = r.json()['query']['pages'][page]


    #document = data['revisions'][0]['*'].split('|')
    #document = [x.replace('[', '').replace(']', '') for x in document if x.find('key_people') >= 0]

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
    

    new_document = []
    for d in document:
        word_to_test = d.lower().replace(',', '').strip()
        if not word_to_test in words:
            new_short_list = []
            short_list = word_to_test.split(' ')
            for s in short_list:
                if not s.lower().replace(',', '').strip() in words:
                    new_short_list.append(s.strip())

            if len(new_short_list) != 0:
                new_document.append(' '.join(new_short_list))




    print
    print new_document
    print

    continue



    for d in document:
        people = [x.replace('>', '') for x in d.split('=')[1].strip().split('<br/')]
        for i, p in enumerate(people):
            if p[-1] == ',':
                people[i] = p[0:-1]
            people_and_position = []
            for p in people:
                p = [x.strip() for x in p.split(',')]
                people_and_position.append(p)



            for ppp in people_and_position:
                people_dict[symbol][ppp[0]] = ppp[1]


pp.pprint(people_dict)



    




