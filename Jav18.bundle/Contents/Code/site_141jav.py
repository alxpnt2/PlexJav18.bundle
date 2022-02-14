from site import *


SEARCH_URL = 'https://www.141jav.com/search/'
DETAIL_URL = 'https://www.141jav.com/torrent/'


def get_search_url(release_id):
    encoded_id = urllib2.quote(release_id.replace("-", ""))
    return SEARCH_URL + encoded_id


def get_detail_url(release_id):
    encoded_id = urllib2.quote(release_id.replace("-", ""))
    return DETAIL_URL + encoded_id


class Site141Jav(Site):
    def tag(self):
        return "141Jav"

    def can_search(self):
        return True

    def do_search(self, release_id):
        url = get_search_url(release_id)
        self.DoLog(url)
        page = HTML.ElementFromURL(url)
        results = []  # List[SearchResult]
        for searchResult in page.xpath('//div[contains(@class, "container")]/div[contains(@class, "card")]'):
            id = searchResult.xpath('//h5/a')[0].text_content().strip()
            title = searchResult.xpath('//p[contains(@class, "level")]')[0].text_content().strip()
            self.DoLog(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.replace("-", "").lower())
            result = SearchResult()
            result.id = release_id.upper()
            result.title = "[" + release_id + "] " + title
            result.score = score
            results.append(result)
        return results

    def can_get_data(self):
        return True

    def do_get_data(self, ids):
        url = get_detail_url(ids.release_id)
        self.DoLog(url)
        page = HTML.ElementFromURL(url)

        result = MetadataResult()
        result.title = page.xpath('//p[contains(@class, "level")]')[0].text_content().strip()
        result.release_date = datetime.strptime(page.xpath('//p[contains(@class, "subtitle")]/a')[0].text_content().strip(), '%b. %d, %Y')

        for tag in page.xpath('//div[contains(@class, "tags")]/a'):
            result.genres.append(tag.text_content().strip())

        for actress in page.xpath('//div[contains(@class, "panel")]/a'):
            role = MetadataRole()
            role.name = actress.text_content().strip()
            result.roles.append(role)

        result.full_cover_high_rez = page.xpath('//div[contains(@class, "container")]//img')[0].get("src")

        return result