from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from random import randint
import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
bcrypt = Bcrypt(app)

app.config['JWT_SECRET_KEY'] = 's2codetaem-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
jwt = JWTManager(app)

# Giả lập DB
users_db = {}
orders_db = {}
otp_store = {}
products = [
    {"id": 1, "name": "ChatGPT API 100K", "desc": "API Key giá rẻ", "price": 100000},
    {"id": 2, "name": "Proxy VIP 50K", "desc": "Tốc độ cao", "price": 50000}
]

EMAIL_SENDER = "trinhsata9@gmail.com"
EMAIL_PASSWORD = "azyt peyk ydjf tbqk"

def send_email_gmail(to_email, otp_code):
    subject = "Mã OTP - S2 Code Shop"
    body = f"Mã xác minh của bạn là: {otp_code}"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
    except Exception as e:
        print(f"[LỖI GỬI MAIL] {e}")

@app.route("/")
def home():
    return jsonify({"message": "S2 Code Shop API is running"})

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Thiếu thông tin"}), 400
    if email in users_db:
        return jsonify({"error": "Email đã tồn tại"}), 400
    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    users_db[email] = {"password_hash": pw_hash, "api_key": "", "balance": 100000}
    orders_db[email] = []
    return jsonify({"success": True, "message": "Đăng ký thành công"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    user = users_db.get(email)
    if not user or not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Sai thông tin"}), 401
    token = create_access_token(identity=email)
    return jsonify({"success": True, "token": token})

@app.route("/api/profile", methods=["GET"])
@jwt_required()
def profile():
    email = get_jwt_identity()
    user = users_db.get(email)
    return jsonify({
        "email": email,
        "balance": user["balance"],
        "api_key": user["api_key"]
    })

@app.route("/api/update-api-key", methods=["POST"])
@jwt_required()
def update_api_key():
    email = get_jwt_identity()
    data = request.get_json()
    users_db[email]["api_key"] = data.get("api_key", "")
    return jsonify({"success": True, "message": "Đã cập nhật API Key"})

@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get("email")
    if email not in users_db:
        return jsonify({"error": "Email không tồn tại"}), 404
    otp = str(randint(100000, 999999))
    otp_store[email] = otp
    send_email_gmail(email, otp)
    return jsonify({"success": True, "message": "Mã xác minh đã gửi về email của bạn!"})

@app.route("/api/reset", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")
    new_pw = data.get("new_password")
    if otp_store.get(email) != otp:
        return jsonify({"error": "Mã xác minh không đúng"}), 400
    pw_hash = bcrypt.generate_password_hash(new_pw).decode("utf-8")
    users_db[email]["password_hash"] = pw_hash
    otp_store.pop(email, None)
    return jsonify({"success": True, "message": "Đã cập nhật mật khẩu"})

@app.route("/api/products", methods=["GET"])
def list_products():
    return jsonify(products)

@app.route("/api/orders", methods=["GET"])
@jwt_required()
def list_orders():
    email = get_jwt_identity()
    return jsonify(orders_db.get(email, []))

@app.route("/api/order", methods=["POST"])
@jwt_required()
def place_order():
    email = get_jwt_identity()
    data = request.get_json()
    pid = data.get("product_id")
    product = next((p for p in products if p["id"] == pid), None)
    if not product:
        return jsonify({"error": "Sản phẩm không tồn tại"}), 404
    if users_db[email]["balance"] < product["price"]:
        return jsonify({"error": "Không đủ số dư"}), 400
    users_db[email]["balance"] -= product["price"]
    orders_db[email].append(product)
    return jsonify({"success": True, "message": "Đặt hàng thành công"})

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/index")
def index_page():
    return render_template("index.html")

@app.route("/forgot")
def forgot_page():
    return render_template("forgot.html")

@app.route("/verify-otp")
def verify_otp_page():
    return render_template("verify-otp.html")

@app.route("/orders")
def orders_page():
    return render_template("orders.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

