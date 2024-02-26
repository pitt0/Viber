SELECT
  playlist_id,
  playlist_title
FROM
  playlists
  LEFT JOIN playlist_owners ON playlist_owners.playlist_id = playlists.playlist_id
WHERE
  playlist_title LIKE :title
  AND guild_id = :guild_id
  AND (
    privacy > :playlist_lvl
    OR (
      owner_id = :auth
      AND permission_lvl >= :playlist_lvl
    )
  );
