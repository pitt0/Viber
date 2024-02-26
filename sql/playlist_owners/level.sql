SELECT
  permission_lvl,
  privacy
FROM
  playlist_owners
  JOIN playlists ON playlists.playlist_id = playlist_owners.playlist_id
WHERE
  playlist_id = ?
  AND owner_id = ?;
