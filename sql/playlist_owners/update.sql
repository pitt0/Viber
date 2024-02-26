UPDATE playlist_owners
SET
  permission_lvl = ?
WHERE
  playlist_id = ?
  AND user_id = ?;
