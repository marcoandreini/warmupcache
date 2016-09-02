#!/usr/bin/python
# -*- encoding: utf-8 -*-

import logging
import argparse
import requests
import re

from xml.etree import ElementTree
from progressbar import ProgressBar, Bar, RotatingMarker, Percentage, ETA
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import namedtuple
from datetime import timedelta

LocationData = namedtuple('LocationData', 'size elapsed')


def getlocation(location):
    """
    get location and return page size

    """
    response = requests.get(location)
    return LocationData(size=len(response.content), elapsed=response.elapsed)

def seconds(diff):
    return diff.total_seconds() + diff.microseconds / 1000000

def milliseconds(diff):
    return diff.total_seconds() * 1000 + diff.microseconds / 1000

class WarmUpCache:

    log = logging.getLogger("WarmUpCache")
    nsre = re.compile(r'\{(.+)\}')

    def __init__(self):
        parser = argparse.ArgumentParser(description='warmupcache')
        parser.add_argument('--dry-run', action='store_true', default=False,
                            help='dry run')
        parser.add_argument('-v', '--verbose', action='store_true', default=False)
        parser.add_argument('-q', '--quiet', action='store_true', default=False)
        parser.add_argument('-s', '--summary', action='store_false',
                            default=True, help='show summary informations')
        parser.add_argument('-j', '--parallel', type=int, default=1)
        parser.add_argument('-l', '--limit', type=int, help='requests limit')
        parser.add_argument('sitemap', nargs='+',
                            help='url of the sitemap')
        args = parser.parse_args()
        self.sitemap = args.sitemap
        self.dry_run = args.dry_run
        self.quiet = args.quiet
        self.summary = args.summary
        self.limit = args.limit
        self.poolsize = args.parallel
        logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    def readAll(self, sitemap):
        self.log.debug("get sitemap from %s", sitemap)
        res = requests.get(sitemap)
        if res.status_code != 200:
            self.log.error("sitemap not found")
            return
        tree = ElementTree.fromstring(res.content)
        # retrieve xmlns
        ns = self.nsre.search(tree.tag).group(1)
        namespaces = dict(sitemap=ns)
        self.log.debug("namespaces used on sitemap %s", namespaces)
        locations = [str(l.text) for l in
                     tree.findall('.//sitemap:url/sitemap:loc', namespaces)]
        if not self.limit is None:
            locations = locations[:self.limit]
        if not locations:
            self.log.error("no locations found in %s", sitemap)
            return
        total = len(locations)
        if not self.quiet:
            progressbar = ProgressBar(maxval=total,
                            widgets=['Warm up cache:', Percentage(), ' ',
                            Bar(marker=RotatingMarker()), ETA()])
            progressbar.start()
        if self.dry_run:
            progressbar.finish()
            return

        self.log.debug("using parallel poolsize of %d on %d locations.",
                       self.poolsize, total)

        results = []
        with ThreadPoolExecutor(max_workers=self.poolsize) as executor:
            futures = [executor.submit(getlocation, url) for url in locations]
            for fs in as_completed(futures):
                results.append(fs.result())
                if not self.quiet:
                    progressbar += 1
        if not self.quiet:
            progressbar.finish()

        if self.summary:
            nr = len(results)
            size = sum(r.size for r in results)
            elapsed = sum((r.elapsed for r in results), timedelta())
            print("Requests: {:d}".format(nr))
            print("Total size: {:d}".format(size))
            print("Total elapsed time: {}".format(elapsed))
            print("Average elapsed time in millisec: {:.3f} (min={:.3f}, max={:.3f})"
                  .format(milliseconds(elapsed / nr),
                          milliseconds(min(r.elapsed for r in results)),
                          milliseconds(max(r.elapsed for r in results))))
            print("Average request/second: {:.3f}".format(nr / seconds(elapsed)))

    def run(self):
        for sitemap in self.sitemap:
            self.readAll(sitemap)

def cli():
    WarmUpCache().run()

if __name__ == '__main__':
    cli()
