# EzStego

- Đầu tiên ta sử dụng ***pdftotext*** để chuyển pdf về dạng text, ta thấy file pdf này đều là các kí tự S, T, L dạng như sau:

![alt text](image.png)

- Mình suy đoán đây là whitespaces language với:

    ○ S --> Space

    ○ T --> Tab

    ○ L --> Line Feed

- Đầu tiên, ta sẽ chuyển file pdf này từ dạng text về dạng *whitespace* và ghi ra 1 file bất kỳ (```program.ws```):

```python
with open("input.txt", "r", encoding="utf-8") as f:
    data = f.read()
ws = (
    data
    .replace("S", " ")
    .replace("T", "\t")
    .replace("L", "\n")
)
with open("program.ws", "w", encoding="utf-8") as f:
    f.write(ws)
```

- Sau khi có được file ```program.ws```, ta chạy file .ws đó:

![alt text](image-1.png)

    ○ Ta sẽ nhận được 1 chuỗi hex như trên

    ○ Thử decode hex về bytes:

![alt text](image-2.png)

--> Byte string không đọc được 

--> Có mã hóa tiếp

- Do bài có mô tả là ta sẽ lấy được flag thông qua các thông tin có trong pdf này, mình sẽ thử phân tích file pdf này

Chạy ```pdfdetach -list``` để xem các file được nhúng trong file pdf này:

![alt text](image-3.png)

--> Ta có 2 file khả nghi, xem thử 2 file này:

![alt text](image-4.png)

- File thứ 2 *you_cannot_read_this.txt* khá khả nghi, suy đoán nó có thể là encrypt key, ta decode bằng đoạn text này:

![alt text](image-5.png)