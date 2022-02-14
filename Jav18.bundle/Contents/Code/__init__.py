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
from site_r18 import *
from site_141jav import *
from site_avwiki import *

try:
    from html import unescape  # python 3.4+
except ImportError:
    try:
        from html.parser import HTMLParser  # python 3.x (<3.4)
    except ImportError:
        from HTMLParser import HTMLParser  # python 2.x
    unescape = HTMLParser().unescape

IMAGE_CROPPER_URL = "https://jav18api.herokuapp.com/crop-poster?poster-url="


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


def get_cache_file_name(filename, relative_directory=""):
    return os.path.abspath(os.path.join(CACHE_PATH, relative_directory, filename))


def save_url_to_cache(url, filename, relative_directory=""):
    downloaded = HTTP.Request(url, headers=HDR, timeout=60, cacheTime=CACHE_1DAY).content
    relative_filename = os.path.join(relative_directory, filename)
    relative_directory, filename = os.path.split(relative_filename)
    absolute_directory = os.path.abspath(os.path.join(CACHE_PATH, relative_directory))
    Log("Saving '" + filename + "' to " + absolute_directory)
    if not os.path.exists(absolute_directory):
        os.makedirs(absolute_directory)
    Data.Save(relative_filename, downloaded)


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

        searchers = [Site141Jav()]

        for searcher in searchers:
            searcher_tag = "" if len(searchers) <= 1 else "[" + searcher.tag() + "] "
            for result in searcher.search(release_id):
                Log(searcher_tag + str(result))
                results.Append(MetadataSearchResult(id=result.id, name=searcher_tag + result.title, score=result.score, lang=lang))

        results.Sort('score', descending=True)
        Log('******* done search ****** ')

    def update(self, metadata, media, lang):
        Log('****** MEDIA UPDATE *******')
        Log("ID: " + str(metadata.id))

        id_gatherers = [SiteAVWiki()]
        ids = None
        for gatherer in id_gatherers:
            ids = gatherer.get_site_ids(metadata.id)
            if ids is not None:
                break
        if ids is None:
            Log("Unable to find site ids for '" + metadata.id + "'. Trying to guess ids.")
            ids = ContentIds(metadata.id)
            ids.try_to_guess_ids()

        updaters = [SiteR18(), Site141Jav()]
        results = MetadataResults()
        for updater in updaters:
            result = updater.get_data(ids)
            if result is not None:
                results.results.append(result)

        if results.no_results_founds():
            Log("Could not gather any metadata!")
            Log("***** UPDATE FAILED! ***** ")
            return

        metadata.title = "[" + metadata.id + "] " + results.get_title()
        metadata.studio = results.get_studio()
        metadata.originally_available_at = results.get_release_date()
        metadata.year = metadata.originally_available_at.year

        metadata.directors.clear()
        for director_name in results.get_directors():
            director = metadata.directors.new()
            director.name = director_name

        metadata.collections.clear()
        for collection in results.get_collections():
            metadata.collections.add(collection)
        metadata.collections.add(metadata.id.split("-")[0])

        metadata.genres.clear()
        for genre in results.get_genres():
            metadata.genres.add(genre)

        metadata.roles.clear()
        for actor in results.get_roles():
            role = metadata.roles.new()
            role.name = actor.name
            role.photo = actor.image_url

        # Posters/Background
        front_cover_high_rez = results.get_front_cover_high_rez()
        front_cover_low_rez = results.get_front_cover_low_rez()
        full_cover_high_rez = results.get_full_cover_high_rez()

        poster_set = False
        if front_cover_high_rez is not None:
            metadata.posters[front_cover_high_rez] = Proxy.Preview(
                HTTP.Request(front_cover_high_rez, headers={'Referer': 'http://www.google.com'}).content, sort_order=1)
            poster_set = True

        if not poster_set and full_cover_high_rez is not None:
            try:
                cropped_url = IMAGE_CROPPER_URL + full_cover_high_rez
                metadata.posters[cropped_url] = Proxy.Preview(HTTP.Request(cropped_url,
                                                                           headers={
                                                                               'Referer': 'http://www.google.com'}).content,
                                                              sort_order=1)
                poster_set = True
            except Exception as e:
                Log("Error trying to get cropped image url")
                Log(str(e))

        if not poster_set and front_cover_low_rez is not None:
            metadata.posters[front_cover_low_rez] = Proxy.Preview(
                HTTP.Request(front_cover_low_rez, headers={'Referer': 'http://www.google.com'}).content, sort_order=1)

        if full_cover_high_rez is not None:
            metadata.art[full_cover_high_rez] = Proxy.Preview(
                HTTP.Request(full_cover_high_rez, headers={'Referer': 'http://www.google.com'}).content, sort_order=1)
        for art in results.get_art():
            metadata.art[art] = Proxy.Preview(
                HTTP.Request(art, headers={'Referer': 'http://www.google.com'}).content, sort_order=1)

        Log('******* done update ****** ')
