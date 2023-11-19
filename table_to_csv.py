import csv
import re

# Your markdown table
with open ("table.md", "r") as table_file:
    markdown_table = table_file.read()

# Splitting the markdown table into lines
lines = markdown_table.strip().split('\n')

# Extracting headers
headers = [header.strip() for header in re.split(r'\s*\|\s*', lines[0]) if header]

# Extracting data
data = []
for line in lines[3:]:
    row_data = [item.strip() for item in re.split(r'\s*\|\s*', line) if item]
    data.append(row_data)

# Writing to CSV
with open('table.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    
    # Writing headers
    csv_writer.writerow(headers)
    
    # Writing data
    csv_writer.writerows(data)



