### To get started first install Okta Python SDK
```
python3 -m pip install okta
```

### Go to Okta Admin Console and add an API Token
https://support.okta.com/help/s/article/How-do-I-create-an-API-token?language=en_US

### Grab the TOTP Factor Authenticator ID
It can be found in Okta's `Security/Authenticators`, find `TOKEN2` and click Actions
and go to `Authenticator ID & Info`. Copy Authenticator ID

Edit the JSON File based on your credentials
```
{
    "org_url": "https://company-name.oktapreview.com/",
    "token": "your-api-token-here",
    "factor_profile_id": "factor-auwthenticator-id-here"
}
```

Run the command:
```
python3 setup_totp.py
```

**NOTE: You need to install TOKEN2 NFC BURNER App on your phone in order to be able to complete the TOTP factor setup**
