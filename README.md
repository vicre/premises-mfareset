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
```


## Dokumentation
1. En IT personale bruger logger ind via MSAL authentikation.  
2. Under authentiaktion tjekkes der om Azure brugeren er synched med en Active Directory konti.
3. Herefter tjekkes der om IT-personale-brugeren er medlem af en af de grupper som giver rettighed til at nulstille en målgruppe's MFA. f.eks. hvis du er medlem af "CN=AIT,OU=MFAResetAdmins,OU=Groups,OU=SOC,OU=CIS,OU=AIT,DC=win,DC=dtu,DC=dk" kan du nulstille DTUBaseUsers/AIT. Fordi extendedAtribbutes1 har værdien AIT
