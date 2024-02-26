SELECT
  playlist_id,
  playlist_title,
  guild_id,
  author_id,
  creation_date,
  privacy
FROM
  playlists
  LEFT JOIN playlist_owners ON playlist_owners.playlist_id = playlists.playlist_id
WHERE
  owner_id = ?
  AND owner_lvl = 4;
