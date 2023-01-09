import datetime

class Time(datetime.datetime):
    
    def __str__(self):
        return f"{self:%T}"

    @classmethod
    def today(cls):
        now = cls.now()
        return f"{now:%d/%m/%y}"

    @staticmethod
    def from_ms(ms: int) -> str:
        duration = ms//1000
        mins = duration//60
        secs = duration - mins * 60
        if secs < 10:
            secs = f"0{secs}"
        return f"{mins}:{secs}"
