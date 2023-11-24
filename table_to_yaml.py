import re
import yaml
from datetime import datetime, timedelta

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

def extract_links(text):
    links = []
    current_index = 0

    while True:
        # Find the next occurrence of '[' and ']'
        start_index = text.find('[', current_index)
        end_index = text.find(']', current_index)

        if start_index == -1 or end_index == -1:
            break

        title = text[start_index + 1:end_index]

        # Check if the closing ']' is followed by '('
        if text[end_index + 1] == '(':
            end_char = 0
            remaining_open = 0

            for a_char in text[end_index + 1:]:
                end_char += 1
                if a_char == "(":
                    remaining_open += 1
                elif a_char == ")":
                    remaining_open -= 1

                if remaining_open == 0:
                    break

            link_start = end_index + 1 + 1
            link_end = end_index + 1 + end_char - 1
            end_index = link_end + 1
            current_index += end_index

            url = text[link_start:link_end]

            # Create a dictionary for each link and append it to the list
            links.append({
                "Link Text": title,
                "Url": url,
                "Link Start": start_index,
                "Link End": end_index
            })
        else:
            # Move the current index to the next '[' character
            raise Exception("The character after the link text must be (")

    return links

def extract_links_and_replace_text(text):
    results = extract_links(text)
    link_data = []
    for result in results:
        text = text[:result["Link Start"]] + result["Link Text"] + text[result["Link End"]:]
        link_data.append(
            {"Title": result["Link Text"] + " wikipedia profile", "Url": result["Url"]}
        )

    return text, link_data

def convert_to_yaml(markdown_table):
    lines = markdown_table.strip().split('\n')
    data = []

    for line in lines[2:]:
        cells = [cell.strip() for cell in re.split(r'\s*\|\s*', line) if cell.strip()]

        episode = int(cells[0].split()[1])
        date_str = cells[1]

        hosts = [host.strip() for host in cells[2].split(',')]
        guests = parse_guest_list(cells[3])
        title, content = extract_links_and_replace_text(cells[4])

        date_object = datetime.strptime(date_str, '%B %d, %Y')

        episode_data = {
            'title': title,
            'date': date_object.strftime("%Y-%m-%d 12:00:00 -0000"),
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
