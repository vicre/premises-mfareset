# MFA Reset done by IT personal 

Denne app giver en IT administratorer mulighed for at for at nulstille en afgrænset håndfuld brugere's multifactor.

## For udviklere

```bash
git clone https://github.com/vicre/premises-mfareset
cd premises-mfareset
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver