from site import *
import urllib2
import json

SEARCH_URL = URL('https://r18.dev/videos/vod/movies/detail/-/dvd_id=', '/json')
API_URL = URL('https://r18.dev/videos/vod/movies/detail/-/combined=', '/json')

R18_DEV_HDR = {
    'User-Agent': 'PlexJav18',
    'accept': '*/*',
}

class SiteR18Dev(Site):

    def tag(self):
        return "R18.dev"

    def can_search(self):
        return Prefs["use_r18dev"] and Prefs["search_r18dev"]

    # def generate_potential_ids(self, id):
    #     results = [id]
    #     split = id.split("-")
    #     if len(split) > 1:
    #         results.append((split[0] + split[1].zfill(5)).lower())
    #         for prefix in ("118", "1", "h_019", "h_068", "h_094", "h_237", "h_173", "h_227"):
    #             results.append(prefix + (split[0] + split[1]).lower())
    #             results.append(prefix + (split[0] + split[1].zfill(5)).lower())
    #     return results

    def get_json(self, id, base_url=API_URL):
        if id is None:
            return None
        id = id.replace("-", "").lower()
        url = base_url.get(id)
        self.DoLog(url)
        req = urllib2.Request(url, headers=R18_DEV_HDR)
        con = urllib2.urlopen(req)
        web_byte = con.read()
        webpage = web_byte.decode('utf-8')
        return json.loads(webpage)

    def get_data_for(self, release_id):
        try:
            data = self.get_json(release_id, base_url=SEARCH_URL)
            content_id = data["content_id"]
            return self.get_json(content_id)
        except: pass
        ### No longer doing to avoid spamming R18.dev servers
        # for id in self.generate_potential_ids(release_id):
        #     try:
        #         return self.get_json(id)
        #     except: pass
        return None

    def do_search(self, release_id):
        data = self.get_data_for(release_id)
        if data is not None:
            result = SearchResult()
            result.id = data["dvd_id"]
            result.content_id = data["content_id"]
            if result.id is None or Prefs["use_content_id_for_metadata"]:
                result.id = result.content_id
            result.title = "[" + result.id + "] " + data["title_en"]
            result.score = 100 - Util.LevenshteinDistance(result.id.lower(), release_id.lower())
            return [result]
        return []

    def can_get_data(self):
        return Prefs["use_r18dev"]

    def do_get_data(self, ids, language):
        result = MetadataResult(self)
        data = self.get_data_for(ids.release_id)
        if data is None:
            raise self.GetException("Could not find page for id: " + ids.release_id)
        # Log(data)

        result.dvd_id = data["dvd_id"]
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
                if "name_romaji" in actor:
                    role.name = actor["name_romaji"]
                else:
                    role.name = actor["name_kanji"]
                if "image_url" in actor and actor["image_url"] is not None:
                    role.image_url = "https://pics.dmm.co.jp/mono/actjpgs/" + actor["image_url"]
                self.DoLog("actor: " + role.name)
                result.roles.append(role)
        actors = data["actors"]
        if actors is not None and len(actors) > 0:
            for actor in actors:
                role = MetadataRole()
                if "name_romaji" in actor:
                    role.name = actor["name_romaji"]
                else:
                    role.name = actor["name_kanji"]
                if "image_url" in actor and actor["image_url"] is not None:
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