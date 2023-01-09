class Ciao:

    x: int

    def print(self):
        print(self.x)

class Helo(Ciao):

    x = 12


s = Helo()
s.print()