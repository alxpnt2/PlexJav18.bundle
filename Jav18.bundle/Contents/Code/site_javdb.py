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
        for searchResult in searchResults.xpath("//main/div[contains(@class, 'row')]/div/div[contains(@class, 'card')]"):
            id = searchResult.xpath('.//p/a')[0].text_content().strip()
            title = searchResult.xpath(".//div/a[contains(@class, 'cut-text')]")[0].text_content().strip()
            self.DoLog(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.lower())
            result = SearchResult()
            result.id = id
            result.title = "[" + id + "] " + title
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

        self.DoLog("Data")
        for detail_key in page.xpath('//td[contains(@class, "tablelabel")]'):
            key = detail_key.text_content().strip().lower()
            value_element = detail_key.xpath('following-sibling::td[contains(@class, "tablevalue")]')
            if len(value_element) == 0:
                continue
            value = value_element[0].text_content().strip()
            self.DoLog(key + " : " + value)
            if len(value) <= 0:
                continue

            if "dvd" in key:
                result.dvd_id = value
            if "title" in key:
                result.title = value
                id_matcher = ID_PATTERN.search(result.title)
                if id_matcher is not None:
                    result.title = result.title.replace(id_matcher.group(0), "")
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

        self.DoLog("Roles")
        for actress_element in page.xpath("//div[contains(@class, 'idol-thumb')]"):
            role = MetadataRole()
            role.name = actress_element.xpath("preceding-sibling::p/a")[0].text_content().strip()
            self.DoLog(role.name)
            role.image_url = actress_element.xpath('a/noscript/img')[0].get("src")
            self.DoLog(role.image_url)
            result.roles.append(role)

        self.DoLog("Art")
        for art_element in page.xpath("//a[contains(@rel, 'lightbox')]"):
            result.art.append(art_element.get("href"))

        # Sometimes JavDB images can't be loaded
        for image in page.xpath("//h2/following-sibling::div/a[contains(@rel, 'sponsored')]/img"):
            result.full_cover_high_rez = image.get("data-src")
        #if "r18" not in result.full_cover_high_rez:
        #    self.DoLog("Cover URL not from R18: " + result.full_cover_high_rez)
        #    result.full_cover_high_rez = None

        return result

    def get_actress_data_quality(self):
        return 3

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
                search_results = page.xpath("//div[contains(@class, 'card-body')]")
                if len(search_results) == 0:
                    self.DoLog('No results, tring to change the wpessid')
                    wpessid = page.xpath("//select[contains(@class, 'search-selector')]/option")[0].get('value')
                    page = HTML.ElementFromURL(ACTRESS_SEARCH_URL.get(name, wpessid))
                    search_results = page.xpath("//div[contains(@class, 'card-body')]")
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

        image_url = page.xpath('//div[contains(@class, "idol-portrait")]//img')[0].get("src")
        return image_url


