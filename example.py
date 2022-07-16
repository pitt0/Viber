from connections import Connector


with Connector() as cur:
    cur.execute("DELETE FROM Songs WHERE Spotify=?;", ('',))