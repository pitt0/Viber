PRAGMA foreign_keys = true;

DROP TABLE IF EXISTS songs;

CREATE TABLE IF NOT EXISTS songs (
  song_id INTEGER PRIMARY KEY, -- alias to ROWID
  track_id INTEGER NOT NULL,
  album_id INTEGER NOT NULL,
  artist_id INTEGER NOT NULL,
  FOREIGN KEY (track_id) REFERENCES tracks (track_id) ON DELETE CASCADE,
  FOREIGN KEY (album_id) REFERENCES albums (album_id) ON DELETE CASCADE,
  FOREIGN KEY (artist_id) REFERENCES artists (artist_id) ON DELETE CASCADE
);
