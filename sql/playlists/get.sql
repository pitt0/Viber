SELECT
  *
FROM
  playlists
WHERE
  playlist_id = ?
  OR (
    playlist_title = ?
    AND guild_id = ?
  );
