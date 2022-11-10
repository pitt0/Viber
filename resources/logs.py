import datetime

class Time(datetime.datetime):
    
    def __str__(self):
        return f"{self:%T}"

    @classmethod
    def today(cls):
        now = cls.now()
        return f"{now:%d/%m/%y}"
