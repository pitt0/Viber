```mermaid
erDiagram
    songs }o--|| albums : in
    songs {
        string song_title
        int album_id
        string duration
    }
    albums {
        string album_name
        date release_date
        string thumbnail
    }

    songs ||--|{ song_authors : by
    song_authors {
        int song_id
        int artist_id
    }
    song_authors }|--|| artists_ids : is
    artists_ids {
        string artist_name
        int genius_id
        string spotify_id
        string youtube_id
    }

    songs ||--|| external_ids : urls
    external_ids {
        int song_id
        int genius_id
        string spotify_id
        string youtube_id
    }

    albums ||--|{ album_authors : by
    album_authors {
        int album_id
        int artist_id
    }
    album_authors }|--|| artists_ids : is

    albums ||--|| external_album_ids : urls
    external_album_ids {
        int album_id
        int genius_id
        string spotify_id
        string youtube_id
    }

    playlists ||--o{ playlist_songs : contains
    playlists {
        string playlist_title
        int target_id
        int author_id
        datetime creation_date
        int privacy
    }
    playlist_songs {
        int playlist_id
        int song_id
        datetime added_in
        int added_by
    }

    playlists |o--|{ playlist_owners : owned_by
    playlist_owners {
        int playlist_id
        int owner_id
        datetime added_in
        int permission_lvl
    }

    playlist_songs |o--|| songs : matches

    playlists |o--|| reminders : has
    reminders {
        int person_id
        bool active
        int weekday
        time remind_time
        date last_sent
    }