DELETE FROM playlist_songs
WHERE
  playlist_id = ?
  AND song_id = ?;
