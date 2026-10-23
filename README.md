# TV Home programme guide

What is on now and next for TV Home's player (work/prizm/launcher), made off the TV so the TV does no
guide work: it downloads one small file (`epg.tsv.gz`, about 40-100 KB) when its copy is 6 hours old.

- `channels.tsv`: the channels covered (iptv-org channel id, name). Free, licensed streams only.
  Add a line for a new channel; the id is the `tvg-id` in TV Home's playlist.
- `make_channels.py`: picks up to three guide sources per channel from iptv-org's guides list.
- `convert.py`: keeps the fullest source per channel and writes `epg.tsv.gz` (format in its header).
- `.github/workflows/guide.yml`: runs [iptv-org/epg](https://github.com/iptv-org/epg)'s grabber every
  6 hours and force-pushes the file to the `guide` branch. TV Home reads
  `raw.githubusercontent.com/<owner>/tvhome-epg/guide/epg.tsv.gz` (jsDelivr as the fallback).

Run it on a Mac instead (Node 18+):

    git clone --depth 1 https://github.com/iptv-org/epg.git grabber && (cd grabber && npm ci --ignore-scripts)
    curl -fsSLo guides.json https://iptv-org.github.io/api/guides.json
    python3 make_channels.py guides.json channels.tsv custom.channels.xml
    (cd grabber && npm run grab --- --channels=../custom.channels.xml --output=../guide.xml --days=2)
    python3 convert.py guide.xml epg.tsv.gz

GitHub turns off scheduled workflows in a repository with no activity for 60 days. If the guide stops
updating, open the repository's Actions tab and enable the Guide workflow again.

No guide exists in iptv-org for the Sri Lankan channels (Rupavahini, ITN, Derana, Sirasa, Hiru, Siyatha,
Swarnavahini, Jaya, Shakthi); YouTube channels show their live stream's title instead.
