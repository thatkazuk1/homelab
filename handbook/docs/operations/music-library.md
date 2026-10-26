# Operations: music library (Lidarr to Navidrome)

This page describes how a song that you see on TikTok or IG becomes a correctly tagged track in
Navidrome. It also records the settings that make this work, so that a rebuild of `nas-01` can
repeat them.

## The flow

```text
You see a song      Lidarr                    slskd or qBittorrent        Lidarr import               Navidrome
(TikTok, IG)   -->  search, monitor      -->  download the release   -->  copy, rename, write   -->  scan, play,
Shazam or caption   (MusicBrainz data)                                    MusicBrainz tags            scrobble
```

One database decides what a release is: **MusicBrainz**. Lidarr uses it, Lidarr writes its IDs into
the files, and Navidrome reads them. A track that Lidarr matched is therefore the same track
everywhere.

## Add a song that you saw

1. **Identify it.** Use Shazam, or read the caption and the comments. Write down the **artist** and
   the **release** (the single, EP or album). A song on TikTok is often a single.
2. **Open Lidarr** (`nas-01.lan:8686`) and click **Add New**. Search for the artist.
3. In the add dialog, leave **Monitor** on **None**. This is the default for this root folder. It
   stops Lidarr from fetching the whole discography.
4. Open the artist. Find the single, EP or album in the list. Click its **monitor** switch, then its
   **search** (magnifier) icon.
5. Lidarr searches its indexers (Soulseek through the Tubifarry plugin and slskd, and the torrent
   indexers). It grabs the best release for the quality profile and imports it. Navidrome picks it
   up within seconds.
6. **Check the result** in Navidrome: the right artist, the cover, the track list, and one correct
   year. If anything is wrong, see "When the match is wrong" below.

## The rules (settings in Lidarr)

| Setting | Value | Reason |
|---|---|---|
| Quality profile | **Lossless first**: allows `High Quality Lossy` (MP3 320, V0, AAC 320) and `Lossless` (FLAC, ALAC), cutoff `Lossless`, upgrades on | Take FLAC when it exists. Accept a good lossy file now. Upgrade later. Low-bitrate files are never accepted. |
| Metadata profile | **Albums, EPs and Singles**: primary types Album, EP, Single. Secondary types Studio, Soundtrack, Remix, Mixtape/Street. Release status Official. | The default `Standard` has only Album, so a viral single never appears. |
| Root folder defaults | Monitor **None**, monitor new items **None** | You choose each release. Nothing is downloaded by default. |
| Tag audio files | **New files only**, cover art embedded | Lidarr writes the MusicBrainz IDs, the album artist, and the track and disc counts. Navidrome needs them to group tracks. |
| Rename tracks | **On**, Lidarr default formats | One folder per album: `Artist/Album (Year)/Artist - Album - 01 - Title.flac` |
| Use hardlinks | **Off** (copy) | A tag write changes the file. A hardlinked file is also the file that qBittorrent seeds, and a changed file breaks the seed. When the torrent rechecks, it can restore the old data over your tags. |

Lidarr does not support Recyclarr, so these values are set by hand (they are not synced from Git).
Create the two profiles first, then set the root folder defaults.

## When the match is wrong or missing

| Symptom | Cause | What to do |
|---|---|---|
| The release is not in Lidarr's search | It is not in MusicBrainz yet. Typical: sped-up edits, TikTok remixes, very new songs, small local artists. | Add it to MusicBrainz (a free account, **Add Release**). Then use **Refresh** on the artist in Lidarr. |
| A download waits in **Activity → Queue** with "unmatched" | The files have no tags, or the names do not match | **Activity → Queue → Manual Import**: choose the release by hand |
| Tracks show under two albums in Navidrome | An old copy is still listed (renamed or retagged files) | Run a **full scan** in Navidrome, then open the admin page **Missing files** and remove the missing entries |
| Only a lossy file was found | No FLAC is on Soulseek or the trackers yet | Leave it. The profile upgrades it when FLAC shows up. |
| You have files that did not come from Lidarr | They carry any tags | Tag them with MusicBrainz Picard, then use Lidarr **Manual Import** from a folder |

## Music that is not in MusicBrainz (DJ edits, mixes)

Lidarr cannot import a release that MusicBrainz does not list. For example, a DJ playlist from Samply
is not in MusicBrainz. Add such music by hand, outside the Lidarr flow:

1. Put the files in `/Volume1/data/media/music/<Artist>/<Album>/`. The owner must be `1006:997`.
2. Write the tags with `ffmpeg`: title, artist, album, album artist, track number (`N/total`) and an embedded cover.
   Convert WAV to FLAC (lossless), because WAV has weak tag support. Keep MP3 as MP3.
3. Name the files `NN - Title.ext`. Put the cover in the album folder as `folder.jpg`.
4. Compare each file length with the length on the source page. A match confirms the right title for each file.
5. Wait for the Navidrome watcher (a few seconds). Check that the album shows the right track count.

Do not run a Lidarr rename or retag on these folders. Lidarr does not know them. These tracks have no
MusicBrainz IDs, so ListenBrainz may not link them to a recording.

## Artist pictures

Navidrome fetches an artist picture from Deezer the first time you open the artist. Nothing to do for
most artists. Deezer does not know some artists (small local artists, DJs). For those artists, put a file
named `artist.jpg` in the artist folder, for example `/Volume1/data/media/music/<Artist>/artist.jpg`.
A local `artist.jpg` takes priority over the Deezer picture.

## Navidrome settings

| Variable | Value | Reason |
|---|---|---|
| `ND_MUSICFOLDER` | `/media/music` (read-only mount of `/Volume1/data/media/music`) | Navidrome never changes the files |
| `ND_SCANNER_SCHEDULE` | `@every 1h` | A safety net. The file watcher (default wait 5 s) scans after each import. The old name `ND_SCANSCHEDULE` is not in the current documentation. |
| `ND_ENABLEINSIGHTSCOLLECTOR` | `false` | It is on by default and sends anonymous usage data |
| `ND_ENABLESHARING` | `false` | It is on by default. It would allow public share links on a service that is reachable from the internet. |
| `ND_SEARCH_FULLSTRING` | `true` | A search matches anywhere in a name |
| `ND_LASTFM_APIKEY` | In `secrets.enc.env` | Artist biographies only. It does not scrobble. |

`ND_PASSWORDENCRYPTIONKEY` is **not** set. It protects the stored user passwords. The documentation
does not say what happens to existing users when you change it later, and the Subsonic apps and the
Homepage widget depend on those passwords. Set it only on a fresh install, before you make users.

## Scrobbling to ListenBrainz

ListenBrainz keeps your listening history and uses MusicBrainz IDs, the same IDs that the files now
carry.

1. Make a free account at `listenbrainz.org`. Open **Settings** and copy your **user token**.
2. In Navidrome, open your user menu, then **Personal**. Paste the token in the ListenBrainz field,
   and turn **Scrobble to ListenBrainz** on.
3. Turn scrobbling **off** in your phone app (Symfonium). Otherwise a track is counted twice.

Treat the token like a password. Do not put it in Git.

## Phone app (Symfonium)

The rebuild of `nas-01` made new song IDs. Symfonium still asked for the old IDs, and Navidrome
answered "not found". Open the Navidrome provider in Symfonium and run **Clear library cache** (or
remove the provider and add it again), then sync.

## Later, optional

- **Discovery loop.** Lidarr can read lists from ListenBrainz ("created for you" playlists) and
  Last.fm. They would add suggestions on their own. This is off on purpose: you decided that every
  release is chosen by hand.
- **A second Navidrome user.** Keep `kazuki` as the admin and make a normal user for daily listening.
