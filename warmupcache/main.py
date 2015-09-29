#!/usr/bin/python
# -*- encoding: utf-8 -*-

import logging
import argparse
import requests
import re

from xml.etree import ElementTree
from progressbar import ProgressBar, Bar, RotatingMarker, Percentage, ETA


class WarmUpCache:

    log = logging.getLogger("WarmUpCache")
    nsre = re.compile(r'\{(.+)\}')

    def __init__(self):
        parser = argparse.ArgumentParser(description='warmupcache')
        parser.add_argument('--dry-run', action='store_true', default=False,
                            help='dry run')
        parser.add_argument('-v', '--verbose', action='store_true', default=False)
        parser.add_argument('-q', '--no-progress', action='store_true', default=False)
        parser.add_argument('sitemap', metavar='SITEMAP',
                            help='url of the sitemap')
        args = parser.parse_args()
        self.sitemap = args.sitemap
        self.really = not args.dry_run
        self.progress = not args.no_progress
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
        locations = tree.findall('.//sitemap:url/sitemap:loc', namespaces)
        if not locations:
            self.log.error("no locations found in %s", self.sitemap)
            return
        if self.progress:
            progress = ProgressBar(maxval=len(locations),
                                   widgets=['Warm up cache:', Percentage(), ' ',
                                            Bar(marker=RotatingMarker()), ETA()])
            progress.start()
        download_size = 0
        for location in locations:
            if self.really:
                self.log.debug('get %s', location.text)
                download_size = len(requests.get(location.text).content)
            if self.progress:
                progress += 1
        if self.progress:
            progress.finish()

def cli():
    WarmUpCache().run()

if __name__ == '__main__':
    cli()
