import argparse
import multiprocessing
from News import News

# if __name__ == '__main__':
def main():
    try:
        # Neat way of inputting CLI arguments
        parser = argparse.ArgumentParser(description='Scrape news articles')

        parser.add_argument("--year", dest="scrapeYear", required=False, help="Specify a specific year to collect from")
        parser.add_argument('--keywords', nargs='+', dest="keywords", required=False)
        parser.add_argument('--sources', nargs='+', dest="sources", help='Set the news websites you want to collect from',
                            required=False)
        args = parser.parse_args()

        # Check if some sources are defined as input argument, otherwise just go over all
        allSources = ['coindesk', 'reuters', 'newsbitcoin', 'wsj', 'cnbc', 'bloomberg']
        if args.sources:
            visitSources = args.sources
        else:
            visitSources = allSources

        for source in visitSources:
            # Using multiprocessing to speed things up a little. Creates new process thread for every source channel o
            # Calling getArticleURLS will also call child function that collects the actual articles
            p = multiprocessing.Process(target=News.getArticleURLS, args=(source, args))
            p.start()
    except Exception as argv:
        print('Arguments parser error, try -h' + argv)
    finally:
        pass

if __name__ == '__main__':
    main()