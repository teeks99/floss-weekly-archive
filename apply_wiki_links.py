import re

start_str = "("
end_str = " \"wikilink\")"
link_root = "https://en.wikipedia.org/wiki/"

def regex_replace(match_obj):
    return link_root + match_obj.group(2)

def regex_algorithm(line, out_lines):
    search_pattern = f"{start_str}(\w*){end_str}"
    line = re.sub(search_pattern, regex_replace, line)
    out_lines.append(line)

in_lines = []
out_lines = []
with open("test.md", "r") as in_file:
    in_lines = in_file.readlines()

for line in in_lines:
    regex_algorithm(line, out_lines)

with open("converted.md", "w") as out_file:
    out_file.writelines(out_lines)