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
      special_id = (
        SELECT
          playlist_id
        FROM
          specials
        WHERE
          user_id = ?
      )
  );
