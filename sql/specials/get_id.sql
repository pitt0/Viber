SELECT
  playlist_id
FROM
  special
WHERE
  user_id = ?
  AND playlist_type = ?;
