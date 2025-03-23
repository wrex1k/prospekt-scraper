import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

class ProspektMaschineScraper:
    def __init__(self):
        self.domain = "https://www.prospektmaschine.de/"
        self.path = "hypermarkte/"
        self.brochures = []

    def fetch_html(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.text

    def extract_shopslist(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        shop_list = soup.find("ul", {"id": "left-category-shops"})
        if not shop_list:
            return False
        
        shops = []
        for li in shop_list.find_all("li"):
            a_tag = li.find("a")
            if a_tag:
                shop_name = a_tag.text.strip()
                shop_url = a_tag.get('href')
                if shop_name and shop_url:
                    shops.append({"shop_name": shop_name, "url": shop_url})
        return shops

    def extract_brochure_data(self, html_content, shop_name):
        soup = BeautifulSoup(html_content, "html.parser")
        main_brochure_div = soup.find("div", {"data-brochure-is-main": "1"})
        if not main_brochure_div:
            return None

        strong_tag = main_brochure_div.find("strong")
        title = strong_tag.text.strip() if strong_tag else "Prospekt"

        img_tag = main_brochure_div.find("img")
        if img_tag:
            thumbnail_url = img_tag.get("src") or img_tag.get("data-src")
        else:
            thumbnail_url = None  

        valid_dates = main_brochure_div.find_all("small")
        valid_from = valid_dates[0].text.strip().split(" - ")[0] if len(valid_dates) > 0 else None
        valid_to = valid_dates[0].text.strip().split(" - ")[-1] if len(valid_dates) > 0 else None

        def convert_date(date_str):
            try:
                return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
            except ValueError:
                return date_str

        valid_from = convert_date(valid_from)
        valid_to = convert_date(valid_to)

        parsed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "title": title,
            "thumbnail": thumbnail_url,
            "shop_name": shop_name,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "parsed_time": parsed_time
        }


    def save_to_json(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.brochures, f, ensure_ascii=False, indent=4)

    def run(self):
        html_content = self.fetch_html(self.domain + self.path)
        if not html_content:
            print("Error fetching the main page.")
            return

        shops = self.extract_shopslist(html_content)
        if not shops:
            print("Error parsing HTML.")
            return

        for index, shop in enumerate(shops, start=1):  
            full_url = f"{self.domain}{shop['url']}"
            brochure_page_content = self.fetch_html(full_url)
            if not brochure_page_content:
                print(f"🔴 [{index} / {len(shops)}] {shop['shop_name']} - Failed to fetch brochure page")
                continue

            brochure_data = self.extract_brochure_data(brochure_page_content, shop['shop_name'])
            if not brochure_data:
                print(f"🔴 [{index} / {len(shops)}] {shop['shop_name']} - Brochure data not found")
                continue

            self.brochures.append(brochure_data)
            print(f"🟢 [{index} / {len(shops)}] {shop['shop_name']}")

        filename = datetime.now().strftime("brochures_%Y_%m_%d.json")
        self.save_to_json(filename)
        print(f"[Successfully loaded data]: {len(self.brochures)}/{len(shops)}")
        print(f"[Data saved in]: {filename}")
        print(f"[Datetime of scrape]: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    scraper = ProspektMaschineScraper()
    scraper.run()
