# Activate venv, run makemigrations, then migrate
& .\.venv\Scripts\Activate.ps1
python manage.py makemigrations
python manage.py migrate
