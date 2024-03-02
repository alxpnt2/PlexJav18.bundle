from site import *

SEARCH_URL = URL('https://www.141jav.com/search/')
DETAIL_URL = URL('https://www.141jav.com/torrent/')


class Site141Jav(Site):
    def get_search_url(self, release_id):
        return SEARCH_URL.get(release_id.replace("-", ""))

    def get_detail_url(self, release_id):
        return DETAIL_URL.get(release_id.replace("-", ""))

    def tag(self):
        return "141Jav"

    def can_search(self):
        return Prefs["search_141jav"]

    def do_search(self, release_id):
        url = self.get_search_url(release_id)
        self.DoLog(url)
        page = HTML.ElementFromURL(url)
        results = []  # List[SearchResult]
        for searchResult in page.xpath('//div[contains(@class, "container")]/div[contains(@class, "card")]'):
            id = searchResult.xpath('.//h5/a')[0].text_content().strip()
            title_element = searchResult.xpath('.//p[contains(@class, "level")]')
            title = title_element[0].text_content().strip() if len(title_element) > 0 else "[No Title]"
            self.DoLog(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.replace("-", "").lower())
            result = SearchResult()
            result.id = id.upper()
            result.title = "[" + id + "] " + title
            result.score = score
            results.append(result)
        return results

    def can_get_data(self):
        return True

    def are_names_japanese_order(self):
        return True

    def do_get_data(self, ids, language):
        url = self.get_detail_url(ids.release_id)
        self.DoLog(url)
        page = HTML.ElementFromURL(url)

        result = MetadataResult(self)
        id_elements = page.xpath('//h5[contains(@class, "title")]/a')
        if len(id_elements) > 0:
            result.dvd_id = id_elements[0].text_content().strip()
        title_elements = page.xpath('//p[contains(@class, "level")]')
        if len(title_elements) > 0:
            result.title = title_elements[0].text_content().strip()
        release_date_text = page.xpath('//p[contains(@class, "subtitle")]/a')[0].text_content().strip()
        try:
            result.release_date = datetime.strptime(release_date_text, '%b. %d, %Y')
        except:
            try:
                result.release_date = datetime.strptime(release_date_text, '%B %d, %Y')
            except:
                self.DoLog("Could not parse release date: " + release_date_text)
                pass

        for tag in page.xpath('//div[contains(@class, "tags")]/a'):
            result.genres.append(tag.text_content().strip())

        for actress in page.xpath('//div[contains(@class, "panel")]/a'):
            role = MetadataRole()
            name = actress.text_content().strip()
            if self.are_names_japanese_order():
                role.name = swap_name_order(name)
            else:
                role.name = name
            result.roles.append(role)

        result.full_cover_high_rez = page.xpath('//div[contains(@class, "container")]//img')[0].get("src")

        return result
