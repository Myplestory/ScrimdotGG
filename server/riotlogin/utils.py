# from secrets                import token_urlsafe
# from httpx                  import Client
# from dataclasses            import dataclass
# from time                   import time
# import requests
# import re



# # Create your views here.
# class Version:
#     def __init__(self):
#         self.versions = requests.get("https://valorant-api.com/v1/version").json()["data"]
#         self.valorant = self.valorant()
#         self.riot = self.riot()
#         self.sdk = self.sdk()

#     def riot(self):
#         return self.versions["riotClientBuild"]
#     def sdk(self):
#         return sdk if (sdk := self.versions["riotClientVersion"].split(".")[1]) else "23.8.0.1382"
#     def valorant(self):
#         return self.versions["riotClientVersion"]

# class Authobj:
#     def __init__(self,username,password):
#         self.version = Version()
#         app = "rso-auth"
#         print("self vars set up")
#         self.session = Client()
#         self.session.headers.update({
#                 "User-Agent": f'RiotClient/{self.version.riot} {app} (Windows;10;;Professional, x64)',
#                 "Cache-Control": "no-cache",
#                 "Accept": "application/json",
#                 "Content-Type": "application/json"
#         })
#         self.session.cookies.update({"tdid": "", "asid": "", "did": "", "clid": ""})

#         data = {
#                     "clientId": "riot-client",
#                     "language": "",
#                     "platform": "windows",
#                     "remember": False,
#                     "riot_identity": {
#                         "language": "it_IT",
#                         "state": "auth",
#                     },
#                     "sdkVersion": self.version.sdk,
#                     "type": "auth",
#                 }
#         r = self.session.post("https://authenticate.riotgames.com/api/v1/login",json=data)
#         data = r.json()

#         sitekey = data["captcha"]["hcaptcha"]["key"]
#         rqdata = data["captcha"]["hcaptcha"]["data"]
#         print("solving captcha with:", sitekey, rqdata)
#         capmonster = capmonster_python.HCaptchaTask("c100d7556f76bb9164f27421666087a2") # api key
#         capmonster.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
#         task_id = capmonster.create_task(website_url="https://auth.riotgames.com", website_key=sitekey, custom_data=rqdata)
#         result = capmonster.join_task_result(task_id)
#         code = result.get("gRecaptchaResponse")
#         data = {
#                     "riot_identity": {
#                         "captcha": f"hcaptcha {code}",
#                         "language": "en_GB",
#                         "password": password,
#                         "remember": False,
#                         "username": username
#                     },
#                     "type": "auth"
#                 }
#         r = self.session.put("https://authenticate.riotgames.com/api/v1/login", json=data)
#         data = r.json()
#         print(data)
#         if "error" in data:
#             print("ERROR")
#         else:
#             login_token = data['success']["login_token"]
#             data = {
#                         "authentication_type": "RiotAuth",
#                         "code_verifier": "",
#                         "login_token": login_token,
#                         "persist_login": False
#                     }
#             url = "https://auth.riotgames.com/api/v1/login-token"
#             self.session.post(url, json=data)
#             data = {
#                     "client_id": "riot-client",
#                     "nonce": token_urlsafe(16),
#                     "redirect_uri": "http://localhost/redirect",
#                     "response_type": "token id_token",
#                     "scope": "account openid",
#                 }
#             url = "https://auth.riotgames.com/api/v1/authorization"
#             r = self.session.post(url, json=data)
#             self.cookies = dict(r.cookies)
#             data = r.json()
#             uri = data["response"]["parameters"]["uri"]
#             self.access_token = uri.split("access_token=")[1].split("&scope")[0]
#             self.token_id = uri.split("id_token=")[1].split("&")[0]
#             self.expires_in = uri.split("expires_in=")[1].split("&")[0]
#             data = {
#                 "id_token" : self.token_id
#             }
#             headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.access_token}'}
#             r = self.session.put("https://riot-geo.pas.si.riotgames.com/pas/v1/product/valorant",json=data,headers=headers)
#             data = r.json()
#             self.Region = data['affinities']['live']

#             self.session.headers.update({"User-Agent": f'RiotClient/{self.version.riot} {app} (Windows;10;;Professional, x64)','Authorization': f'Bearer {self.access_token}',})
#             r = self.session.get(url="https://email-verification.riotgames.com/api/v1/account/status")
#             data = r.json()
#             self.Emailverifed = data["emailVerified"]
#             r = self.session.post("https://entitlements.auth.riotgames.com/api/token/v1")
#             data = r.json()
#             self.entitlement_token =  data['entitlements_token']
            