from flask import render_template, request, flash, redirect, url_for
from app.events import bp
from app.events import services

@bp.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form.get("title", "")
        category = request.form.get("category", "")
        venue = request.form.get("venue", "")
        start_time = request.form.get("start_time", "")
        end_time = request.form.get("end_time", "")
        
        try:
            # Boş değer gelme ihtimaline karşı int dönüşümlerini güvenli yapıyoruz
            capacity_str = request.form.get("capacity")
            price_str = request.form.get("price")
            
            capacity = int(capacity_str) if capacity_str else None
            price = int(price_str) if price_str else None
            
            # Backend doğrulaması yapılıyor (Madde 6)
            services.validate_event_data(title, category, venue, start_time, end_time, capacity, price)
            
            # 8. Madde: Geçerli bilgiler girildiğinde gösterilecek özel başarı mesajı
            flash("Etkinlik bilgileri doğrulandı. Henüz kaydedilmedi.", "success")
        except ValueError as e:
            # 7. ve 9. Maddelerdeki hata mesajları
            flash(str(e), "error")
            
        return redirect(url_for("events.create"))

    return render_template("events/create.html")