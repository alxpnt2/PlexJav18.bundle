from site import *
import urllib2
import json

SEARCH_URL = URL('https://www.r18.com/common/search/searchword=', '/')
API_URL = URL('https://www.r18.com/api/v4f/contents/', '?lang=', '&unit=USD')

LANG_CODES = {"English": "en", "Chinese": "zh"}

class SiteR18(Site):

    def tag(self):
        return "R18"

    def can_search(self):
        return Prefs["search_r18"]

    def do_search(self, release_id):
        url = SEARCH_URL.get(release_id)
        self.DoLog(url)
        searchResults = HTML.ElementFromURL(url)
        results = []  # List[SearchResult]
        for searchResult in searchResults.xpath('//li[contains(@class, "item-list")]'):
            content_id = searchResult.get("data-content_id")
            id = searchResult.xpath('a//p//img')[0].get("alt")
            title = searchResult.xpath('a//dl//dt')[0].text_content()
            if title.startswith("Sale"):
                title = title[4:]
            self.DoLog(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.lower())
            result = SearchResult()
            result.id = id
            result.content_id = content_id
            result.title = "[" + id + "] " + title
            result.score = score
            results.append(result)
        return results

    def can_get_data(self):
        return True

    def do_get_data(self, ids, language):
        result = MetadataResult(self)

        if ids.fanza_id is None and ids.service_used == self.tag():
            search_results = self.do_search(ids.release_id)
            if len(search_results) > 0:
                ids.fanza_id = search_results[0].content_id
            else:
                raise self.GetException("No Fanza ID present and no search results")
        if ids.fanza_id is None and ids.fanza_id_guess is None:
            raise self.GetException("No Fanza ID present")
        language = "en" if language not in LANG_CODES else LANG_CODES[language]
        self.DoLog(language)
        data = None
        for id in [ids.fanza_id, ids.fanza_id_guess]:
            try:
                if id is None:
                    continue
                url = API_URL.get(id, language)
                self.DoLog(url)
                req = urllib2.Request(url, headers=HDR)
                con = urllib2.urlopen(req)
                web_byte = con.read()
                webpage = web_byte.decode('utf-8')
                data = json.loads(webpage)["data"]
                break
            except: pass
        if data is None:
            raise self.GetException("Could not find page for id: " + ids.fanza_id)
        # Log(data)

        id = data["dvd_id"]
        title = data["title"]
        result.title = title
        result.studio = data["maker"]["name"]
        director_info = data["director"]
        if director_info is not None:
            result.directors.append(director_info)
        date = data["release_date"]
        date_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        result.release_date = date_object

        # Collections
        series = data["series"]
        if series is not None:
            result.collections.append(series["name"])

        # Genres
        for category in data["categories"]:
            category_name = category["name"]
            if "Featured" in category_name or "Sale" in category_name or "Hi-Def" in category_name or "4K" in category_name:
                continue
            result.genres.append(category_name)

        # Actors
        actors = data["actresses"]
        if actors is not None and len(actors) > 0:
            for actor in actors:
                role = MetadataRole()
                role.name = actor["name"]
                role.image_url = actor["image_url"]
                self.DoLog("actor: " + role.name)
                result.roles.append(role)

        # Posters/Background
        result.full_cover_high_rez = data["images"]["jacket_image"]["large"]
        result.front_cover_low_rez = data["images"]["jacket_image"]["medium"]
        gallery = data["gallery"]
        for scene in gallery:
            result.art.append(scene["large"])

        return result

    def get_actress_data_quality(self):
        return 3

    def has_actress_pictures(self):
        return True