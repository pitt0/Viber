PRAGMA foreign_keys = true;

DROP TABLE IF EXISTS playlist_owners;

CREATE TABLE IF NOT EXISTS playlist_owners (
  playlist_id INTEGER NOT NULL,
  owner_id INTEGER NOT NULL,
  added_in TEXT DEFAULT CURRENT_TIMESTAMP,
  permission_lvl INTEGER NOT NULL, -- 0: None; 1: View; 2: Add songs; 3: Remove songs; 4: Admin
  UNIQUE (playlist_id, owner_id),
  FOREIGN KEY (playlist_id) REFERENCES playlists (playlist_id) ON DELETE CASCADE
);
