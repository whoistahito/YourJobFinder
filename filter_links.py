import csv

def filter_links(input_file='sent_link.csv', output_file='google_links.csv'):
    """
    Reads a CSV file, filters out links from linkedin.com and indeed.com,
    and saves the remaining links to a new CSV file.
    """
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Assuming the first row is the header
            header = next(reader)
            writer.writerow(header)

            # Find the index of the column containing the URLs.
            # This assumes the column is named 'url' or 'link'.
            # Modify this if your column name is different.
            url_column_index = -1
            for i, col in enumerate(header):
                if 'url' in col.lower() or 'link' in col.lower():
                    url_column_index = i
                    break

            if url_column_index == -1:
                print("Error: Could not find a URL column in the CSV header.")
                print("Please ensure the header contains 'url' or 'link'.")
                return

            for row in reader:
                if row: # Ensure row is not empty
                    link = row[url_column_index]
                    if 'linkedin.com' not in link and 'indeed.com' not in link:
                        writer.writerow(row)

        print(f"Filtered links have been saved to {output_file}")

    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    filter_links()

