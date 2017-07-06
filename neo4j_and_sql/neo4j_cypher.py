#
# read cypher query output
#
def read_cypher_query_output(filename, remove_quotes=False):
    results = []
    header = []
    f = open(filename)
    for line in f:
        line = line.strip()
        if line == '':  continue
        if line[0] != '|':  continue
        line = [x.strip() for x in line.split('|') if x != '']

        if header == []:
            header = line
            continue

        if remove_quotes:
            new_line = []
            for item in line:
                if item[0] == '"' and item[-1] == '"':
                    new_line.append(item[1:-1])
                else:
                    new_line.append(item)
            line = new_line

        dict_to_append = {}
        for h, item in zip(header, line):
            dict_to_append[h] = item
        results.append(dict_to_append)

    f.close()

    return results, header
