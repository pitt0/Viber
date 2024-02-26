SELECT
  track_id,
  album_id,
  artist_id
FROM
  songs
WHERE
  song_id IN (
    SELECT
      song_id
    FROM
      playlist_songs
    WHERE
      playlist_id = ?
  );
