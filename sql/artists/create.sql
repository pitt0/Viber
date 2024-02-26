DROP TABLE IF EXISTS artists;

CREATE TABLE IF NOT EXISTS artists (
  artist_id INTEGER PRIMARY KEY,
  artist_name TEXT NOT NULL,
  spotify_id TEXT UNIQUE DEFAULT NULL,
  youtube_id TEXT UNIQUE DEFAULT NULL
);