from resources.connections import Connection


def read(sql: str, *params) -> list:
    with Connection() as cursor:
        cursor.execute(sql, *params)
        return cursor.fetchall()

def check(sql: str, *params) -> bool:
    with Connection() as cursor:
        cursor.execute(sql, *params)
        return bool(cursor.fetchone())
    
def write(sql: str, *params) -> None:
    with Connection() as cursor:
        cursor.execute(sql, *params)
