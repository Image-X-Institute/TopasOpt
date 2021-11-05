import re

theme_file = "theme_templates/theme-dark.css"

output_file = "_static/css/theme.css"

oranges = ['#ef9737',
           '#f79d39',
           '#fac27d',
           '#fcdbb2']
pinks = ['#ed117b',
         '#f14592',
         '#f471aa',
         '#fabfd7']
greens = ['#d1e52a',
          '#d6e841',
          '#e8f189',
          '#f2f7bd']
blues = ['#50ade4',
         '#65cdf5',
         '#91dbf8',
         '#bfeafb']
purples = ['#972d9b',
           '#a03fa5',
           '#c282c7',
           '#dbb6df']

colours = {'main_color': oranges[0],
           'navbar_1': blues[0],
           'navbar_2': blues[1],
           'navbar_3': blues[2],
           'link_visited': purples[0],
           'link_hover': oranges[2],
           'methods_text': purples[0],
           'methods_background': '#dccade',
           'class_text': purples[0],
           'class_background': '#dccade',
           'variable_color': pinks[0],
           }

with open(theme_file, 'r', encoding="utf8") as in_file:
    with open(output_file, 'w', encoding="utf8") as out_file:
        for line in in_file:
            reg = re.findall(r"(%.*%)", line)
            if(reg):
                line = line.replace(reg[0], colours[reg[0][1:-1]])
            out_file.write(line)
