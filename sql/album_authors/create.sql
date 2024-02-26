PRAGMA foreign_keys = true;

DROP TABLE IF EXISTS album_authors;

CREATE TABLE IF NOT EXISTS album_authors (
  costraint_id INTEGER PRIMARY KEY,
  album_id INTEGER NOT NULL,
  artist_id INTEGER NOT NULL,
  FOREIGN KEY (album_id) REFERENCES albums (album_id),
  FOREIGN KEY (artist_id) REFERENCES artists (artist_id)
);
