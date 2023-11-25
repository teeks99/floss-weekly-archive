import re
import yaml
from datetime import datetime, timedelta


def extract_links(text):
    links = []
    current_index = 0

    while text.find('[', current_index) != -1:
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
    offset = 0
    for result in results:
        start = result["Link Start"]
        end = result["Link End"]
        replacement = result["Link Text"]
        text = text[:start - offset] + replacement + text[end - offset:]
        offset += end - start - len(replacement)
        link_data.append(
            {"Title": result["Link Text"].strip() + " wikipedia profile", "Url": result["Url"]}
        )

    return text, link_data


def parse_guest_list(cell_text):
    guests_strs = cell_text.split(",")
    guests = []
    for guest_str in guests_strs:
        results = extract_links(guest_str)

        if results:
            guests.append({"Name": results[0]["Link Text"].strip(), "Wikipedia Profile": results[0]["Url"]})
        else:
            guests.append({"Name": guest_str.strip()})
    
    return guests


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
        }

        if content:
            episode_data["content"] = content

        data.append(episode_data)

    yaml_data = {'episodes': data}
    return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

with open ("example_table.md", "r") as table_file:
    markdown_table = table_file.read()

# Convert to YAML
yaml_output = convert_to_yaml(markdown_table)

with open("table.yml", 'w', newline='') as yamlfile:
    yamlfile.write(yaml_output)
