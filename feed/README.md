# Drone build feed

`index.html` is the published artifact (https://claude.ai/artifact/PZznX76X35aGoRyHUKSt4b).
`sync_sheet.py` downloads the SharePoint build workbook (read-only) and writes `data.json`,
which the page reads. The page's **Update from Excel** button fires a Claude Code scheduled
task that runs the sync and republishes `data.json` next to the page.

Manual refresh: `python3 feed/sync_sheet.py`, then republish `feed/index.html` with
`data.json` as a supporting file.
