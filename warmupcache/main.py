#!/usr/bin/python
# -*- encoding: utf-8 -*-

import logging
import argparse
import requests
import re
import time

from xml.etree import ElementTree
from progressbar import ProgressBar, Bar, RotatingMarker, Percentage, ETA
from concurrent.futures import ThreadPoolExecutor, as_completed

def getlocation(location):
    """
    get location and return page size

    """
    return len(requests.get(location).content)


class WarmUpCache:

    log = logging.getLogger("WarmUpCache")
    nsre = re.compile(r'\{(.+)\}')

    def __init__(self):
        parser = argparse.ArgumentParser(description='warmupcache')
        parser.add_argument('--dry-run', action='store_true', default=False,
                            help='dry run')
        parser.add_argument('-v', '--verbose', action='store_true', default=False)
        parser.add_argument('-q', '--no-progress', action='store_true', default=False)
        parser.add_argument('-j', '--parallel', type=int, default=1)
        parser.add_argument('sitemap', metavar='SITEMAP',
                            help='url of the sitemap')
        args = parser.parse_args()
        self.sitemap = args.sitemap
        self.dry_run = args.dry_run
        self.progress = not args.no_progress
        self.poolsize = args.parallel
        logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)

    def run(self):
        self.log.debug("get sitemap from %s", self.sitemap)
        res = requests.get(self.sitemap)
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
        if not locations:
            self.log.error("no locations found in %s", self.sitemap)
            return
        total = len(locations)
        if self.progress:
            progressbar = ProgressBar(maxval=total,
                            widgets=['Warm up cache:', Percentage(), ' ',
                            Bar(marker=RotatingMarker()), ETA()])
            progressbar.start()
        if self.dry_run:
            progressbar.finish()
            return

        self.log.debug("using parallel poolsize of %d on %d locations.",
                       self.poolsize, total)

        with ThreadPoolExecutor(max_workers=self.poolsize) as executor:
            futures = [executor.submit(getlocation, url) for url in locations]
            for fs in as_completed(futures):
                fs.result()
                if self.progress:
                    progressbar += 1
        if self.progress:
            progressbar.finish()

def cli():
    WarmUpCache().run()

if __name__ == '__main__':
    cli()
