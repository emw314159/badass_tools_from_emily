
#
# import useful libraries
#
from numpy import arange

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
def dataframe_to_table_HTML(df, prefix, headers=None, header_to_nice_name={}, style={}, header_color='#A4A4A4', even_color='FFB6C1', odd_color='#E6E6FA'):

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
    html += '  background-color: ' + header_color + ';\n'
    html += '}\n'
    html += class_prefix + '-even {\n'
    html += '  background-color: ' + even_color + ';\n'
    html += '}\n'
    html += class_prefix + '-odd {\n'
    html += '  background-color: ' + odd_color + ';\n'
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
        row_status = 'even'
        if i % 2 == 1:
            row_status = 'odd'

        html += '<tr class="' + prefix + '-' + row_status + '">\n'
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
# correlationsHeatMapHTML class
#
class correlationsHeatMapHTML:
    null_color = 'lightgrey'
    header_color = 'grey'
    abs_range_to_use = [0, 1]

    text_colors = ['#000000', '#000000', '#000000', '#000000', '#000000', '#000000', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff',] 
    
    gradient = ['#b0e0e6', '#a3cfdc', '#97bfd2', '#8aaec8', '#7e9ebf', '#718db5', '#647dab', '#586ca1', '#4b5b97', '#3f4b8e', '#323a84', '#262a7a', '#191970',]

    def __init__(self, matrix, header, class_name, round_to=3):
        self.matrix = matrix
        self.header = header
        self.class_name = class_name
        self.round_to = round_to
        start = self.abs_range_to_use[0]
        end = self.abs_range_to_use[1]
        diff = float(end - start)
        segment_length = diff / float(len(self.gradient))
        self.segments = arange(start, end + segment_length, segment_length)

    def getHTML(self):
        html = '<style>\n'
        html += '.' + self.class_name + """-table {
                         border-collapse: collapse;
                         padding-left: 50px;
                         padding-top: 50px;
                    }

                         """ + '.' + self.class_name + '-table, .' + self.class_name + '-th, .' + self.class_name + """-td {
                         border: 1px solid black;
                    }
                    """ + '.' + self.class_name + '-th, .' + self.class_name + """-td {
                         text-align: center;
                         padding-left: 15px;
                         padding-right: 15px;
                    }
                """ + '\n'
        html += '</style>\n'


        html += '<table class="' + self.class_name + '-table">\n'

        html += '<tr class="' + self.class_name + '-th"><th class="' + self.class_name + '-th" style="background-color: ' + self.header_color + ';"></th>\n'
        for i, h in enumerate(self.header):
            html += '<th class="' + self.class_name + '-th" style="background-color: ' + self.header_color + ';">' + h + '</th>\n'
        html += '</tr>\n'

        for i, h in enumerate(self.header):
            html += '<tr class="' + self.class_name + '-tr"><th class="' + self.class_name + '-th" style="background-color: ' + self.header_color + ';">' + h + '</th>\n'
            for j, h in enumerate(self.header):
                value = self.matrix[i][j]



                abs_value = abs(value)

                for s, e, idx in zip(self.segments[0:-1], self.segments[1:], range(0, len(self.gradient))):
                    if s <= abs_value and abs_value < e:
                        gradient_index = idx
                if abs_value == self.segments[-1]:
                    gradient_index = len(self.gradient) - 1
                color = self.gradient[gradient_index]
                text_color = self.text_colors[gradient_index]

                value = str(round(value, self.round_to))
                if i == j:
                    value = ''
                    color = self.null_color
                    text_color = self.null_color
                html += '<td class="' + self.class_name + '-td" style="color: ' + text_color + '; background-color: ' + color + ';">' + value + '</td>\n'
            html += '</tr>\n'



        html += '</table>\n'


        return html





