from site import *
import urllib2
import json

SEARCH_URL = 'https://www.javdatabase.com/?s='
DETAIL_URL = 'https://www.javdatabase.com/movies/'


def get_search_url(release_id):
    encodedId = urllib2.quote(release_id)
    return SEARCH_URL + encodedId


def get_api_url(id):
    encodedId = urllib2.quote(id)
    return DETAIL_URL + encodedId + '/'


class SiteJavDB(Site):

    def tag(self):
        return "JavDB"

    def can_search(self):
        return Prefs["search_javdb"]

    def do_search(self, release_id):
        url = get_search_url(release_id)
        self.DoLog(url)
        searchResults = HTML.ElementFromURL(url)
        results = []  # List[SearchResult]
        for searchResult in searchResults.xpath("//main/div[contains(@class, 'row')]/div/div[contains(@class, 'card')]"):
            id = searchResult.xpath('.//h2/a')[0].text_content().strip()
            release_date = searchResult.xpath('.//figcaption')[0].text_content().strip()
            title = id + " (" + release_date + ")"
            self.DoLog(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.lower())
            result = SearchResult()
            result.id = id
            result.title = "[" + id + "] " + release_date
            result.score = score
            results.append(result)
        return results

    def can_get_data(self):
        return True

    def do_get_data(self, ids, language):
        potential_ids = [ids.release_id]
        if ids.fanza_id is not None:
            potential_ids.append(ids.fanza_id)
        page = None
        for id in potential_ids:
            try:
                url = get_api_url(id)
                self.DoLog(url)
                page = HTML.ElementFromURL(url)
                if page is not None:
                    break
            except:
                pass
        if page is None:
            raise self.GetException("[" + self.tag() + "] Could not find page for id: " + ids.release_id)

        result = MetadataResult()

        for detail_key in page.xpath('//td[contains(@class, "tablelabel")]'):
            key = detail_key.text_content().strip().lower()
            value = detail_key.xpath('following-sibling::td[contains(@class, "tablevalue")]')[0].text_content().strip()
            self.DoLog(key + " : " + value)
            if len(value) <= 0:
                continue

            if "title" in key:
                result.title = value
            if "genre" in key:
                for genre in detail_key.xpath('following-sibling::td[contains(@class, "tablevalue")]/span'):
                    result.genres.append(genre.text_content().strip())
            if "series" in key:
                result.collections.append(value)
            if "studio" in key:
                result.studio = value
            if "director" in key:
                for director in value.split(","):
                    result.directors.append(director.strip())
            if "date" in key:
                result.release_date = datetime.strptime(value, "%Y-%m-%d")

        for actress_element in page.xpath("//div[contains(@class, 'flex-item-idol')]/figure"):
            role = MetadataRole()
            role.name = actress_element.xpath("//div[contains(@class, 'idol-name')]/a")[0].text_content().strip()
            role.image_url = actress_element.xpath('//img')[0].get("src")
            result.roles.append(role)

        # Sometimes JavDB images can't be loaded
        # result.full_cover_high_rez = page.xpath('//tr[contains(@class, "moviecovertb")]//img')[0].get("src")

        return result
