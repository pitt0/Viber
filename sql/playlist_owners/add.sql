INSERT INTO
  playlist_owners (playlist_id, owner_id, permission_lvl)
VALUES
  (?, ?, ?) ON CONFLICT DO
UPDATE permission_lvl = ?;
