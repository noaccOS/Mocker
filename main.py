import random
import re

from mock import INT, STR, DATE, BOOL, GIORNO, VOTO, Table, editdata

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
               # Edificio.piani > stanza.piano
               fks=[(edifici, [1,2,3], [0,1,2], [lambda edificio, stanza: edificio[3] > stanza[4]])])
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
                uniques=[[6,7]],
                post_triggers=[
                    # If a student with the same CF exists, the name and surname must be the same
                    lambda doc: doc if (stu := next((s for s in studenti.generated if s[1] == doc[1]), None)) is None else editdata(editdata(doc, 2, stu[2]), 3, stu[3])
                ])
docenti.tofile(300)

ric = docenti.generated[:100]
oras = docenti.generated[100:]
ordi = oras[:100]
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
                                fks=[(stanze, [7, 8], [0, 3], [])],
                                post_triggers=[
                                    # Same as for docenti, but for both docenti and studenti
                                    lambda pa: pa if (stu := next((s for s in studenti.generated if s[1] == pa[1]), None)) is None else editdata(editdata(pa, 2, stu[2]), 3, stu[3]),
                                    lambda pa: pa if (doc := next((d for d in docenti .generated if d[1] == pa[1]), None)) is None else editdata(editdata(pa, 2, doc[2]), 3, doc[3])
                                ])
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

# Helper function for edizioni corsi trigger
def toints(lst: list):
    return [1 if x == 'true' else 0 for x in lst]

# Edizioni Corsi
edizionicorsi = Table('EdizioniCorsi',
                      [
                          STR(r'[A-Z\-]{5,8}', key=True),
                          INT(2011, 2022, key=True),
                          BOOL(notnull=True),
                          BOOL(notnull=True),
                          BOOL(notnull=True),
                          INT(1, 4, notnull=True)
                      ],
                      fks=[(corsi, [0], [0], [ lambda corso, edizione: corso[3] == str(sum(toints(edizione[2:5])))])],
                      # if all Qn are false, change one of them to true
                      pre_triggers=[(lambda ed: ed if ed[2] == 'true' or ed[3] == 'true' or ed[4] == 'true' else editdata(ed, random.randint(2,4), 'true'))])
edizionicorsi.tofile(150)

# Lezioni
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
