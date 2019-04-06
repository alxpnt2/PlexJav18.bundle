import re
import random
import urllib
import urllib2
import urlparse
import json
from datetime import datetime
from cStringIO import StringIO
import inspect

SEARCH_URL = 'https://www.r18.com/common/search/searchword='
DETAIL_URL = 'https://www.r18.com/videos/vod/movies/detail/-/id='

HDR = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

def detailItem(root,selector):
	elements = root.xpath(selector)
	if len(elements) > 0:
		text = elements[0].text_content().strip()
		if "----" in text:
			return None
		return elements[0].text_content().strip()
	return None

class Jav18Agent(Agent.Movies):
	name = 'Jav18'
	languages = [Locale.Language.English,]
	primary_provider = True
	accepts_from = ['com.plexapp.agents.localmedia']
	
	def search(self, results, media, lang):
		release_id = media.name.strip().replace(" ", "-")
		release_title = media.name
		if media.primary_metadata is not None:
			release_title = media.primary_metadata.title
		
		Log('******* MEDIA SEARCH ****** ')
		Log("Release ID:    " + str(release_id))
		Log("Release Title: " + str(release_title))
				    
		encodedId = urllib2.quote(release_id)
		url = SEARCH_URL + encodedId
		Log(url)
		req = urllib2.Request(url, headers = HDR)
		con = urllib2.urlopen(req)
		web_byte = con.read()
		webpage = web_byte.decode('utf-8')
		searchResults = HTML.ElementFromURL(url)
		Log("Got search results")
		for searchResult in searchResults.xpath('//li[contains(@class, "item-list")]'):
			Log(searchResult.text_content())
			content_id = searchResult.get("data-content_id")
			id = searchResult.xpath('a//p//img')[0].get("alt")
			title = searchResult.xpath('a//dl//dt')[0].text_content()
			if title.startswith("SALE"):
				title = title[4:]
			Log(id + " : " + title)
			score = 100 - Util.LevenshteinDistance(id.lower(), release_id.lower())
			results.Append(MetadataSearchResult(id = content_id, name = "[" + id + "] " + title, score = score, lang = lang))
				    
		results.Sort('score', descending=True) 
		Log('******* done search ****** ')
		
	def update(self, metadata, media, lang):
		Log('****** MEDIA UPDATE *******')
		Log("ID: " + str(metadata.id))
		
		url = DETAIL_URL + metadata.id
		root = HTML.ElementFromURL(url)

		id = detailItem(root,'//dt[contains(text(), "DVD ID")]/following-sibling::dd[1]')
		metadata.title = "[" + id + "] " + detailItem(root,'//cite[@itemprop="name"]')
		metadata.studio = detailItem(root,'//dd[@itemprop="productionCompany"]//a')
		director_info = detailItem(root,'//dd[@itemprop="director"]')
		metadata.directors.clear()
		if director_info != None > 0:
			director = metadata.directors.new()
			director.name = director_info
		date = detailItem(root,'//dd[@itemprop="dateCreated"]')
		date_object = datetime.strptime(date.replace(".", "").replace("Sept", "Sep").replace("July", "Jul").replace("June", "Jun"), '%b %d, %Y')
		metadata.originally_available_at = date_object
		metadata.year = metadata.originally_available_at.year   
		
		# Collections
		series = detailItem(root,'//div[contains(@class, "product-details")]//a[contains(@href, "type=series")]')
		if series != None:
			metadata.collections.add(series)
		
		# Genres
		metadata.genres.clear()
		categories = root.xpath('//div[contains(@class, "product-categories-list")]//div//a')
		for category in categories:
			genreName = category.text_content().strip()
			if "Featured" in genreName or "Sale" in genreName:
				continue
			metadata.genres.add(genreName)

		# Actors
		metadata.roles.clear()
		actors = root.xpath('//div[contains(@class, "js-tab-contents")]//ul[contains(@class, "cmn-list-product03")]//a')
		if len(actors) > 0:
			for actorLink in actors:
				role = metadata.roles.new()
				actorName = actorLink.text_content().strip()
				role.name = actorName
				actorPage = actorLink.xpath("p/img")[0].get("src")
				role.photo = actorPage
				Log("actor: " + actorName)
		else:
			Log("no actors found")

		# Posters/Background
		posterURL = root.xpath('//img[@itemprop="image"]')[0].get("src")
		Log("PosterURL: " + posterURL)			
		metadata.posters[posterURL] = Proxy.Preview(HTTP.Request(posterURL, headers={'Referer': 'http://www.google.com'}).content, sort_order = 1)
		scenes = root.xpath('//ul[contains(@class, "product-gallery")]//img')
		Log("background images: " + str(len(scenes)))
		for scene in scenes:		
			background = scene.get("data-original").replace("-", "jp-")
			Log("BackgroundURL: " + background)	
			metadata.art[background] = Proxy.Preview(HTTP.Request(background, headers={'Referer': 'http://www.google.com'}).content, sort_order = 1)
			
		Log('******* done update ****** ')
		