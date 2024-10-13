# Django version of ACAS


## Installation
Currently requires starting an ACAS stack, mainly to get the database up and running with the acas db user.

```bash
python3 -m venv venv
source venv/bin/activate
pip install django psycopg2 django-concurrency
```

Roo automatically creates the objects we are staring with so skip the first migration and apply the rest.
```
python manage.py migrate acas 0001 --fake
python manage.py migrate
```


