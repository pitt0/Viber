DELETE FROM playlist_owners
WHERE
  playlist_id = ?
  AND owner_id = ?;
