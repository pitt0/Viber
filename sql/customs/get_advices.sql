SELECT
  title,
  name
FROM
  songs
  JOIN tracks ON track_id
  JOIN artists ON artist_id
WHERE
  song_id = (
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
          ?
      )
  );
