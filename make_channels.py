#!/usr/bin/env python3
"""Writes custom.channels.xml for iptv-org/epg's grabber from channels.tsv (one channel per line:
iptv-org channel id, a tab, a name). Each channel gets up to three guide sources from iptv-org's
guides list, each under its own id (<id>~1, ~2, ~3); convert.py keeps the one that came back fullest,
so a site that is down or empty that day costs nothing.

  python3 make_channels.py guides.json channels.tsv custom.channels.xml
guides.json: https://iptv-org.github.io/api/guides.json"""
import json
import sys
from xml.sax.saxutils import escape, quoteattr

# Sources tried first: whole-service guides that are fast and steady, then broadcasters and operators.
PREFER = ['i.mjh.nz', 'pluto.tv', 'plex.tv', 'watch.whaletvplus.com', 'aljazeera.com', 'nhkworldpremium.com',
          'tvtv.us', 'tvpassport.com', 'mytelly.co.uk', 'distro.tv', 'xumo.tv', 'singtel.com',
          'content.astro.com.my', 'nowplayer.now.com', 'starhubtvplus.com', 'sky.com']
SOURCES = 3


def rank(g):
    site = PREFER.index(g['site']) if g['site'] in PREFER else len(PREFER)
    return (g.get('lang') != 'en', site)


def main(guides_path, channels_path, out_path):
    by_id = {}
    for g in json.load(open(guides_path, encoding='utf-8')):
        if g.get('channel'):
            by_id.setdefault(g['channel'], []).append(g)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<channels>']
    missing = []
    for row in open(channels_path, encoding='utf-8'):
        row = row.strip()
        if not row or row.startswith('#'):
            continue
        cid = row.split('\t')[0].split('@')[0]
        picked, seen = [], set()
        for g in sorted(by_id.get(cid, []), key=rank):
            where = (g['site'], g['site_id'].split('#')[0] if g['site'] == 'i.mjh.nz' else '')
            if where in seen:   # three different sites (or i.mjh.nz services), not one site three times
                continue
            seen.add(where)
            picked.append(g)
            if len(picked) == SOURCES:
                break
        if not picked:
            missing.append(cid)
        for n, g in enumerate(picked, 1):
            lines.append(f'  <channel site={quoteattr(g["site"])} lang={quoteattr(g.get("lang") or "en")} '
                         f'xmltv_id={quoteattr(f"{cid}~{n}")} site_id={quoteattr(g["site_id"])}>{escape(g["site_name"])}</channel>')
    lines.append('</channels>')
    open(out_path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    sites = sorted({l.split('site="')[1].split('"')[0] for l in lines if 'site="' in l})
    print(f'{len(lines) - 2} sources for the channels; sites: {" ".join(sites)}')
    if missing:
        print('no guide source:', ', '.join(missing))


if __name__ == '__main__':
    main(*sys.argv[1:4])
