SELECT
  song_id,
  title,
  'by',
  artist_name
FROM
  songs
  JOIN tracks ON songs.track_id = tracks.track_id
  LEFT JOIN artists ON songs.track_id = artists.artist_id;
