## Anime library

Anime runs as **dedicated libraries**, not a Jellyfin "Collection" (a Collection
is an intra-library grouping; it can't carry its own metadata-provider order or
episode-ordering rules). Nothing in this compose file changes for it — the
`jellyfin` service already bind-mounts the whole media tree
(`/Volume1/nexus-pve/media:/data/media`) and the `media` stack's Sonarr/Radarr
mount the same tree at `/media`. The anime setup is entirely app-config across
Jellyfin, Sonarr, and Seerr.

### Folder layout (on `nas-01`)

```
/Volume1/nexus-pve/media/anime/          # series      -> Jellyfin "Anime" (Shows)
/Volume1/nexus-pve/media/anime-movies/   # films       -> Jellyfin "Anime Movies" (Movies)
```

Both owned `1006:997` to match the container `user:` in the `jellyfin` and
`media` stacks.

### Jellyfin libraries

Two libraries, **not** one Mixed-content library. Mixed content exposes a
reduced metadata-provider config — you lose the per-type downloader ordering,
which is the whole reason for a separate anime library. Content type can't be
changed after creation; a wrong choice means delete + re-add the library (drops
scan/metadata state only, never touches files).

| Library | Content type | Folder |
|---|---|---|
| `Anime` | Shows | `/data/media/anime` |
| `Anime Movies` | Movies | `/data/media/anime-movies` |

Metadata + image downloaders on both, in order: **AniList → AniDB → TheTVDB → TMDB**.
Requires the anime plugin repo:
`https://raw.githubusercontent.com/jellyfin/jellyfin-plugin-anime/master/manifest.json`
(Dashboard → Plugins → Repositories), then install AniList / AniDB / Kitsu and
restart.

For long-running shows that use absolute numbering (One Piece etc.), if seasons
look wrong after the first scan: series → Edit → **Display Order = Absolute**.
AniDB metadata usually handles this; TVDB-sourced entries often need the nudge.

### Sonarr routing

- Root folder `/media/anime` added in Sonarr (Media Management).
- Sonarr tag `anime` created — used by Seerr's anime routing and for anime
  release profiles / custom formats (see TRaSH-Guides "Anime" section).
- Series added via Seerr's anime path arrive with `seriesType: anime` set
  automatically (absolute numbering + anime release-name parsing).
- Anime indexers (Nyaa.si, private anime trackers) live in Prowlarr and sync
  down to Sonarr.

### Seerr routing

Seerr auto-detects anime (bundled anidb↔tvdb mapping) and applies the
**anime** field set on the Sonarr service entry — a single Sonarr server in
Seerr carries both a default and an anime set of (quality profile, root folder,
language profile, tags). Config on the Sonarr service in Seerr:

- Anime Root Folder: `/media/anime`
- Anime Quality Profile: (dedicated anime profile, or reuse HD-1080p)
- Anime Language Profile: as needed (e.g. a profile allowing Japanese + English)
- Anime Tags: `anime`
- Server must be marked **Default Server**.

**Radarr has no equivalent anime field set in Seerr** (only default + 4K
slots). With the single Radarr in the `media` stack, requested anime films flow
through the normal Radarr root into the regular movie path. Options if that
matters: (a) accept anime films in the main Movies library, (b) point the
`Anime Movies` Jellyfin library at the normal movie folder and rely on tags, or
(c) stand up a second Radarr instance. Not solved here — anime films currently
take path (a).

Auto-detection occasionally misses a title TMDB classifies oddly. An admin can
fix it after the fact by editing the request, or by using Advanced request
options (per-request server/root/profile) if that permission is granted.
