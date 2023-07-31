-- BASE TRIGGERS
-- id generation triggers
CREATE TRIGGER generate_artists_id
    AFTER INSERT ON artists
FOR EACH ROW
BEGIN 
    INSERT INTO data (data_id) VALUES ('t'||NEW.rowid);
    UPDATE artists SET artist_id = 't'||NEW.rowid WHERE rowid = NEW.rowid;
END;

CREATE TRIGGER generate_albums_id
    AFTER INSERT ON albums
FOR EACH ROW
BEGIN 
    INSERT INTO data (data_id) VALUES ('a'||NEW.rowid);
    UPDATE albums SET album_id = 'a'||NEW.rowid WHERE rowid = NEW.rowid;
END;

CREATE TRIGGER generate_songs_id
    AFTER INSERT ON songs
FOR EACH ROW
BEGIN 
    INSERT INTO data (data_id) VALUES ('s'||NEW.rowid);
    UPDATE songs SET song_id = 's'||NEW.rowid WHERE rowid = NEW.rowid;
END;

CREATE TRIGGER generate_playlists_id
    AFTER INSERT ON playlists
FOR EACH ROW
BEGIN 
    INSERT INTO data (data_id) VALUES ('p'||NEW.rowid);
    UPDATE playlists SET playlist_id = 'p'||NEW.rowid WHERE rowid = NEW.rowid;
END;

CREATE TRIGGER generate_special_id
    AFTER INSERT ON special
FOR EACH ROW
BEGIN 
    INSERT INTO data (data_id) VALUES ('f'||NEW.rowid);
    UPDATE special SET playlist_id = 'f'||NEW.rowid WHERE rowid = NEW.rowid;
END;


-- SPECIAL TRIGGERS
-- insert playlist's author into playlist_owners
CREATE TRIGGER initiate_owners
    AFTER INSERT ON playlists
BEGIN
    INSERT INTO playlist_owners VALUES (NEW.playlist_id, NEW.author_id, NEW.creation_date, 4);
END;

-- create reminder after creating advice playlist
CREATE TRIGGER generate_reminder 
    AFTER INSERT ON special
FOR EACH ROW
    WHEN NEW.playlist_type = 'Advices'
BEGIN
    INSERT INTO reminders (playlist_id) VALUES ('f'||NEW.rowid);
END;
