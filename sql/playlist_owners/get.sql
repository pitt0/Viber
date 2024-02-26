SELECT
  owner_id,
  permission_lvl
FROM
  playlist_owners
WHERE
  playlist_id = ?;
