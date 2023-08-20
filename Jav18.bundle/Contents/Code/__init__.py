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

from site_javdb import *
from site_r18 import *
from site_r18dev import *
from site_141jav import *
from site_avwiki import *
from site_onejav import *
from site_javguru import *

try:
    from html import unescape  # python 3.4+
except ImportError:
    try:
        from html.parser import HTMLParser  # python 3.x (<3.4)
    except ImportError:
        from HTMLParser import HTMLParser  # python 2.x
    unescape = HTMLParser().unescape

SERVICES = [SiteR18Dev(), SiteJavGuru(), SiteJavDB(), SiteAVWiki(), Site141Jav(), SiteOneJav()]

CURRENT_UPDATE = "23/08/20"


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
        Log("        Version: " + CURRENT_UPDATE)
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

        searchers = [s for s in SERVICES if s.can_search()]

        for searcher in searchers:
            searcher_tag = "" if len(searchers) <= 1 else "[" + searcher.tag() + "] "
            for result in searcher.search(release_id):
                Log(searcher_tag + str(result))
                results.Append(MetadataSearchResult(id=searcher.tag() + "#" + result.id, name=searcher_tag + result.title, score=result.score, lang=lang))

        results.Sort('score', descending=True)
        Log('******* done search ****** ')

    def update(self, metadata, media, lang):
        Log('******* MEDIA UPDATE *******')
        Log("        Version: " + CURRENT_UPDATE)
        HTTP.SetTimeout(120)
        Log("Result: " + str(metadata.id))
        searcher_tag, metadata.id = metadata.id.split("#")
        Log("ID: " + str(metadata.id))

        id_gatherers = [s for s in SERVICES if s.can_get_site_ids()]
        ids = None
        for gatherer in id_gatherers:
            ids = gatherer.get_site_ids(metadata.id, searcher_tag)
            if ids is not None:
                break
        if ids is None:
            Log("Unable to find site ids for '" + metadata.id + "', trying with just the release ID.")
            ids = ContentIds(searcher_tag, metadata.id)

        updaters = [s for s in SERVICES if s.can_get_data()]
        results = MetadataResults()
        for updater in updaters:
            result = updater.get_data(ids, Prefs["language"])
            if result is not None:
                results.results.append(result)

        if results.no_results_founds():
            Log("Could not gather any metadata!")
            Log("***** UPDATE FAILED! ***** ")
            return

        metadata.title = "[" + metadata.id + "] " + ("" if results.get_title() is None else results.get_title())
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
        id_matcher = ID_PATTERN.match(metadata.id)
        if id_matcher is not None:
            metadata.collections.add(id_matcher.group(1))
        else:
            metadata.collections.add(metadata.id.split("-")[0])

        metadata.genres.clear()
        real_genres = set()
        for genre in results.get_genres():
            real_genre = get_real_genre(genre)
            if real_genre is not None:
                real_genres.add(real_genre)
            Log(str(genre) + " -> " + str(real_genre))
        for genre in real_genres:
            metadata.genres.add(genre)

        photo_gatherers = [s for s in SERVICES if s.can_search_actor_photos()]
        metadata.roles.clear()
        for actor in results.get_roles():
            role = metadata.roles.new()
            role.name = actor.name
            if actor.image_url is not None and len(actor.image_url) > 0:
                role.photo = actor.image_url
            elif Prefs["find_actor_pictures"]:
                photo_url = None
                for gatherer in photo_gatherers:
                    photo_url = gatherer.get_actress_photo(role.name)
                    if photo_url is not None:
                        break
                if photo_url is not None:
                    role.photo = photo_url

        # Posters/Background
        front_cover_high_rez = results.get_front_cover_high_rez()
        front_cover_low_rez = results.get_front_cover_low_rez()
        full_cover_high_rez = results.get_full_cover_high_rez()

        header = {'Referer': 'http://www.google.com'}

        poster_set = False
        image_cropper_failed = False
        if front_cover_high_rez is not None:
            metadata.posters[front_cover_high_rez] = Proxy.Preview(
                HTTP.Request(front_cover_high_rez, headers=header).content, sort_order=1)
            poster_set = True

        if not poster_set and full_cover_high_rez is not None:
            cropped_url = Prefs["poster_cropper_url"] + full_cover_high_rez
            try:
                metadata.posters[cropped_url] = Proxy.Preview(HTTP.Request(cropped_url, headers=header).content,
                                                              sort_order=1)
                poster_set = True
            except Exception as e:
                Log("Error trying to get cropped image url")
                Log(str(e))
                if "timed out" in str(e):
                    try:
                        Log("Timed out, trying again")
                        metadata.posters[cropped_url] = Proxy.Preview(HTTP.Request(cropped_url, headers=header).content,
                                                                      sort_order=1)
                        poster_set = True
                    except Exception as e:
                        Log("Error trying to get cropped image url (again)")
                        Log(str(e))
                        image_cropper_failed = True
                else:
                    image_cropper_failed = True

        if not poster_set and front_cover_low_rez is not None:
            metadata.posters[front_cover_low_rez] = Proxy.Preview(
                HTTP.Request(front_cover_low_rez, headers=header).content, sort_order=1)
            poster_set = True

        if not poster_set and image_cropper_failed:
            metadata.posters[full_cover_high_rez] = Proxy.Preview(
                HTTP.Request(full_cover_high_rez, headers=header).content, sort_order=1)

        if full_cover_high_rez is not None:
            metadata.art[full_cover_high_rez] = Proxy.Preview(
                HTTP.Request(full_cover_high_rez, headers=header).content, sort_order=1)
        for art in results.get_art():
            metadata.art[art] = Proxy.Preview(
                HTTP.Request(art, headers=header).content, sort_order=1)

        Log('******* done update ****** ')
