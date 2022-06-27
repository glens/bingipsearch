#!/usr/bin/env python

# bingipsearch.py, a CLI tool to find alternative hostnames via Bing IP search
# Author: Glen Scott (glen at glenscott.net, @memoryresident)
# github.com/glens/bingipsearch

# todo: add option to suppress verbosity
# todo: validate hosts via dns resolution
# todo: handle multiple A records returned when a host is passed as the first argument


import sys, socket, time, copy
import urllib.request
from bs4 import BeautifulSoup as BS

def extractHostname(urltag):
	if urltag is None:
		return None

	urltext = urltag.findAll(text = True)
	url=''.join(urltext).rstrip()

	# todo: verbose / debug only
	print("found url: " + url)

	if '://' in url:
		url = (url.split('://', 1)[1])

	# extract the hostname from url string
	for character in [ ':', '/', '?', '&', ' ']:
		url = (url.split(character, 1)[0])

	return str(url)

	
def getHtmlPage(nexturl):
	# Send a basic mobile user agent to get the simplified version of the page
	headers = { 'User-Agent' : 'Mozilla/5.0 (Linux; U; Android 1.5; en-us; AppleWebkit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1' }
	httprequest = urllib.request.Request(nexturl, None, headers)
	htmlblob = urllib.request.urlopen(httprequest).read()
	htmlpage = BS(htmlblob, features="html.parser")
	return htmlpage

	
def filterbogeys(hostset, ipaddress):
	print("\nFiltering " + str(len(hostset)) + " host(s) via forward lookups")
	hostset_loopcopy = copy.copy(hostset)
	
	for host in hostset_loopcopy:
		print("attempting to resolve " + host)
		try: 
			resolvedip = socket.gethostbyname(host) 
			if resolvedip != ipaddress:
				hostset.remove(host)
		except:
			print(host + "not resolvable, removing from list")
	return hostset


def printfoundhosts(hostset):
	print("Found " + str(len(hostset)) + " hostname(s): ")
	for host in hostset:
		print(str(host))


def bingCheckNext(searchsite, bingpage):

	'''
	This function decides if we have reached the last page of search results or not.
	'''

	nextpagelink = bingpage.find_all('a', attrs={"title" : "Next page"})
	page_citations = bingpage.find_all('cite')

	# if there are the max (10) results on the page, and the next page link exists
	# have to check for max results since bing always returns a 'next page' link

	if len(page_citations) == 10 and len(nextpagelink) > 0:
		return searchsite + str(nextpagelink[0].get('href'))
	
	return 'none'


def scrapeBing(hostset, ipaddress):
	bingurl = "http://www.bing.com"

	# using "+" operator to work around a bug in bing where blank pages are returned using just ip:
	bingpage = "/search?q=+ip:"
	pagenumber = 1

	print("Requesting bing IP search results for " + ipaddress)
	requestpage = bingurl + bingpage + ipaddress
	
	while requestpage != 'none' :
		htmlpage = getHtmlPage(requestpage)
	
		# relevant host entries are usefully contained in <cite> tags
		for citationtag in htmlpage.findAll('cite'):
			hostset.add(extractHostname(citationtag))
		
		# check if there is a 'next' link in the results
		requestpage = bingCheckNext(bingurl, htmlpage)
		if requestpage != 'none':
			pagenumber = pagenumber + 1
			print("Requesting page " + str(pagenumber))
			time.sleep(3)

	return hostset

	
def main():
	hostset = set()

	try:
		ipaddress = socket.gethostbyname(sys.argv[1])
		
	except:
		sys.exit('usage: ' + sys.argv[0] + ' ip.address.or.hostname')

	hostset = scrapeBing(hostset, ipaddress)

	printfoundhosts(hostset)

main()
