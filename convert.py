#!/usr/bin/env python3
"""Turns the grabber's XMLTV (guide.xml) into the small file TV Home reads (epg.tsv.gz).

For each channel, of its up-to-three sources (<id>~1, ~2, ~3; see make_channels.py) the one that
covers the next 24 hours best is kept. Programmes from an hour ago to three days ahead, overlaps
trimmed, descriptions cut to 220 characters. Format, UTF-8, gzip:
  #TVHOME-EPG 1 <generated, UTC>
  =<channel id>\t<name>
  <start>\t<stop>\t<title>\t<description>      (Unix seconds)

  python3 convert.py guide.xml epg.tsv.gz"""
import gzip
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime

KEEP_BEFORE, KEEP_AFTER, SCORE_SPAN = 3600, 3 * 86400, 86400
DESC_MAX = 220


def when(stamp):
    """XMLTV '20261023180000 +0000' -> Unix seconds."""
    stamp = stamp.strip()
    fmt = '%Y%m%d%H%M%S %z' if ' ' in stamp else '%Y%m%d%H%M%S'
    t = datetime.strptime(stamp, fmt)
    return int(t.timestamp()) if t.tzinfo else int(time.mktime(t.timetuple()))


def clean(text, limit=None):
    text = ' '.join((text or '').split())
    if limit and len(text) > limit:
        cut = text[:limit].rsplit(' ', 1)[0]
        text = cut.rstrip(',.;:-') + '…'
    return text


def main(src, dest):
    now = int(time.time())
    names, sources = {}, {}
    for _, el in ET.iterparse(src, events=('end',)):
        if el.tag == 'channel':
            names.setdefault(el.get('id', '').split('~')[0], clean(el.findtext('display-name')))
        elif el.tag == 'programme':
            try:
                start, stop = when(el.get('start')), when(el.get('stop'))
            except (TypeError, ValueError):
                el.clear()
                continue
            if stop > now - KEEP_BEFORE and start < now + KEEP_AFTER and stop > start:
                title = clean(el.findtext('title'))
                sub = clean(el.findtext('sub-title'))
                if sub and sub.lower() not in title.lower():
                    title = f'{title} · {sub}'
                if title:
                    sources.setdefault(el.get('channel', ''), []).append((start, stop, title, clean(el.findtext('desc'), DESC_MAX)))
            el.clear()
    best = {}
    for source, shows in sources.items():
        cid = source.split('~')[0]
        cover = sum(max(0, min(stop, now + SCORE_SPAN) - max(start, now)) for start, stop, _, _ in shows)
        score = (cover, len(shows))
        if cid not in best or score > best[cid][0]:
            best[cid] = (score, source, shows)
    out = [f'#TVHOME-EPG 1 {time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(now))}']
    report = []
    for cid in sorted(best):
        (cover, count), source, shows = best[cid]
        shows = sorted(set(shows))
        kept = []
        for s in shows:
            if kept and s[0] < kept[-1][1]:   # overlaps the one before: that one ends here
                if s[0] <= kept[-1][0]:
                    continue
                kept[-1] = (kept[-1][0], s[0]) + kept[-1][2:]
            kept.append(s)
        out.append(f'={cid}\t{names.get(cid, cid)}')
        out.extend(f'{a}\t{b}\t{t}\t{d}' for a, b, t, d in kept)
        report.append(f'{cid:28} {len(kept):4} programmes, {cover / 3600:4.1f} h of the next 24 (source {source.split("~")[-1]})')
    data = ('\n'.join(out) + '\n').encode('utf-8')
    with open(dest, 'wb') as f:
        with gzip.GzipFile(fileobj=f, mode='wb', mtime=0, compresslevel=9) as z:
            z.write(data)
    print('\n'.join(report))
    print(f'{len(best)} channels, {len(data)} bytes, {sum(1 for _ in open(dest, "rb").read())} gzipped -> {dest}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
