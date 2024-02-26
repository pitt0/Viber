SELECT
  song_id,
  title
FROM
  playlist_songs
  INNER JOIN special ON special.playlist_id = playlist_songs.playlist_id
  INNER JOIN songs ON songs.song_id = playlist_songs.song_id
  INNER JOIN tracks ON songs.track_id = tracks.track_id
WHERE
  playlist_type = ?
  AND user_id = ?
  AND title LIKE ?;
