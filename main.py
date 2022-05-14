import random
import exrex as ex
import datetime as dt
import re

class INT():
    def __init__(self, min: int, max: int, step: int = 1, notnull: bool = False, unique: bool = False, key: bool = False):
        self.min = min
        self.max = max
        self.step = step
        self.notnull = notnull
        self.unique = unique
        self.key = key

    @staticmethod
    def given(max: int, notnull: bool = False, unique: bool = False, key: bool = False):
        return INT(0, max, notnull=notnull, unique=unique, key=key)

    def gen(self) -> int:
        return random.randrange(self.min, self.max + 1, self.step)

    def __str__(self):
        return f"{self.gen()}"

class STR():
    def __init__(self, regex: str, notnull: bool = False, unique: bool = False, key: bool = False):
        self.regex = regex
        self.notnull = notnull
        self.unique = unique
        self.key = key

    def gen(self) -> str:
        return ex.getone(self.regex)

    def __str__(self):
        return f"'{self.gen()}'"

class DATE():
    def __init__(self, min: str, max: str, notnull: bool = False, unique: bool = False, key: bool = False):
        self.min = dt.date.fromisoformat(min)
        self.max = dt.date.fromisoformat(max)
        self.notnull = notnull
        self.unique = unique
        self.key = key

    @staticmethod
    def given(max: str, notnull: bool = False, unique: bool = False, key: bool = False):
        return DATE('1970-01-01', max, notnull=notnull, unique=unique, key=key)

    def gen(self) -> dt.date:
        return self.min + (self.max - self.min) * random.random()

    def __str__(self):
        return f"'{str(self.gen())}'"

class BOOL():
    def __init__(self, notnull: bool = False, unique: bool = False, key: bool = False):
        self.notnull = notnull
        self.unique = unique
        self.key = key
        
    def gen(self) -> bool:
        return random.choice([True, False])

    def __str__(self):
        return f"{str(self.gen()).lower()}"

class VOTO():
    def __init__(self, notnull: bool = False, unique: bool = False, key: bool = False):
        self.notnull = notnull
        self.unique = unique
        self.key = key
    def gen(self) -> str:
        return random.choice(['18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '30L'])

    def __str__(self):
        return f"'{self.gen()}'"

class GIORNO():
    def __init__(self, weekend: bool = False, notnull: bool = False, unique: bool = False, key: bool = False):
        self.weekend = weekend
        self.notnull = notnull
        self.unique = unique
        self.key = key
        
    def gen(self) -> str:
        return random.choice(['LUN', 'MAR', 'MER', 'GIO', 'VEN'] + (['SAB', 'DOM'] if self.weekend else []))

    def __str__(self):
        return f"'{self.gen()}'"

class Table():
    def __init__(self, name: str, fields: list, fks: list = [], uniques: list = [], cascadenulls: list = [], debug = False):
        self.name = name
        self.fields = fields
        self.fks = fks
        self.uniques = uniques
        self.cascadenulls = cascadenulls
        self.keys = []
        self.generated = []
        self.debug = debug

    def gen_n(self, n: int):
        def tokeys(dic):
            z = list(filter(lambda x: x[0].key, dic))
            return [v[1] for v in z]
        def tofks(vals):
            newf = vals
            for (tab, myfields, foreignfields, options) in self.fks:
                ref = random.choice(tab.generated)
                if self.debug: print(f'Searching for suitable FK for {vals}, index {myfields}')

                while not all(f(ref[i]) for i,f in options):
                    ref = random.choice(tab.generated)

                if self.debug: print(f'FOUND')
                    
                for i, j in zip(myfields, foreignfields):
                    newf[i] = ref[j]
            return newf
        def tonullables(dic):
            vals = []
            groups = []
            for i, (f, v) in enumerate(dic):
                # Is null. mark group as nullified
                if not f.key and not f.notnull and random.random() < .1:
                    groups += [g for g in self.cascadenulls if i in g]
                vals.append(v)

            done = []
            while groups:
                g = groups.pop()
                if self.debug: print(f'BEGIN NULL SET ON {g}')

                if g in done:
                    continue
                else:
                    done.append(g)

                for i in g:
                    vals[i] = "NULL"
                    groups += [group for group in self.cascadenulls if i in group]
                    
                if self.debug: print(f'END NULL SET ON {g}')

            return vals
        def check_single_uniques(newn) -> bool:
            for i, f, v in zip(range(len(self.fields)), self.fields, newn):
                if not f.unique:
                    continue
                l = [x[i] for x in self.generated]
                if v != "NULL" and v in l:
                    if self.debug: print(f'UNIQUE FAILED FOR {i}: {v}')
                    return True
            return False
        def check_compound_uniques(newn) -> bool:
            for u in self.uniques:
                l = [newn[i] for i in u]
                saved = [[x[i] for i in u] for x in self.generated]
                if all(x != "NULL" for x in l) and l in saved:
                    if self.debug: print(f'UNIQUE FAILED FOR {u}: {l}')
                    return True
            return False
        
        while n > 0:
            new = self.gen()
            
            # Foreign key adjust
            newf = tofks(new)

            # Check primary key
            newk = tokeys(list(zip(self.fields, newf)))

            # If the key is already present, try again
            if newk in self.keys:
                if self.debug: print('KEY ALREADY PRESENT')
                continue
            
            # Nullable checks
            newn = tonullables(list(zip(self.fields, newf)))

            # If a unique field/set of fields already exists,
            #   discard the generated values
            if check_single_uniques(newn):
                continue
            if check_compound_uniques(newn):
                continue

            # The data is ok, store it
            self.keys.append(newk)
            self.generated.append(newn)
            n -= 1

    def __str__(self):
        return '\n'.join(f"INSERT INTO {self.name} VALUES ({', '.join(g)});" for g in self.generated)

    def gen(self):
        return [str(field) for field in self.fields]

    def tofile(self, n):
        if not self.generated:
            self.gen_n(n)
        with open(f"out/{self.name}.sql", 'w') as f:
            f.write(str(self))

    @staticmethod
    def fromData(name, fields, data):
        tbl = Table(name, fields)
        tbl.generated = data
        return tbl
        

# Defining tables
# Studenti
studenti = Table('Studenti',
                 [
                     INT(1,100000, key=True),
                     STR(r'[A-Z]{6}\d{2}(([ACELMRT](([04][1-9])|([1256][0-9])|([37][01])))|([DHPS](([04][1-9])|([1256][0-9])|([37]0)))|(B(([04][1-9])|([1256][0-9]))))[A-Z]\d{3}[A-Z]', notnull=True, unique=True),
                     STR(r'[A-Z][a-z]{1,9}', notnull=True),
                     STR(r'[A-Z][a-z]{1,9}', notnull=True),
                     STR(r'[a-z]{6,10}@[a-z]{5,10}\.[a-z]{2,5}', unique=True),
                     DATE('1980-01-01', '2003-02-02', notnull=True),
                     INT(2000, 2022, notnull=True)
                 ])
studenti.tofile(1000)

# Dipartimenti
dipartimenti = Table('Dipartimenti',
                     [
                         STR(r'[A-Z]{4}', key=True),
                         STR(r'[a-z ,]{5,30}', notnull=True)
                     ])
dipartimenti.tofile(3)

# Sedi
sedi = Table('Sedi',
             [
                 STR('[A-Z][a-z ]{3,10}', key=True),
                 STR('[A-Z]{4}', key=True),
                 STR('[a-z]{10}'),
                 INT(1,100),
                 INT(0,10000, notnull=True),
                 STR('Italia|Austria', notnull=True)
             ],
             fks=[(dipartimenti, [1], [0], [])],
             cascadenulls=[[2,3]])
sedi.tofile(15)

# Edifici
edifici = Table('Edifici',
                [
                    STR('[A-Z]', key=True),
                    STR('[A-Z][a-z ]{3,10}', key=True),
                    STR('[A-Z]{4}', key=True),
                    INT(1,4, notnull=True)
                ],
                fks=[(sedi, [1,2], [0,1], [])])
edifici.tofile(37)

# Stanze
stanze = Table('Stanze',
               [
                   STR(r'[A-G]?[1-9]\d?|[1-9]\d?\d?', key=True),
                   STR('[A-Z]'),
                   STR('[A-Z][a-z ]{3,10}'),
                   STR('[A-Z]{4}', key=True),
                   INT(0, 3, notnull=True),
               ],
               fks=[(edifici, [1,2,3], [0,1,2], [])])
stanze.tofile(1800)

uff = list(filter(lambda x: re.match(r"^\'\d", x[0]), stanze.generated))
au  = list(filter(lambda x: re.match(r"^\'\D", x[0]), stanze.generated))

# Uffici
uffici = Table.fromData('Uffici',
                        [
                            STR(r'[1-7]\d?', key=True),
                            STR('[A-Z]{4}', key=True),
                        ],
                        uff)
uffici.tofile(-1)

aule = Table.fromData('Aule',
                     [
                         STR(r'[A-G][1-7]\d?', key=True),
                         STR('[A-Z]{4}', key=True),
                         INT(30, 500)
                     ],
                      au)
aule.tofile(-1)

# Laboratori
laboratori = Table('Laboratori',
                   [
                       STR(r'[A-G][1-7]\d?', key=True),
                       STR('[A-Z]{4}', key=True)
                   ],
                   fks=[(aule, [0, 1], [0, 1], [])])
laboratori.tofile(10)

# Docenti
docenti = Table('Docenti',
                [
                    INT(1, 5000, key=True),
                    STR(r'[A-Z]{6}\d{2}(([ACELMRT](([04][1-9])|([1256][0-9])|([37][01])))|([DHPS](([04][1-9])|([1256][0-9])|([37]0)))|(B(([04][1-9])|([1256][0-9]))))[A-Z]\d{3}[A-Z]', notnull=True, unique=True),
                    STR(r'[A-Z][a-z]{1,9}', notnull=True),
                    STR(r'[A-Z][a-z]{1,9}', notnull=True),
                    STR(r'[a-z]{6,10}@[a-z]{5,10}\.[a-z]{2,5}', unique=True, notnull=True),
                    STR(r'\d{8,10}', unique=True, notnull=True),
                    STR(r'[A-Z]{4}', notnull=True),
                    STR(r'[1-9]\d?\d?')
                ],
                fks=[(uffici, [7, 6], [0, 1], [])],
                uniques=[[6,7]])
docenti.tofile(300)

ric = docenti.generated[:99]
oras = docenti.generated[100:]
ordi = oras[:99]
ass = oras[100:]

# Ricercatori
ricercatori = Table.fromData('Ricercatori',
                             [
                                 INT(1, 5000, key=True),
                             ],
                             ric)
ricercatori.tofile(-1)

# OrdAss
ordass = Table.fromData('OrdAss',
                        [
                            INT(1, 5000, key=True),
                        ],
                        oras)
ordass.tofile(-1)

# Ordinario
ordinario = Table.fromData('Ordinario',
                           [
                               INT(1, 5000, key=True),
                           ],
                           ordi)
ordinario.tofile(-1)

# Associato
associato = Table.fromData('Associato',
                           [
                               INT(1, 5000, key=True),
                           ],
                           ass)
associato.tofile(-1)

# Personale Amministrativo
personaleamministrativo = Table('PersonaleAmministrativo',
                                [
                                    INT(1, 5000, key=True),
                                    STR(r'[A-Z]{6}\d{2}(([ACELMRT](([04][1-9])|([1256][0-9])|([37][01])))|([DHPS](([04][1-9])|([1256][0-9])|([37]0)))|(B(([04][1-9])|([1256][0-9]))))[A-Z]\d{3}[A-Z]', notnull=True, unique=True),
                                    STR(r'[A-Z][a-z]{1,9}', notnull=True),
                                    STR(r'[A-Z][a-z]{1,9}', notnull=True),
                                    STR(r'[a-z]{6,10}@[a-z]{5,10}\.[a-z]{2,5}', unique=True, notnull=True),
                                    STR(r'\d{8,10}', unique=True, notnull=True),
                                    STR(r'segretario|tecnico|[a-z]{5,10}', notnull=True),
                                    STR(r'[A-G]?[1-7]\d?', notnull=True),
                                    STR(r'[A-Z]{4}', notnull=True)
                                ],
                                fks=[(stanze, [7, 8], [0, 3], [])])
personaleamministrativo.tofile(150)

# Corsi
corsi = Table('Corsi',
              [
                  STR(r'[A-Z\-]{5,8}', key=True),
                  STR(r'[a-z \,]{20,100}', notnull=True),
                  STR(r'[a-z ,]{5,30}', notnull=True),
                  INT(1, 3, notnull=True),
              ])
corsi.tofile(20)

edizionicorsi = Table('EdizioniCorsi',
                      [
                          STR(r'[A-Z\-]{5,8}', key=True),
                          INT(2011, 2022, key=True),
                          BOOL(notnull=True),
                          BOOL(notnull=True),
                          BOOL(notnull=True),
                          INT(1, 4, notnull=True)
                      ],
                      fks=[(corsi, [0], [0], [])])
edizionicorsi.tofile(150)

lezioni = Table('Lezioni',
                [
                    STR(r'[A-Z\-]{5,8}', key=True),
                    INT(2011, 2022, key=True),
                    GIORNO(key=True),
                    STR(r'(0[89]|1[0-7]):(00|30)', key=True),
                    STR(r'[A-G]?[1-7]\d?', notnull=True),
                    STR(r'[A-Z]{4}', notnull=True),
                    INT(60, 180, step=30, notnull=True)
                ],
                fks=[(edizionicorsi, [0,1], [0,1], []), (aule, [4,5], [0, 1], [])])
lezioni.tofile(375)

esami = Table('Esami',
              [
                  INT(1, 10000, key=True),
                  STR(r'[A-Z\-]{5,8}', key=True),
                  VOTO(notnull=True),
                  DATE('2012-01-01','2022-05-14',notnull=True)
              ],
              fks=[(studenti, [0], [0], []), (corsi, [1], [0], [])])
esami.tofile(10000)
