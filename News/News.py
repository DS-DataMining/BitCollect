#!/usr/bin/env python
# -*- coding:utf-8 -*-

# The scrapeconfig.py config file contains all xpaths for the websites that are being scraped 
# Since this scraper is modular, you can edit the scrapeconfig.py file to use this 
# scraper to collect data from ANY news website with a results and article page
# Just make sure you set correct XPaths for the properties you want to collect 

from . import scrapeconfig
import requests
from lxml import html
from dateutil.parser import parse as dateParse
import time
import importlib
import sys
import json


importlib.reload(sys)

def parsedHTML(url):
    # This function handles the web requests and parses the HTML into an lxml tree
    # Headers so we don't get 403 forbidden errors
    headers = {
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.8',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'cache-control': 'max-age=0',
        'authority': 'news.bitcoin.com',
        'cookie': '__cfduid=d784026513c887ec39604c0f35333bb231500736652; PHPSESSID=el5c5j7a26njfvoe2dh6fnrer3; _ga=GA1.2.552908756.1500736659; _gid=GA1.2.2050113212.1500736659'
    }
    page = requests.get(url)
    tree = html.fromstring(page.content)

    return tree


def collectArticles(urls, source, args, filename):
    # Loop over all the URLS that were collected in the parent function
    for url in urls:

        tree = parsedHTML(url)

        articleText = ""

        # The function that is called here is from the scrapeconfig.py file (imported)
        # Have to pass the tree along with the source key, otherwise it cant access xpaths
        config = scrapeconfig.pageConfig(source, tree)

        # If page was not found, continue to next URL
        if not config:
            continue

        # Based on xpaths defined above, call correct selector for current source
        # Could just pass the config selectors to the array, but for the sake of cleanliness...

        articleDate = config['articleDate']
        # Check against the year argument, terminate if it turns out the year for the current
        # article is < than the year you want to collect from (no point in continuing then)
        # if it does not match, don't write, if it's smaller, terminate
        if args.scrapeYear and dateParse(articleDate).year < int(args.scrapeYear):
            return True
        elif args.scrapeYear and dateParse(articleDate).year != int(args.scrapeYear):
            pass
        else:
            print(json.dumps(config))
            sys.stdout.flush()
    return False


def getArticleURLS(source, args):
    # Create filename where everything is stored eventually. Doing str(int()) so the time is rounded off
    filename = source + '_ARTICLES_' + str(int(time.time())) + '.csv'
    urls = []
    currentPage = 1
    hasNextPage = True
    outOfRange = False
    shouldStop = False

    illegal_string = ["", " ", "\n", "\t"]
    keywords = ""

    for key in args.keywords:
        if key not in illegal_string:
            if keywords == "":
                keywords = str(key)
            else:
                keywords = keywords + "+" + str(key)

    args.keywords = keywords

    while hasNextPage and not outOfRange and not shouldStop:
        # Parse HTML, invoke config (x)paths
        tree = parsedHTML(scrapeconfig.resultsConfig(currentPage, args)[source]['pageURL'])
        items = tree.xpath(scrapeconfig.resultsConfig(currentPage, args)[source]['itemXpath'])

        # For every item on the search results page...
        for item in items:
            # Here we invoke the correct Xpaths from the config dict above
            # Not every results page correctly displays datetime in result, so if it's not here
            # do the check when fetching the articles. Else, if its ordered by date just terminate if the current article date is < the year youre scraping
            if scrapeconfig.resultsConfig(currentPage, args)[source]['dateOnPage'] and \
                    scrapeconfig.resultsConfig(currentPage, args)[source]['dateOrdered'] and args.scrapeYear:
                articleDate = dateParse(
                    item.xpath(scrapeconfig.resultsConfig(currentPage, args)[source]['dateXpath'])[0].get('datetime'))

                # If we already see that the article date is not from a year we want to collect (eg if from 2014 and 2015 was specified)
                # then we just terminate the while loop. Only works one way, as articles are ordered by date, so can only do if smaller
                if articleDate.year < int(args.scrapeYear):
                    outOfRange = True
                # Note that it then just terminates on the next page (since there is no 'break' statement for the while loop)

            articleURL = item.xpath(scrapeconfig.resultsConfig(currentPage, args)[source]['urlXpath'])[0].get('href')

            # Some websites have relative URL pointers.so prefix the base URL
            if '://' not in articleURL:
                articleURL = scrapeconfig.resultsConfig(currentPage,args)[source]['baseURL'] + articleURL

            # Urlfilter hack to prevent video/audio/gadfly pages from being visited (mostly bloomberg)
            # These pages have custom xpath structures, so not even bothering collecting them
            urlFilters = ['/videos/', '/audio/', '/gadfly/', '/features/', '/press-releases/']
            # If any of the above strings is in the url, pass writing it, else write it
            if any(urlFilter in articleURL for urlFilter in urlFilters):
                pass
            else:
                urls.append(articleURL)

        # If there are less items in the results than the resultsPerPage param, we assume this is the last page
        if (len(items) < scrapeconfig.resultsConfig(currentPage, args)[source]['resultsPerPage'] and currentPage > 1) or len(items) == 0:
            hasNextPage = False

        # Increase page number by 1 for the next iteration of the while loop
        currentPage += 1
        # Once all URLs for the page have been collected, go visit the actual articles
        # Do this here so it doesn't first collect too many URLs that are useless afterwards
        shouldStop = collectArticles(urls, source, args, filename)
        if shouldStop:
            break
        # Reinitialize URLS array again for next loop
        urls = []

    print(str(source), ": All done")
    sys.stdout.flush()
