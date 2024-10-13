# Django version of ACAS


## Installation

1. Start normal acas stack
Checkout acas and docker-compose up -d

> Currently requires starting an ACAS stack, mainly to get the database up and running with the acas db user.

2. Install venv and dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install django psycopg2 django-concurrency pytest-django
```

3. Migrate to django

```
python manage.py migrate acas 0001 --fake
python manage.py migrate
```

4. Play around

- Pytests
You can run the pytests using vscode `Testing`
They should automatically populate and there should be a few tests for protocl creation
This is a good place to start and it doesn't actually commmit to the database so you can run it as many times as you want
- Seed protocols
I wrote a command to seed 1000 protocols and it can be run as a django command

```
python manage.py seed_protocols
```





## Notes on how this was setup

Using acas release-2024.4.x I startted up a local dev instance


```
python3 -m venv venv
source venv/bin/activate
pip install django
django-admin startproject acas
cd acas
```

Edit the settings.py DATABASES

```
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'acas',
        'USER': 'acas',
        'PASSWORD': 'acas',
        'HOST': 'localhost',
        'PORT': '5432'
```

Create a migration for the models

```
python manage.py inspectdb > models.py
```

Search and remove this in models.py (including new line at the end)
```
        managed = False
```

Add acas to the list of installed apps in settings.py
```
INSTALLED_APPS = [
	…
    'acas'
```

Create the initial migration and fake run it (since this was initially created by too)
```
python manage.py makemigrations
python manage.py migrate --fake
```


```
python manage.py runserver
```


I then began modifying the models to match roo's inheritance (AbstractThing, AbstractValue, Abstract...etc.)
I also added a module called django-concurrency to handle the version numbers of protocols
