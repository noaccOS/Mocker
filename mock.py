import random
import exrex as ex
import datetime as dt

# No actual data for names and descriptions, just random strings.
# Should work good enough for its purpose.

class INT():
    def __init__(self, min: int, max: int, step: int = 1, notnull: bool = False, unique: bool = False, key: bool = False):
        self.min = min
        self.max = max + 1
        self.step = step
        self.notnull = notnull
        self.unique = unique
        self.key = key

    def gen(self) -> int:
        return random.randrange(self.min, self.max, self.step)

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


class PERSON_NAME():
    def __init__(self, notnull: bool = False, unique: bool = False, key: bool = False):
        self.notnull = notnull
        self.unique = unique
        self.key = key
        self._cache = None
        
    def gen(self) -> str:
        if not self._cache:
            with open('in/names', 'r') as f:
                self._cache = list(map(lambda l: l[:-1], f.readlines()))
        return random.choice(self._cache)

    def __str__(self):
        return f"'{self.gen()}'"

class PERSON_SURNAME():
    def __init__(self, notnull: bool = False, unique: bool = False, key: bool = False):
        self.notnull = notnull
        self.unique = unique
        self.key = key
        self._cache = None
        
    def gen(self) -> str:
        if not self._cache:
            with open('in/surnames', 'r') as f:
                self._cache = list(map(lambda l: l[:-1], f.readlines()))
        return random.choice(self._cache)

    def __str__(self):
        return f"'{self.gen()}'"
    
class Table():
    def __init__(self, name: str, fields: list, fks: list = [], uniques: list = [], cascadenulls: list = [], post_triggers: list = [], pre_triggers: list = [], debug = False):
        self.name = name
        self.fields = fields
        self.fks = fks
        self.uniques = uniques
        self.cascadenulls = cascadenulls
        self.pre_triggers = pre_triggers
        self.post_triggers = post_triggers
        self.keys = []
        self.generated = []
        self._debug = debug

    def gen_n(self, n: int, _existing_data = [], _data_assign = {}):
        def tokeys(dic):
            z = list(filter(lambda x: x[0].key, dic))
            return [v[1] for v in z]
        def tofks(vals):
            newf = vals
            for (tab, myfields, foreignfields, options) in self.fks:
                ref = random.choice(tab.generated)
                if self._debug: print(f'Searching for suitable FK for {vals}, index {myfields}')

                while not all(f(ref, vals) for f in options):
                    ref = random.choice(tab.generated)

                if self._debug: print(f'FOUND')
                    
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
                if self._debug: print(f'BEGIN NULL SET ON {g}')

                if g in done:
                    continue
                else:
                    done.append(g)

                for i in g:
                    vals[i] = "NULL"
                    groups += [group for group in self.cascadenulls if i in group]
                    
                if self._debug: print(f'END NULL SET ON {g}')

            return vals
        def check_single_uniques(newn) -> bool:
            for i, f, v in zip(range(len(self.fields)), self.fields, newn):
                if not f.unique:
                    continue
                l = [x[i] for x in self.generated]
                if v != "NULL" and v in l:
                    if self._debug: print(f'UNIQUE FAILED FOR {i}: {v}')
                    return True
            return False
        def check_compound_uniques(newn) -> bool:
            for u in self.uniques:
                l = [newn[i] for i in u]
                saved = [[x[i] for i in u] for x in self.generated]
                if all(x != "NULL" for x in l) and l in saved:
                    if self._debug: print(f'UNIQUE FAILED FOR {u}: {l}')
                    return True
            return False
        
        while n > 0:
            new = self.gen()
            
            # Apply pre triggers
            for t in self.pre_triggers:
                new = t(new)

            # A trigger deleted the data
            if new == None:
                continue
            
            # Foreign key adjust
            newf = tofks(new)
            
            # Nullable checks
            newn = tonullables(list(zip(self.fields, newf)))

            # Use existing data, if any
            for k,v in _data_assign.items():
                newn[k] = _existing_data[n - 1][v]

            # Check primary key
            newk = tokeys(list(zip(self.fields, newn)))

            # If the key is already present, try again
            if newk in self.keys:
                if self._debug: print('KEY ALREADY PRESENT')
                continue
            
            # If a unique field/set of fields already exists,
            #   discard the generated values
            if check_single_uniques(newn):
                continue
            if check_compound_uniques(newn):
                continue

            # The data is ok.
            
            # Apply post triggers. Should not edit primary or foreign keys.
            for t in self.post_triggers:
                newn = t(newn)

            # A trigger deleted the data
            if newn == None:
                continue

            # Store the values
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
    def fromData(name, fields, data, assign, fks: list = [], uniques: list = [], cascadenulls: list = [], post_triggers: list = [], pre_triggers: list = [], debug = False):
        tbl = Table(name, fields, fks=fks, uniques=uniques, cascadenulls=cascadenulls, post_triggers=post_triggers, pre_triggers=pre_triggers, debug=debug)

        tbl.gen_n(len(data), data, assign)
        
        return tbl
        
# Edits and returns the record. Used in triggers
def editdata(data: list, index: int, value):
    data[index] = value
    return data
