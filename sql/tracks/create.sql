DROP TABLE IF EXISTS tracks;

CREATE TABLE IF NOT EXISTS tracks (
  track_id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  duration REAL NOT NULL,
  duration_str TEXT NOT NULL,
  spotify_id TEXT UNIQUE DEFAULT NULL,
  youtube_id TEXT UNIQUE DEFAULT NULL
);