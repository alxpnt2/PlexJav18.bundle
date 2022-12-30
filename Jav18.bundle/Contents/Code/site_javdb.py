from site import *
import urllib2
import json

SEARCH_URL = URL('https://www.javdatabase.com/?s=', '&wpessid=')
DETAIL_URL = URL('https://www.javdatabase.com/movies/', '/')
ACTRESS_DETAIL_URL = URL('https://www.javdatabase.com/idols/', '/')
ACTRESS_SEARCH_URL = URL('https://www.javdatabase.com/?s=', '&wpessid=')


class SiteJavDB(Site):

    def tag(self):
        return "JavDB"

    def can_search(self):
        return Prefs["search_javdb"]

    def do_search(self, release_id):
        url = SEARCH_URL.get(release_id, '391487')
        self.DoLog(url)
        searchResults = HTML.ElementFromURL(url)
        results = []  # List[SearchResult]
        for searchResult in searchResults.xpath("//main/div[contains(@class, 'container')]/div[contains(@class, 'card')]"):
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
                url = DETAIL_URL.get(id)
                self.DoLog(url)
                page = HTML.ElementFromURL(url)
                if page is not None:
                    break
            except:
                pass
        if page is None:
            raise self.GetException("[" + self.tag() + "] Could not find page for id: " + ids.release_id)

        result = MetadataResult(self)

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
            role.name = actress_element.xpath(".//div[contains(@class, 'idol-name')]/a")[0].text_content().strip()
            role.image_url = actress_element.xpath('.//img')[0].get("src")
            result.roles.append(role)

        for art_element in page.xpath("//main/div/a/img"):
            result.art.append(art_element.get("data-src"))

        # Sometimes JavDB images can't be loaded
        result.full_cover_high_rez = page.xpath('//tr[contains(@class, "moviecovertb")]//img')[0].get("src")
        #if "r18" not in result.full_cover_high_rez:
        #    self.DoLog("Cover URL not from R18: " + result.full_cover_high_rez)
        #    result.full_cover_high_rez = None

        return result

    def has_actress_pictures(self):
        return True

    def can_search_actor_photos(self):
        return True

    def do_get_actress_photo(self, name):
        try:
            page = HTML.ElementFromURL(ACTRESS_DETAIL_URL.get(name.lower().replace(" ", "-")))
        except:
            self.DoLog('Could not reach detail page for ' + name + ', trying to search for it')
            try:
                page = HTML.ElementFromURL(ACTRESS_SEARCH_URL.get(name, '391488'))
                search_results = page.xpath("//div[contains(@class, 'flex-container')]/div[contains(@class, 'card')]")
                if len(search_results) == 0:
                    self.DoLog('No results, tring to change the wpessid')
                    wpessid = page.xpath("//input[contains(@placeholder, 'Idol Name')]/following-sibling::input")[0].get('value')
                    page = HTML.ElementFromURL(ACTRESS_SEARCH_URL.get(name, wpessid))
                    search_results = page.xpath("//div[contains(@class, 'flex-container')]/div[contains(@class, 'card')]")
                    if len(search_results) == 0:
                        raise self.GetException('No results when searching')

                matching_url = None
                matching_score = 95  # minimum score to only allow slight name differences
                for result in search_results:
                    link = result.xpath(".//h2/a")[0]
                    result_name = link.text_content()
                    score = 100 - Util.LevenshteinDistance(name.lower(), result_name.lower())
                    if score > matching_score:
                        matching_url = link.get('href')
                        matching_score = score
                if matching_url is not None:
                    self.DoLog("Match: " + matching_url + " (" + str(matching_score) + ")")
                    page = HTML.ElementFromURL(matching_url)
                else:
                    raise self.GetException('No search results matched name closely enough')
            except:
                raise self.GetException('Error trying to search for actress, aborting')

        if page is None:
            raise self.GetException("Could not find page for id: " + ids.release_id)

        image_url = page.xpath('//img[@height=500]')[0].get("src")
        return image_url


