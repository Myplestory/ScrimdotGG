import requests
import json

# authorizes/creates puuid client
def authpuuid(jsonargs):
    url = 'http://127.0.0.1:8000/login/login/'
    try:
      response = requests.post(url, json=jsonargs)
      if response.status_code == 200:
            data = response.json()
            return data
      else:
            return {"error": "Request failed", "status_code": response.status_code}
    except Exception as e:
        # Handle any exceptions that occur during the request
        return {"error": str(e)}