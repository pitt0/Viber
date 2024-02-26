DROP TABLE IF EXISTS special;

CREATE TABLE IF NOT EXISTS special (
  playlist_id INTEGER PRIMARY KEY,
  playlist_type TEXT NOT NULL, -- either 'Advices' or 'Favourites'
  user_id INTEGER NOT NULL,
  UNIQUE (playlist_type, user_id)
);

CREATE TRIGGER generate_reminder AFTER INSERT ON special FOR EACH ROW WHEN NEW.playlist_type = 'Advices' BEGIN
INSERT INTO
  reminders (playlist_id)
VALUES
  (NEW.playlist_id);

END;
