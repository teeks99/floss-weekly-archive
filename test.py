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

# Test case
text_with_links = "This is text with [a link](http://example.com(embedded)) and more text then [another link](http://something.else)."
result = extract_links(text_with_links)
print(result)
print(text_with_links[:result[0]["Link Start"]] + text_with_links[result[0]["Link End"]:])
