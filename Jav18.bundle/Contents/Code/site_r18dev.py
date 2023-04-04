from site import *
import urllib2
import json

SEARCH_URL = URL('https://www.r18.com/common/search/searchword=', '/')
API_URL = URL('https://r18.dev/videos/vod/movies/detail/-/combined=', '/json')

class SiteR18Dev(Site):

    def tag(self):
        return "R18.dev"

    def can_search(self):
        return Prefs["search_r18dev"]

    def find_potential_ids(self, id):
        results = [id]
        split = id.split("-")
        if len(split) > 1:
            results.append((split[0] + split[1].zfill(5)).lower())
            for prefix in ("118", "1", "h_068", "h_094", "h_237", "h_173", "h_227"):
                results.append(prefix + (split[0] + split[1]).lower())
                results.append(prefix + (split[0] + split[1].zfill(5)).lower())
        return results

    def get_json(self, id):
        if id is None:
            return None
        id = id.replace("-", "").lower()
        url = API_URL.get(id)
        self.DoLog(url)
        req = urllib2.Request(url, headers=HDR)
        con = urllib2.urlopen(req)
        web_byte = con.read()
        webpage = web_byte.decode('utf-8')
        return json.loads(webpage)

    def do_search(self, release_id):
        for id in self.find_potential_ids(release_id):
            try:
                data = self.get_json(id)
                result = SearchResult()
                result.id = data["dvd_id"]
                result.content_id = data["content_id"]
                result.title = "[" + result.id + "] " + data["title_en"]
                result.score = 100 - Util.LevenshteinDistance(result.id.lower(), release_id.lower())
                return [result]
            except: pass
        return []

    def can_get_data(self):
        return True

    def do_get_data(self, ids, language):
        result = MetadataResult(self)
        data = None
        for id in [ids.release_id, ids.fanza_id]:
            try:
                data = self.get_json(id)
                break
            except: pass
        if data is None:
            for id in self.find_potential_ids(ids.release_id):
                try:
                    data = self.get_json(id)
                    break
                except: pass
        if data is None:
            raise self.GetException("Could not find page for id: " + ids.release_id)
        # Log(data)

        id = data["dvd_id"]
        result.title = data["title_en"]
        result.title_jp = data["title_ja"]
        result.studio = data["maker_name_en"]
        directors = data["directors"]
        if directors is not None and len(directors) > 0:
            for director in directors:
                result.directors.append(director["name_romaji"])
        date = data["release_date"]
        date_object = datetime.strptime(date, '%Y-%m-%d')
        result.release_date = date_object

        # Collections
        if "series_name_en" in data:
            result.collections.append(data["series_name_en"])

        # Genres
        for category in data["categories"]:
            category_name = category["name_en"]
            if "Featured" in category_name or "Sale" in category_name or "Hi-Def" in category_name or "4K" in category_name or "Video" in category_name:
                continue
            result.genres.append(category_name)

        # Actors
        actors = data["actresses"]
        if actors is not None and len(actors) > 0:
            for actor in actors:
                role = MetadataRole()
                role.name = actor["name_romaji"]
                role.image_url = "https://pics.dmm.co.jp/mono/actjpgs/" + actor["image_url"]
                self.DoLog("actor: " + role.name)
                result.roles.append(role)
        actors = data["actors"]
        if actors is not None and len(actors) > 0:
            for actor in actors:
                role = MetadataRole()
                role.name = actor["name_romaji"]
                role.image_url = "https://pics.dmm.co.jp/mono/actjpgs/" + actor["image_url"]
                self.DoLog("actor: " + role.name)
                result.roles.append(role)

        # Posters/Background
        result.full_cover_high_rez = data["jacket_full_url"]
        result.front_cover_low_rez = data["jacket_thumb_url"]
        gallery = data["gallery"]
        for scene in gallery:
            result.art.append(scene["image_full"])

        return result

    def get_actress_data_quality(self):
        return 3

    def has_actress_pictures(self):
        return True