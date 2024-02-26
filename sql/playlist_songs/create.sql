PRAGMA foreign_keys = true;

DROP TABLE IF EXISTS playlist_songs;

CREATE TABLE IF NOT EXISTS playlist_songs (
  playlist_id INTEGER NULL,
  special_id INTEGER NULL,
  song_id INTEGER NOT NULL,
  added_in TEXT DEFAULT CURRENT_TIMESTAMP,
  added_by INTEGER NOT NULL,
  FOREIGN KEY (playlist_id) REFERENCES playlists (playlist_id) ON DELETE CASCADE,
  FOREIGN KEY (special_id) REFERENCES special (playlist_id), -- cannot be deleted
  FOREIGN KEY (song_id) REFERENCES songs (song_id) ON DELETE CASCADE,
  CHECK (
    CASE
      WHEN playlist_id IS NULL THEN 0
      ELSE 1
    END + CASE
      WHEN special_id IS NULL THEN 0
      ELSE 1
    END = 1
  )
);
