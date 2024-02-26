```mermaid
erDiagram
    data ||--o| albums : is
    data ||--o| songs : is
    data ||--o| artists : is
    data ||--o| playlists : is
    data ||--o| special : is

    data {
        string data_id
        int genius_id
        string spotify_id
        string youtube_id
    }

    songs {
        string song_id
        string song_title
        string duration
    }
    albums {
        string album_id
        string album_name
        date release_date
        string thumbnail
    }
    artists {
        string artist_id
        string artist_name
    }

    authors {
        string data_id
        string artist_id
    }
    tracks {
        string song_id
        string album_id
    }

    songs ||--|{ authors : by
    authors }|--|| artists : is

    albums ||--|{ authors : by
    authors }|--|| artists : is

    songs ||--|| tracks : in
    tracks }|--|| albums : in

    playlists ||--o{ playlist_songs : contains
    special ||--o{ playlist_songs : contains
    playlists {
        string playlist_id
        string playlist_title
        int guild_id
        int author_id
        datetime creation_date
        int privacy
    }
    special {
        string playlist_id
        string playlist_title
        int user_id
    }
    playlist_songs {
        string playlist_id
        int song_id
        datetime added_in
        int added_by
    }

    playlists |o--|{ playlist_owners : owned_by
    playlist_owners {
        string playlist_id
        int owner_id
        datetime added_in
        int permission_lvl
    }

    playlist_songs |o--|| songs : matches

    special |o--|| reminders : has
    reminders {
        string playlist_id
        bool active
        int weekday
        time remind_time
        date last_sent
    }