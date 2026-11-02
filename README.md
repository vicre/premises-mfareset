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


#### Notes
prepare_auth_methods return all methods that this system is allowed to delete. e.g. not the password forexample

On a fresh Coolify instance, apply the existing migrations:
```bash
python manage.py migrate
```
Otherwise the app will not work

## Passkeys / FIDO2

MFA reset preserves passkeys by default. Select **Slet også passkeys /
FIDO2-sikkerhedsnøgler** to also delete all passkeys and FIDO2 security keys for
the selected user. The confirmation shows the target and scope. Password and
Windows Hello methods remain excluded, and existing AD group/OU authorization
still applies. The selected scope is recorded in the audit log.

## Automated tests

```bash
python manage.py test --settings=config.test_settings
```

These tests use fake credentials, an in-memory database, and simulated Graph/AD
responses. Outbound socket connections are blocked by the test runner. They do
not reset real accounts.
