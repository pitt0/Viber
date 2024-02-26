SELECT
  *
FROM
  playlists
WHERE
  guild_id = ?
  AND privacy > 0;
