import csv
from bs4 import BeautifulSoup
import os 


def scrape_html_to_csv(html_file_path, csv_file_path):
    if not os.path.exists(html_file_path):
        print(f"Error: The file '{html_file_path}' was not found.")
        return

    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        rows = soup.find_all('tr', class_='column')

        if not rows:
            print("No rows with class 'column' found in the HTML file.")
            return

        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Column Name', 'Short Description', 'Long Description'])

            for row in rows:
                cells = row.find_all('td')

                if len(cells) >= 3:
                    col_name = cells[0].get_text(strip=True)
                    short_desc = cells[1].get_text(strip=True)
                    long_desc = cells[2].get_text(strip=True).replace("\n", " ")

                    if "Reference" in short_desc:
                        continue

                    csv_writer.writerow([col_name, short_desc, long_desc])

        print(f"Successfully scraped {len(rows)} rows and saved to '{csv_file_path}'")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    input_filename = 'ps-description-page.html'
    output_filename = 'api-ps-columns.csv'
    scrape_html_to_csv(input_filename, output_filename)
