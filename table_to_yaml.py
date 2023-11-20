import re
import yaml
from datetime import datetime

def parse_guest_list(cell):
    entries = []
    start = 0

    while True:
        match = re.search(r'\[([^]]+)\]\(([^)]+)\)|\[([^]]+)\]', cell[start:])
        if match:
            if match.group(1) and match.group(2):
                # Both name and URL
                name = match.group(1)
                url = match.group(2)
                entries.append({'Name': name, 'Wikipedia Profile': url})
            elif match.group(3):
                # Only name
                name = match.group(3)
                entries.append({'Name': name})

            # Move the starting position after the processed part
            start += match.end()
        else:
            break

    return entries

def convert_to_yaml(markdown_table):
    lines = markdown_table.strip().split('\n')
    data = []

    for line in lines[2:]:
        cells = [cell.strip() for cell in re.split(r'\s*\|\s*', line) if cell.strip()]

        episode = int(cells[0].split()[1])
        title = re.sub(r'\[.*?\]\((.*?)\)|\*\*|\*|_|`', r'\1', cells[-1])
        date_str = cells[1]

        hosts = [host.strip() for host in cells[2].split(',')]
        guests = parse_guest_list(cells[3])

        content = []
        if len(cells) > 4:
            for i in range(4, len(cells)):
                link_match = re.search(r'\[.*?\]\((.*?)\)', cells[i])
                if link_match:
                    content.append({'Title': link_match.group(1), 'Url': cells[i]})
                else:
                    content.append({'Title': cells[i]})

        date_object = datetime.strptime(date_str, '%B %d, %Y').isoformat()

        episode_data = {
            'title': title,
            'date': date_object,
            'episode': episode,
            'hosts': hosts,
            'guests': guests,
            'content': content if content else None
        }

        data.append(episode_data)

    yaml_data = {'episodes': data}
    return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

with open ("example_table.md", "r") as table_file:
    markdown_table = table_file.read()

# Convert to YAML
yaml_output = convert_to_yaml(markdown_table)

with open("table.yml", 'w', newline='') as yamlfile:
    yamlfile.write(yaml_output)
