from site import *

from Contents.Code.site_141jav import Site141Jav

SEARCH_URL = URL('https://onejav.com/search/')
DETAIL_URL = URL('https://onejav.com/torrent/')


class SiteOneJav(Site141Jav):
    def get_search_url(self, release_id):
        return SEARCH_URL.get(release_id.replace("-", ""))

    def get_detail_url(self, release_id):
        return DETAIL_URL.get(release_id.replace("-", "").lower())

    def tag(self):
        return "OneJav"

    def can_search(self):
        return Prefs["search_onejav"]

    def can_get_data(self):
        return True

    def are_names_japanese_order(self):
        return False