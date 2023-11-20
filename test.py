def extract_links(text):
    links = []
    current_index = 0

    while True:
        # Find the next occurrence of '[' and ']'
        start_index = text.find('[', current_index)
        end_index = text.find(']', current_index)

        if start_index == -1 or end_index == -1:
            break

        # Check if the closing ']' is followed by '('
        if text[end_index + 1] == '(':
            # Extract link text and URL
            link_text = text[start_index + 1:end_index]
            link_start = start_index
            link_end = text.find(')', end_index + 1)

            # Count parentheses within the URL
            open_paren_count = link_text.count('(')
            close_paren_count = link_text.count(')')

            while link_end != -1 and open_paren_count != close_paren_count:
                link_end = text.find(')', link_end + 1)
                if link_end != -1:
                    close_paren_count += 1

            if link_end != -1:
                url = text[end_index + 2:link_end]
                current_index = link_end + 1

                # Create a dictionary for each link and append it to the list
                links.append({
                    "Link Text": link_text.strip(),
                    "Url": url.strip(),
                    "Link Start": link_start,
                    "Link End": link_end + 1
                })
            else:
                # Move the current index to the next '[' character
                current_index = start_index + 1
        else:
            # Move the current index to the next '[' character
            current_index = start_index + 1

    return links

# Test case
text_with_links = "This is text with [a link](http://example.com(embedded)) and more text."
result = extract_links(text_with_links)
print(result)
