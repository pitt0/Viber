CREATE TABLE IF NOT EXISTS playlists (
    title           TEXT NOT NULL,
    target_id       INTEGER NOT NULL, -- either guild or user id, depends on playlist type
    author_id       INTEGER NOT NULL,
    creation_date   DATE DEFAULT CURRENT_TIMESTAMP,
    privacy         INTEGER DEFAULT 1, -- 0: None; 1: View; 2: Add songs; 3: Remove songs; 4: Admin
    PRIMARY KEY (title, target_id, author_id)
);

CREATE TABLE IF NOT EXISTS albums (
    name            TEXT NOT NULL,
    release_date    DATE NOT NULL,
    thumbnail       TEXT DEFAULT NULL,
    PRIMARY KEY (name, release_date)
);

CREATE TABLE IF NOT EXISTS songs (
    title           TEXT NOT NULL,
    album_id        INTEGER NOT NULL,
    duration        TEXT DEFAULT NULL,
    PRIMARY KEY (title, album_id),
    FOREIGN KEY (album_id) REFERENCES albums (rowid)
);

CREATE TABLE IF NOT EXISTS reminders (
    person_id       INTEGER NOT NULL,
    active          INTEGER NOT NULL DEFAULT 0,
    weekday         INTEGER NOT NULL DEFAULT -1, -- between -1 (unset/daily) and 6
    remind_time     TEXT NOT NULL DEFAULT '16:00',
    last_sent       DATE NOT NULL DEFAULT (DATE('now', '-1 day')),
    FOREIGN KEY (person_id) REFERENCES playlists (target_id)
);


CREATE TABLE IF NOT EXISTS playlist_owners (
    playlist_id     INTEGER NOT NULL,
    owner_id        INTEGER NOT NULL,
    added_in        TEXT DEFAULT CURRENT_TIMESTAMP,
    permission_lvl  INTEGER NOT NULL,  -- 0: None; 1: View; 2: Add songs; 3: Remove songs; 4: Admin
    PRIMARY KEY (playlist_id, owner_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists (rowid)
);

CREATE TABLE IF NOT EXISTS playlist_songs (
    playlist_id     INTEGER NOT NULL,
    song_id         INTEGER NOT NULL,
    added_in        TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists (rowid),
    FOREIGN KEY (song_id) REFERENCES songs (rowid)
);

CREATE TABLE IF NOT EXISTS album_authors (
    album_id        INTEGER NOT NULL,
    artist          TEXT NOT NULL,
    PRIMARY KEY (album_id, artist)
    FOREIGN KEY (album_id) REFERENCES albums (rowid)
);

CREATE TABLE IF NOT EXISTS song_authors (
    song_id         INTEGER NOT NULL,
    artist          TEXT NOT NULL,
    PRIMARY KEY (song_id, artist)
    FOREIGN KEY (song_id) REFERENCES songs (rowid)
);

CREATE TABLE IF NOT EXISTS external_ids (
    song_id         INTEGER NOT NULL,
    genius_id       INTEGER DEFAULT NULL,
    spotIFy_id      TEXT DEFAULT NULL,
    youtube_id      TEXT DEFAULT NULL,
    PRIMARY KEY (song_id)
    FOREIGN KEY (song_id) REFERENCES songs (rowid)
);

CREATE TABLE IF NOT EXISTS external_album_ids (
    album_id        INTEGER NOT NULL,
    genius_id       INTEGER DEFAULT NULL,
    spotIFy_id      TEXT DEFAULT NULL,
    youtube_id      TEXT DEFAULT NULL,
    PRIMARY KEY (album_id)
    FOREIGN KEY (album_id) REFERENCES albums (rowid)
);

CREATE TABLE IF NOT EXISTS external_artists_ids (
    name            TEXT NOT NULL,
    genius_id       INTEGER DEFAULT NULL,
    spotIFy_id      TEXT DEFAULT NULL,
    youtube_id      TEXT DEFAULT NULL,
    PRIMARY KEY (name)
);