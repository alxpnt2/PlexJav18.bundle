from site import *
import urllib2
import json

SEARCH_URL = URL('https://jav.guru/?s=')


class SiteJavGuru(Site):
    def tag(self):
        return "JavGuru"

    def can_search(self):
        return Prefs["search_javguru"]

    def do_search(self, release_id):
        url = SEARCH_URL.get(release_id)
        self.DoLog(url)
        searchResults = HTML.ElementFromURL(url)
        results = []  # List[SearchResult]
        for searchResult in searchResults.xpath("//main/div[contains(@class, 'row')]/div/div"):
            title_element = searchResult.xpath('.//h2/a')[0]
            title = title_element.text_content().strip()
            id = title[1:title.find("]")]
            release_date = searchResult.xpath(".//div[contains(@class, 'date')]")[0].text_content().strip()
            title = title + " (" + release_date + ")"
            self.DoLog(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.lower())
            result = SearchResult()
            result.id = id
            result.title = title
            result.score = score
            result.detail_url = title_element.get("href")
            results.append(result)
        return results

    def can_get_data(self):
        return True

    def do_get_data(self, ids, language):
        page = None
        try:
            url = self.do_search(ids.release_id)[0].detail_url
            self.DoLog(url)
            page = HTML.ElementFromURL(url)
        except:
            pass
        if page is None:
            raise self.GetException("[" + self.tag() + "] Could not find page for id: " + ids.release_id)

        result = MetadataResult(self)

        title_text = page.xpath('//h1[contains(@class, "titl")]')[0].text_content().strip()
        result.title = title_text[title_text.find("]") + 1:]

        for detail_key in page.xpath('//div[contains(@class, "infometa")]//li'):
            key_and_value = detail_key.text_content().strip().split(":")
            if len(key_and_value) <= 1:
                continue
            key = key_and_value[0].lower().strip()
            value = key_and_value[1].strip()
            self.DoLog(key + " : " + value)
            if len(value) <= 0:
                continue

            if "code" in key:
                result.dvd_id = value
            if "tags" in key:
                for genre in value.split(","):
                    result.genres.append(genre.strip())
            if "studio label" in key:
                result.studio = value
            if "actress" in key:
                for actress in value.split(","):
                    role = MetadataRole()
                    role.name = swap_name_order(actress.strip())
                    result.roles.append(role)
            if "series" in key:
                result.collections.append(value)
            if "release date" in key:
                result.release_date = datetime.strptime(value, '%Y-%m-%d')

        # release_date_text = page.xpath("//div[contains(@class, 'infometa')]//p[contains(@class, 'javstats')]")[0].text_content().split("•")[1].strip()
        # result.release_date = datetime.strptime(release_date_text, '%B %d, %Y')

        result.full_cover_high_rez = page.xpath('//main//img')[0].get("src")

        return result
