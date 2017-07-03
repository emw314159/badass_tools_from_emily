
#
# start HTML
#
def start_HTML(f, title, top_header=''):
    f.write('<html>\n<head>\n<title>' + title + '</title>\n</head>\n<body>\n')
    if top_header != '':
        f.write('<h1>' + top_header + '</h1>\n')
    return None

#
# end and close HTML
#
def end_and_close_HTML(f):
    f.write('</body>\n</html>\n')
    f.close()
    return None

#
# function to display alternative amplicon design as HTML
#
# Uses the result of display_alt_amplicon_design_text(fwd, rev, original_amplicon, design, breakpoint=None)
#
def display_alt_amplicon_design_html(result_as_text, header=None):
    html = ''
    if header != None:
        html += '<h3>' + header + '</h3>'
    html += '<p style="font-family : monospace;">'
    for line in result_as_text.split('\n'):
        html += line.replace(' ', '&nbsp;') + '<br/>'
    html += '</p>'
    return html

#
# dataframe to table
#
def dataframe_to_table_HTML(df, prefix, headers=None, header_to_nice_name={}, style={}):

    class_prefix = '.' + prefix

    html = '<style>\n'
    html += class_prefix + '-table, ' + class_prefix + '-th, ' + class_prefix + '-td {\n'
    html += '  border: 1px solid black;\n'
    html += '}\n'
    html += class_prefix + '-table {\n'
    html += '  border-collapse: collapse;\n'
    html += '}\n'
    html += class_prefix + '-th, ' + class_prefix + '-td {\n'
    html += '  text-align: center;'
    html += '  padding-left: 25px;\n'
    html += '  padding-right: 25px;\n'
    html += '}\n'
    html += class_prefix + '-th {\n'
    html += '  background-color: #A4A4A4;\n'
    html += '}\n'
    html += class_prefix + '-td {\n'
    html += '  background-color: #D8D8D8;\n'
    html += '}\n'
    html += class_prefix + '-monospace {\n'
    html += '  font-family: monospace;\n'
    html += '}\n'

    html += '</style>\n'

    html += '<table class="' + prefix + '-table">\n'
    if headers == None:
        headers = list(df.columns.values)
    html += '<tr class="' + prefix + '-row">'
    h_list = []
    for h in headers:
        if header_to_nice_name.has_key(h):
            h = header_to_nice_name[h]
        h_list.append(h)
    html += '<th class="' + prefix + '-th">' + ('</th><th class="' + prefix + '-th">').join(h_list) + '</th>\n'
    html += '</tr>\n'
    
    for i in range(0, len(df.index)):
        html += '<tr class="' + prefix + '-row">\n'
        row =  df.iloc[i,:]
        value_list = []
        class_list = []
        for h in h_list:
            value = row[h]
            classes = []
            classes.append(prefix + '-td')
            if style.has_key(h):
                if style[h] == ('monospace'):
                    classes.append(prefix + '-monospace')
                if style[h][0] == 'float':
                    value = round(row[h], style[h][1])
            class_list.append(classes)
            value_list.append(str(value))
                              
        for c, v in zip(class_list, value_list):
            html += '<td class="' + ' '.join(c) + '">' + v + '</td>\n'
        html += '</tr>\n'


    html += '</table>'
    return html


#
# correlation matrix
#
def correlation_matrix_HTML(matrix, header):
    print matrix
    print header
