PRAGMA foreign_keys = true;

DROP TABLE IF EXISTS reminders;

CREATE TABLE IF NOT EXISTS reminders (
  playlist_id INTEGER UNIQUE NOT NULL, -- only refers to 'Advice' playlists
  active INTEGER NOT NULL DEFAULT 1, -- bool, 0|1
  weekday INTEGER NOT NULL DEFAULT -1, -- between -1 (unset/daily) and 6
  remind_time TEXT NOT NULL DEFAULT '16:00',
  last_sent DATE NOT NULL DEFAULT (date('now', '-1 day')),
  FOREIGN KEY (playlist_id) REFERENCES special (playlist_id) -- cannot be deleted
);
