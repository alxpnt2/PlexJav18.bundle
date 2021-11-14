import re
import random
import urllib
import urllib2
import urlparse
import json
import os
from datetime import datetime
from cStringIO import StringIO
import inspect
from pprint import pprint

try:
    from html import unescape  # python 3.4+
except ImportError:
    try:
        from html.parser import HTMLParser  # python 3.x (<3.4)
    except ImportError:
        from HTMLParser import HTMLParser  # python 2.x
    unescape = HTMLParser().unescape

SEARCH_URL = 'https://www.r18.com/common/search/searchword='
API_URL = 'https://www.r18.com/api/v4f/contents/[ID]?lang=en&unit=USD'
IMAGE_CROPPER_URL = "https://rootanya.com/image-croper/image/crop?imageUrl="

HDR = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}


def get_search_url(release_id):
    encodedId = urllib2.quote(release_id)
    return SEARCH_URL + encodedId


def get_api_url(id):
    return API_URL.replace("[ID]", id)


def title_id_to_r18_id(id):
    if "-" not in id:
        return id
    split = id.split("-")
    return (split[0] + split[1].zfill(5)).lower()


def unencode_file_name(filename):
    if filename is None:
        return ""
    filename = filename.replace("%3A", ":")
    filename = filename.replace("%5C", "\\")
    filename = filename.replace("%2F", "/")
    filename = filename.replace("%2E", ".")
    return filename


class Jav18Agent(Agent.Movies):
    name = 'Jav18'
    languages = [Locale.Language.English, ]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang):
        Log('******* MEDIA SEARCH ******')
        release_id = media.name.strip().replace(" ", "-")
        if not "-" in release_id and media.filename is not None:
            path, release_id = os.path.split(unencode_file_name(media.filename))
            if "." in release_id:
                release_id = release_id[0:release_id.find(".")]
        release_title = media.name
        if media.primary_metadata is not None:
            release_title = media.primary_metadata.title

        Log("Filename:      " + unencode_file_name(media.filename))
        Log("Release ID:    " + str(release_id))
        Log("Release Title: " + str(release_title))

        url = get_search_url(release_id)
        Log(url)
        #req = urllib2.Request(url, headers=HDR)
        #con = urllib2.urlopen(req)
        #web_byte = con.read()
        #webpage = web_byte.decode('utf-8')
        searchResults = HTML.ElementFromURL(url)
        Log("Got search results")
        for searchResult in searchResults.xpath('//li[contains(@class, "item-list")]'):
            content_id = searchResult.get("data-content_id")
            id = searchResult.xpath('a//p//img')[0].get("alt")
            title = searchResult.xpath('a//dl//dt')[0].text_content()
            if title.startswith("Sale"):
                title = title[4:]
            Log(id + " : " + title)
            score = 100 - Util.LevenshteinDistance(id.lower(), release_id.lower())
            results.Append(MetadataSearchResult(id=content_id, name="[" + id + "] " + title, score=score, lang=lang))

        results.Sort('score', descending=True)
        Log('******* done search ****** ')

    def update(self, metadata, media, lang):
        Log('****** MEDIA UPDATE *******')
        Log("ID: " + str(metadata.id))

        content_id = title_id_to_r18_id(metadata.id)
        url = get_api_url(content_id)   
        Log(url)
        req = urllib2.Request(url, headers=HDR)
        con = urllib2.urlopen(req)
        web_byte = con.read()
        webpage = web_byte.decode('utf-8')
        data = json.loads(webpage)["data"]
        #Log(data)

        id = data["dvd_id"]
        title = data["title"]
        metadata.title = None if title is None else "[" + id + "] " + title
        metadata.studio = data["maker"]["name"]
        director_info = data["director"]
        metadata.directors.clear()
        if director_info is not None:
            director = metadata.directors.new()
            director.name = director_info
        date = data["release_date"]
        date_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        metadata.originally_available_at = date_object
        metadata.year = metadata.originally_available_at.year

        # Collections
        metadata.collections.clear()
        series = data["series"]
        if series is not None:
            metadata.collections.add(series["name"])

        # Genres
        metadata.genres.clear()
        for category in data["categories"]:
            category_name = category["name"]
            if "Featured" in category_name or "Sale" in category_name:
                continue
            metadata.genres.add(category_name)

        # Actors
        metadata.roles.clear()
        actors = data["actresses"]
        if len(actors) > 0:
            for actor in actors:
                role = metadata.roles.new()
                role.name = actor["name"]
                role.photo = actor["image_url"]
                Log("actor: " + role.name)
        else:
            Log("no actors found")

        # Posters/Background
        full_url = data["images"]["jacket_image"]["large"]
        half_url = IMAGE_CROPPER_URL + full_url
        Log("Full URL: " + full_url)
        metadata.posters[half_url] = Proxy.Preview(
            HTTP.Request(half_url, headers={'Referer': 'http://www.google.com'}).content, sort_order=1)
        metadata.art[full_url] = Proxy.Preview(
            HTTP.Request(full_url, headers={'Referer': 'http://www.google.com'}).content, sort_order=1)
        gallery = data["gallery"]
        Log("background images: " + str(len(gallery)))
        for scene in gallery:
            Log("BackgroundURL: " + scene["large"])
            metadata.art[scene["large"]] = Proxy.Preview(
                HTTP.Request(scene["large"], headers={'Referer': 'http://www.google.com'}).content, sort_order=1)

        Log('******* done update ****** ')
