import psycopg2

OPTS = {
    'host': 'ec2-54-155-226-153.eu-west-1.compute.amazonaws.com',
    'database': 'dtu7jg0lvmtej',
    'user': 'fxqymnlckfpcbm',
    'password': '72527776edc84135cdf89ee213f0ff06605b556a895320a862f37eb2de85f04b'
    }

class Connector:

    def __init__(self):
        self.connection = psycopg2.connect(**OPTS)

    def __enter__(self):
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.commit()
        self.connection.close()
