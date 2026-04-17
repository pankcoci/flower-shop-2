from functools import wraps
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "secret123"

# -----------------------
# ДАННЫЕ
# -----------------------
# Картинки кладите в папку static/images/ и укажите путь от static, например:
# "image": "images/moya_roza.jpg"
# Поле image должно совпадать с реальным именем файла на диске.

products = [
    {
        "id": 1,
        "name": "Роза",
        "price": 250,
        "desc": "Красная роза",
        "color": "#ffcccc",
        "image": "images/rose.svg",
    },
    {
        "id": 2,
        "name": "Тюльпан",
        "price": 180,
        "desc": "Жёлтый тюльпан",
        "color": "#ffffcc",
        "image": "images/tulip.svg",
    },
    {
        "id": 3,
        "name": "Лилия",
        "price": 300,
        "desc": "Белая лилия",
        "color": "#e6e6fa",
        "image": "images/lily.svg",
    },
]

users = {
    "admin": "admin",
}


# -----------------------
# ДЕКОРАТОР ЛОГИНА
# -----------------------


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Сначала войдите в систему", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapper


# -----------------------
# ШАБЛОНЫ: пользователь и корзина
# -----------------------


def _asset_version(static_filename):
    """Версия по времени файла — браузер заново загрузит картинку после замены."""
    if not static_filename:
        return "0"
    parts = static_filename.replace("\\", "/").split("/")
    full = os.path.join(app.root_path, "static", *parts)
    try:
        return str(int(os.path.getmtime(full)))
    except OSError:
        return "0"


@app.context_processor
def inject_globals():
    cart = session.get("cart") or {}
    try:
        cart_count = sum(int(q) for q in cart.values())
    except (TypeError, ValueError):
        cart_count = 0
    return dict(
        current_user=session.get("user"),
        cart_count=cart_count,
        asset_version=_asset_version,
    )


# -----------------------
# РОУТЫ
# -----------------------


@app.route("/")
def index():
    return render_template("index.html", products=products)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if users.get(username) == password:
            session["user"] = username
            flash("Добро пожаловать!", "success")
            return redirect(url_for("index"))
        flash("Неверный логин или пароль", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из аккаунта", "info")
    return redirect(url_for("index"))


@app.route("/account")
@login_required
def account():
    return render_template("account.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not username or not password:
            flash("Заполните логин и пароль", "danger")
        elif password != confirm:
            flash("Пароли не совпадают", "danger")
        elif username in users:
            flash("Такой логин уже занят", "warning")
        else:
            users[username] = password
            flash("Аккаунт создан. Войдите с этими данными.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------
# КОРЗИНА
# -----------------------


@app.route("/add_to_cart/<int:pid>")
@login_required
def add_to_cart(pid):
    cart = session.get("cart", {})
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    session["cart"] = cart
    session.modified = True
    flash("Товар добавлен в корзину", "success")
    return redirect(url_for("index"))


@app.route("/cart")
@login_required
def cart():
    raw = session.get("cart", {})
    items = []
    total = 0

    for pid, qty in raw.items():
        product = next((p for p in products if p["id"] == int(pid)), None)
        if product:
            item_sum = product["price"] * qty
            items.append({"product": product, "qty": qty, "sum": item_sum})
            total += item_sum

    return render_template("cart.html", items=items, total=total)


@app.route("/update_cart/<int:pid>", methods=["POST"])
@login_required
def update_cart(pid):
    action = request.form.get("action")
    cart = session.get("cart", {})

    if action == "increase":
        cart[str(pid)] = cart.get(str(pid), 0) + 1
    elif action == "decrease":
        if cart.get(str(pid), 0) > 1:
            cart[str(pid)] -= 1
        else:
            cart.pop(str(pid), None)
    elif action == "remove":
        cart.pop(str(pid), None)

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    session.pop("cart", None)
    session.modified = True
    flash("Заказ успешно оформлен!", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    _img_dir = os.path.join(app.root_path, "static", "images")
    print("\n>>> Картинки товаров кладите СЮДА (проверьте путь в проводнике):\n", os.path.abspath(_img_dir), "\n")
    app.run(debug=True)
