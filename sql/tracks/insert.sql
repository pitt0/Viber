INSERT INTO
  songs (title, duration)
VALUES
  (?, ?) RETURNING track_id;
