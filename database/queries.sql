-- Parent table of all
CREATE TABLE IF NOT EXISTS data (
    data_id     TEXT NOT NULL,
    genius_id   INTEGER DEFAULT NULL,
    spotify_id  TEXT DEFAULT NULL,
    youtube_id  TEXT DEFAULT NULL,
    PRIMARY KEY (data_id)
);


CREATE TABLE IF NOT EXISTS artists (
    artist_id       TEXT UNIQUE,
    artist_name     TEXT NOT NULL,
    FOREIGN KEY (artist_id) REFERENCES data(data_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS albums (
    album_id        TEXT UNIQUE,
    album_name      TEXT NOT NULL,
    release_date    DATE NOT NULL,
    thumbnail       TEXT DEFAULT NULL,
    FOREIGN KEY (album_id) REFERENCES data(data_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS songs (
    song_id         TEXT UNIQUE,
    song_title      TEXT NOT NULL,
    song_duration   TEXT NOT NULL,
    FOREIGN KEY (song_id) REFERENCES data(data_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS playlists (
    playlist_id     TEXT UNIQUE,
    playlist_title  TEXT NOT NULL,
    guild_id        INTEGER NOT NULL,
    author_id       INTEGER NOT NULL,
    creation_date   DATE DEFAULT CURRENT_TIMESTAMP,
    privacy         INTEGER DEFAULT 1, -- 0: None; 1: View; 2: Add songs; 3: Remove songs; 4: Admin
    PRIMARY KEY (playlist_title, guild_id),
    FOREIGN KEY (playlist_id) REFERENCES data(data_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS special (
    playlist_id     TEXT UNIQUE,
    playlist_type   TEXT NOT NULL, -- either 'Advices' or 'Favourites'
    user_id         INTEGER NOT NULL,
    PRIMARY KEY (playlist_type, user_id),
    FOREIGN KEY (playlist_id) REFERENCES data(data_id) -- cannot be deleted
);



CREATE TABLE IF NOT EXISTS authors (
    data_id     TEXT NOT NULL,  -- must be either song_id or album_id, nothing else
    artist_id   TEXT NOT NULL,
    PRIMARY KEY (data_id, artist_id),
    FOREIGN KEY (data_id) REFERENCES data(data_id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES data(data_id) ON DELETE CASCADE -- artists(artist_id) might be better (?)
);

CREATE TABLE IF NOT EXISTS tracks (
    song_id     TEXT NOT NULL UNIQUE,
    album_id    TEXT NOT NULL,
    PRIMARY KEY (song_id, album_id),
    FOREIGN KEY (song_id) REFERENCES data(data_id) ON DELETE CASCADE,
    FOREIGN KEY (album_id) REFERENCES data(data_id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS reminders (
    playlist_id     TEXT NOT NULL,  -- only refers to 'Advice' playlists
    active          INTEGER NOT NULL DEFAULT 1,
    weekday         INTEGER NOT NULL DEFAULT -1, -- between -1 (unset/daily) and 6
    remind_time     TEXT NOT NULL DEFAULT '16:00',
    last_sent       DATE NOT NULL DEFAULT (date('now', '-1 day')),
    FOREIGN KEY (playlist_id) REFERENCES data(data_id)
);


CREATE TABLE IF NOT EXISTS playlist_owners (
    playlist_id     TEXT NOT NULL,
    owner_id        INTEGER NOT NULL,
    added_in        TEXT DEFAULT CURRENT_TIMESTAMP,
    permission_lvl  INTEGER NOT NULL,  -- 0: None; 1: View; 2: Add songs; 3: Remove songs; 4: Admin
    PRIMARY KEY (playlist_id, owner_id),
    FOREIGN KEY (playlist_id) REFERENCES data(data_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS playlist_songs (
    playlist_id     TEXT NOT NULL,
    song_id         TEXT NOT NULL,
    added_in        TEXT DEFAULT CURRENT_TIMESTAMP,
    added_by        INTEGER NOT NULL,
    FOREIGN KEY (playlist_id) REFERENCES data(data_id),
    FOREIGN KEY (song_id) REFERENCES data(data_id) ON DELETE CASCADE
);
