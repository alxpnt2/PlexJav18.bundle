import os
import re
import urllib2
from genres import *


CACHE_PATH = os.path.join(Core.app_support_path, "Plug-in Support", "Data", "com.plexapp.agents.jav18", "DataItems")
HDR = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}
ID_PATTERN = re.compile("([a-zA-Z]+)-*([0-9]+)")




class URL:
    def __init__(self, *parts):
        self.parts = parts  # str[]

    def get(self, *values):
        result = ""
        for i in range(0, len(self.parts)):
            result += self.parts[i]
            if i < len(values):
                result += urllib2.quote(values[i])
        return result


class SearchResult:
    def __init__(self):
        self.id = ""
        self.site_id = ""
        self.title = ""
        self.score = ""
        self.detail_url = ""

    def __str__(self):
        return self.id + " (" + str(self.score) + ") :: " + self.title


class ContentIds:
    def __init__(self, service_used, release_id):
        self.service_used = service_used
        self.release_id = release_id
        self.mgs_id = None
        self.sokmil_id = None
        self.duga_id = None
        self.fanza_id = None


class MetadataRole:
    def __init__(self):
        self.name = ""
        self.image_url = ""


class MetadataResult:
    def __init__(self, service):
        self.service = service
        self.dvd_id = None
        self.title = None
        self.title_jp = None
        self.studio = None
        self.directors = []
        self.release_date = None
        self.collections = []
        self.genres = []
        self.roles = []
        self.front_cover_low_rez = None
        self.front_cover_high_rez = None
        self.full_cover_high_rez = None
        self.art = []


class MetadataResults:
    def __init__(self):
        self.results = []

    def no_results_founds(self):
        return len(self.results) <= 0

    def get_first_non_null(self, getter):
        for result in self.results:
            if getter(result) is not None:
                return getter(result)
        return None

    def get_first_non_empty(self, getter):
        for result in self.results:
            if len(getter(result)) > 0:
                return getter(result)
        return []

    def get_title(self):
        for result in self.results:
            if result.title is not None and len(result.title) > 0:
                return result.title
        for result in self.results:
            if result.title_jp is not None and len(result.title_jp) > 0:
                return result.title_jp
        return None

    def get_dvd_id(self, metadata_id):
        result = self.get_first_non_null(lambda x: x.dvd_id)
        return result if result is not None else metadata_id

    def get_studio(self):
        return self.get_first_non_null(lambda x: x.studio)

    def get_directors(self):
        return self.get_first_non_empty(lambda x: x.directors)

    def get_release_date(self):
        return self.get_first_non_null(lambda x: x.release_date)

    def get_collections(self):
        return self.get_first_non_empty(lambda x: x.collections)

    def get_roles(self):
        role_results = []
        data_quality = 0
        for result in self.results:
            if Prefs["actor_pictures_only"] and not result.service.has_actress_pictures():
                continue
            if result.service.get_actress_data_quality() < data_quality or len(result.roles) == 0:
                continue
            data_quality = result.service.get_actress_data_quality()
            for role in result.roles:
                if len([x for x in role_results if x.name == role.name]) > 0:
                    continue
                role_results.append(role)
        return role_results

    def get_front_cover_low_rez(self):
        return self.get_first_non_null(lambda x: x.front_cover_low_rez)

    def get_front_cover_high_rez(self):
        return self.get_first_non_null(lambda x: x.front_cover_high_rez)

    def get_full_cover_high_rez(self):
        return self.get_first_non_null(lambda x: x.full_cover_high_rez)

    def get_art(self):
        return self.get_first_non_empty(lambda x: x.art)

    def get_genres(self):
        genres = set()
        for result in self.results:
            for genre in result.genres:
                genres.add(genre)
        return genres


def get_possible_content_ids_for_id(release_id):
    if "-" not in release_id:
        Log("using literal id")
        return [release_id]
    split = release_id.split("-")
    return [(split[0] + split[1].zfill(5)).lower(),
            "1" + (split[0] + split[1].zfill(5)).lower(),
            release_id.replace("-", "").lower()]


def swap_name_order(name):
    split = name.split(' ', 1)
    if len(split) < 2:
        return name
    return split[1] + ' ' + split[0]


class Site:
    def tag(self):
        raise NotImplementedError

    def can_search(self):
        return False

    def do_search(self, release_id):
        raise NotImplementedError

    def search(self, release_id):
        try:
            return self.do_search(release_id)
        except Exception as e:
            self.DoLog("Error trying to search for " + release_id)
            self.DoLog(str(e))
            return []

    def can_get_site_ids(self):
        return False

    def do_get_site_ids(self, release_id, searcher_tag):
        raise NotImplementedError

    def get_site_ids(self, release_id, searcher_tag):
        try:
            return self.do_get_site_ids(release_id, searcher_tag)
        except Exception as e:
            self.DoLog("Error trying to get site ids for " + release_id)
            self.DoLog(str(e))
            return None

    def can_get_data(self):
        return False

    def do_get_data(self, ids, language):
        raise NotImplementedError

    def get_data(self, ids, language):
        try:
            return self.do_get_data(ids, language)
        except Exception as e:
            self.DoLog("Error trying to update metadata for " + ids.release_id)
            self.DoLog(str(e))
            return None

    def get_actress_data_quality(self):
        return 0

    def has_actress_pictures(self):
        return False

    def can_search_actor_photos(self):
        return False

    def do_get_actress_photo(self, name):
        raise NotImplementedError

    def get_actress_photo(self, name):
        try:
            return self.do_get_actress_photo(name)
        except Exception as e:
            self.DoLog("Error trying to get photo for " + name)
            self.DoLog(str(e))
            return None

    def DoLog(self, text):
        Log("[" + self.tag() + "] " + text)

    def GetException(self, text):
        self.DoLog(text)
        return Exception("[" + self.tag() + "] " + text)
