# Mocker
Mock data generator for databases.

Allowed constraints definition
- Primary key (multiple fields)
- Foreign keys (multiple fields, with options)
- Unique constraints
- Triggers

## Data definition
As of now, Mocker supports numbers (only integers), strings, booleans, dates and a couple custom enums I made for my project (marks and days). All the data definition is index-based, the code has no knowledge whatsoever of the field names.

Example data definition
```python
corsi = Table('Corsi',
              [
                  STR(r'[A-Z\-]{5,8}', key=True),
                  STR(r'[a-z \,]{20,100}', notnull=True),
                  STR(r'[a-z ,]{5,30}', notnull=True),
                  INT(1, 3, notnull=True),
              ])
corsi.tofile(20)
```
This snippet defines a table (`'Corsi'`) and writes to a file 20 random generated instances, keeping them in memory for a possible future usage (like a foreign key pointing to the table)

### Data types
A definition of the data types available. All the types share some optional attributes 
| Attribute | Usage                       |
|-----------|-----------------------------|
| `key`     | Sets the primary key fields |
| `notnull` | Like sql's counterpart      |
| `unique`  | Like sql's counterpart      |

> Note: each nullable field has a 10% of being null

#### INT
Generates an integer.

**Required parameters:**
- `min`: the minimum number that can be generated (inclusive)
- `max`: the maximum number that can be generated (inclusive)

**Optional parameters:**
- `step`: The step between the generated values

Example
```python
INT(30, 180, step=30)
```
#### STR
Generates a string based on a given regex

Strings are generated from the regex using [exrex](https://github.com/asciimoo/exrex)

Example
```python
STR(r'segretario|tecnico|[a-z]{5,10}', notnull=True)
```
#### BOOL
Generates a boolean

Example
```python
BOOL(notnull=True)
```
#### DATE
Generates a random date between a minimum and a maximum.

Date parameters are srings in ISO format (yyyy-MM-dd)

Example:
```python
DATE('2012-01-01','2022-05-14',notnull=True)
```
### Table definition
Each table must have 
- A name
- A list of fields

> At least one key field is required (the program won't throw an error, but it will cycle endlessly)

Additionally, there are many optional parameters to allow for a better data generation
- `fks`: a list of the foreign keys
- `uniques`: a list of unique groups. Single field uniques can be set directly on the field
- `cascadenulls`: useful when a group of fields should be either all set or all null (example: an address)
- `pre_triggers`/`post_triggers`: triggers executed at the start or at the very end of the procedure.

Example:
```python
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
```
#### Foreign keys
`fks` is a list containing all the foreign keys.

A single foreign key is represented with a tuple of 4 elements:
1. The table referenced
2. A list with the local indexes
3. A list with the foreign indexes
4. Options

The structure is pretty similar to how sql defines its foreign keys, but it's using indexes instead of field names. Except for -
##### Options
A special mention is needed. This field is set to only chose a foreign key reference if all its elements evaluate to `True`.

Example:
```python
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
```
This example only selects buildings _(edificio)_ where the number of floors _(piano)_ is greater than the floor where this room _(stanza)_ is located.

A similar result would be obtained by using a `post_trigger` and changing the floor value to a random number below the number of floors of the building, but this approach keeps the generation logic away from the data definition.
#### Triggers
Allows changing the generated data

> Note: Post triggers **should not edit primary/foreign keys**

Examples:
```python
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
```
#### Table from already generated data
Sometimes it's useful to generate a table from data already available, like in case of specializations. An additional parameter is needed for the assignment. It's a dictionary of self index to remote index
> Note: for now, only simple completion is allowed for new generated fields (like Aule's third field in the example)
Example:
```python
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

uffici = Table.fromData('Uffici',
                        [
                            STR(r'[1-7]\d?', key=True),
                            STR('[A-Z]{4}', key=True),
                        ],
                        uff,
                        { 0: 0, 1: 3 })
uffici.tofile(-1)

aule = Table.fromData('Aule',
                      [
                          STR(r'[A-G][1-7]\d?', key=True),
                          STR('[A-Z]{4}', key=True),
                          INT(30, 500)
                      ],
                      au,
                      { 0: 0, 1: 3 })
aule.tofile(-1)
```
> Note: `tofile` still wants a number, but it's not used. I set it to -1 for the human readers to make it obvious for them.
## How this project was born
Had to populate a database for a university project but couldn't stand Mockeroo's RegEx syntax, so I decided to make my own version in a couple days

Made with ❤️ in Emacs
