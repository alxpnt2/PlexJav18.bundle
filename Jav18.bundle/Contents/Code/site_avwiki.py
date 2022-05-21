from site import *


SEARCH_URL = URL("https://av-wiki.net/?s=", "&post_type=product")
DETAIL_URL = URL("https://av-wiki.net/", "/")


class SiteAVWiki(Site):
    def tag(self):
        return "AV-Wiki"

    def can_search(self):
        return Prefs["search_avwiki"]

    def do_search(self, release_id):
        url = SEARCH_URL.get(release_id)
        self.DoLog(url)
        search_page = HTML.ElementFromURL(url)
        results = []  # List[SearchResult]
        for searchResult in search_page.xpath('//div[contains(@class, "post")]/article'):
            id = searchResult.xpath('//li/i[contains(@class, "fa-circle-o")]/..')[0].text_content().strip()
            title = searchResult.xpath('//h2/a')[0].text_content().strip()
            self.DoLog(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.lower())
            result = SearchResult()
            result.id = id
            result.title = "[" + id + "] " + title
            result.score = score
            results.append(result)
        return results

    def can_get_site_ids(self):
        return True

    def do_get_site_ids(self, release_id, searcher_tag):
        page = None
        try:
            url = DETAIL_URL.get(release_id)
            self.DoLog(url)
            page = HTML.ElementFromURL(url)
        except:
            self.DoLog("AV-Wiki doesn't use release id '" + release_id + "' in page url, trying searching for it")
            url = SEARCH_URL.get(release_id)
            self.DoLog(url)
            search_page = HTML.ElementFromURL(url)
            first_result = search_page.xpath('//div[contains(@class, "post")]/article//div[contains(@class, "read-more")]/a')[0]
            url = first_result.get("href")
            self.DoLog(url)
            page = HTML.ElementFromURL(url)

        results = []  # List[SearchResult]
        ids = ContentIds(searcher_tag, release_id)
        for detail_key in page.xpath('//dl[contains(@class, "dltable")]/dt'):
            key = detail_key.text_content().strip()
            value = detail_key.xpath('following-sibling::dd')[0].text_content().strip()
            self.DoLog(key + " : " + value)
            if "FANZA品番" == key:
                ids.fanza_id = value
            if "MGS品番" == key:
                ids.mgs_id = value
            if key in ("SOKMIL品番", "ソクミル品番"):
                ids.sokmil_id = value
            if "DUGA品番" == key:
                ids.duga_id = value
        return ids

    def do_get_data(self, ids, language):
        pass