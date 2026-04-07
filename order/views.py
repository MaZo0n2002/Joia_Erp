from decimal import Decimal

from django.shortcuts import get_object_or_404, render, redirect
from urllib3 import request

from customers.models import Customer
from inventory.models import Stock
from products.models import Product
from .models import Quotation, QuotationLine
from .forms import QuotationForm
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import Max, Sum
from django.db import transaction
from Sales_Order.models import SalesOrder, SalesOrderLine, Reservation
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect
from customers.models import Customer
from inventory.models import Stock
from products.models import Product
from .models import Quotation, QuotationLine
from Sales_Order.models import Reservation


@transaction.atomic
def create_quotation(request):

    customers = Customer.objects.all()

    incoming_stock = (
        Stock.objects
        .filter(status="incoming")
        .values("joia_code")
        .distinct()
    )

    if request.method == "POST":

        form = QuotationForm(request.POST)

        if form.is_valid():

            quotation = form.save(commit=False)
            quotation.notes = request.POST.get("notes", "")
            quotation.save()

            joia_codes = request.POST.getlist("joia_code[]")
            colors = request.POST.getlist("color[]")
            rolls = request.POST.getlist("rolls[]")
            qtys = request.POST.getlist("qty_m[]")
            prices = request.POST.getlist("unit_price[]")

            for joia, color, roll, qty, price in zip(
                joia_codes, colors, rolls, qtys, prices
            ):

                if not joia.strip():
                    continue

                qty = Decimal(str(qty or 0))
                price = Decimal(str(price or 0))

                # =====================================
                # 🔥 GET STOCK + PRODUCT (REAL FIX)
                # =====================================
                stocks = Stock.objects.filter(
                    joia_code=joia,
                    color_name=color,
                    status="incoming"
                ).select_related("product").order_by("id")

                if not stocks.exists():
                    raise ValueError(f"❌ No stock found for {joia} - {color}")

                # ✅ ناخد أول product من stock
                first_stock = stocks.first()

                if not first_stock.product:
                    raise ValueError(f"❌ Stock exists but no product linked for {joia}")

                product = first_stock.product

                # =====================================
                # ✅ CREATE QUOTATION LINE
                # =====================================
                line = QuotationLine.objects.create(
                    quotation=quotation,
                    product=product,
                    joia_code=joia,
                    color_name=color,
                    rolls=int(roll or 0),
                    qty_m=qty,
                    unit_price=price,
                )

                # =====================================
                # 🔥 RESERVATION ENGINE
                # =====================================
                remaining = qty

                for s in stocks:

                    if remaining <= 0:
                        break

                    if not s.product:
                        continue  # skip invalid stock

                    stock_qty = Decimal(str(s.qty_m))
                    take = min(stock_qty, remaining)

                    Reservation.objects.create(
                        product=s.product,
                        stock=s,
                        color=color,
                        quantity=float(take),
                        quotation_line=line,
                        status="reserved"
                    )

                    remaining -= take

                # =====================================
                # 🔥 BACKORDER
                # =====================================
                if remaining > 0:
                    Reservation.objects.create(
                        product=None,
                        stock=None,
                        color=color,
                        quantity=float(remaining),
                        quotation_line=line,
                        status="backorder"
                    )

            return redirect("generate_pdf", quotation_id=quotation.id)

    else:
        form = QuotationForm()

    return render(request, "dashboard/quotation.html", {
        "form": form,
        "customers": customers,
        "incoming_stock": incoming_stock,
    })
# ===============================
# PDF
# ===============================
def generate_pdf(request, quotation_id):

    quotation = Quotation.objects.get(id=quotation_id)

    template = get_template("pdf/quotation_pdf.html")

    html = template.render({
        "quotation": quotation
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="quotation_{quotation.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF ❌")

    return response


# ===============================
# AJAX COLORS
# ===============================
# def get_product_info(request):

#     joia_code = request.GET.get("joia_code")

#     stocks = (
#         Stock.objects
#         .filter(joia_code=joia_code, status="actual")
#         .values("color_name")
#         .annotate(
#             total_qty=Sum("qty_m"),
#             price=Max("product__selling_price")  # ✅ CORRECT  # ✅ IMPORTANT
#         )
#     )

#     data = list(stocks)

#     return JsonResponse(data, safe=False)


def manage_quotations(request):

    quotations = Quotation.objects.all().order_by("-created_at")

    return render(request, "dashboard/manage_quotations.html", {
        "quotations": quotations
    })


@transaction.atomic
def confirm_quotation(request, quotation_id):

    quotation = get_object_or_404(Quotation, id=quotation_id)

    # لو already confirmed
    if hasattr(quotation, 'sales_order'):
        return redirect('sales_order_detail', quotation.sales_order.id)

    # إنشاء Sales Order
    order = SalesOrder.objects.create(
        customer=quotation.customer,
        quotation=quotation,
        status='confirmed'
    )

    # =====================================
    # 🔥 LOOP ON QUOTATION LINES
    # =====================================
    for q_line in quotation.lines.all():

        # ناخد reserved بس (مش backorder)
        reservations = Reservation.objects.filter(
            quotation_line=q_line,
            status="reserved"
        )

        # =====================================
        # 🔥 PRODUCT RESOLUTION ENGINE
        # =====================================
        product = None

        # 1️⃣ من quotation line
        if q_line.product:
            product = q_line.product

        # 2️⃣ من reservations (أول واحد فيه product)
        if not product:
            res = reservations.filter(product__isnull=False).first()
            if res:
                product = res.product

        # 3️⃣ fallback من stock (آخر أمل)
        if not product:
            stock = Stock.objects.filter(
                joia_code=q_line.joia_code,
                color_name=q_line.color_name,
                product__isnull=False
            ).select_related("product").first()

            if stock:
                product = stock.product

        # ❌ منع الكارثة
        if not product:
            raise ValueError(
                f"❌ CRITICAL: No product found for joia={q_line.joia_code}, color={q_line.color_name}"
            )

        # =====================================
        # ✅ CREATE SALES ORDER LINE
        # =====================================
        line = SalesOrderLine.objects.create(
            order=order,
            product=product,
            color=q_line.color_name,
            requested_qty=float(q_line.qty_m),
            delivered_qty=0
        )

        # =====================================
        # 🔗 LINK RESERVATIONS (بس اللي فيها product)
        # =====================================
        total_reserved = 0

        for r in reservations:

            if not r.product:
                continue  # تجاهل أي reservation بايظ

            r.order_line = line
            r.save()

            total_reserved += r.quantity

        # =====================================
        # 📊 STATUS LOGIC
        # =====================================
        requested = float(q_line.qty_m)

        if total_reserved >= requested:
            line.status = 'ready'
        elif total_reserved > 0:
            line.status = 'partial'
        else:
            line.status = 'waiting'

        line.save()

    return redirect('sales_order_detail', order.id)

def quotation_api(request, quotation_id):

    quotation = get_object_or_404(Quotation, id=quotation_id)

    data = {
        "id": quotation.id,
        "customer": quotation.customer.name,
        "date": quotation.created_at.strftime("%Y-%m-%d %H:%M"),
        "notes": quotation.notes or "",
        "lines": []
    }

    for line in quotation.lines.all():
        data["lines"].append({
            "id": line.id,
            "product": line.style_number if hasattr(line, 'style_number') else line.joia_code,
            "color": line.color_name,
            "rolls": line.rolls,
            "qty": line.qty_m,
            "price": line.unit_price,
        })

    return JsonResponse(data)


@csrf_exempt
@transaction.atomic
def update_quotation(request, quotation_id):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body)
    lines = data.get("lines", [])
    notes = data.get("notes", "")

    quotation = Quotation.objects.get(id=quotation_id)
    quotation.notes = notes
    quotation.save()

    for item in lines:

        line = QuotationLine.objects.get(id=item["id"])

        new_qty = Decimal(str(item["qty"]))
        old_qty = Decimal(str(line.qty_m))

        diff = new_qty - old_qty

        joia = line.joia_code
        color = line.color_name

        # =====================================
        # 🔥 INCREASE (reserve more)
        # =====================================
        if diff > 0:

            remaining = diff

            stocks = Stock.objects.filter(
                joia_code=joia,
                color_name=color,
                status="incoming"
            ).order_by("id")

            for stock in stocks:

                if remaining <= 0:
                    break

                stock_qty = Decimal(str(stock.qty_m))
                take = min(stock_qty, remaining)

                Reservation.objects.create(
                    stock=stock,   # ✅ مهم جدا
                    product=stock.product,
                    color=color,
                    quantity=take,
                    quotation_line=line,
                    status="reserved"
                )

                remaining -= take

            # 🔥 BACKORDER
            if remaining > 0:
                Reservation.objects.create(
                    stock=None,
                    product=None,
                    color=color,
                    quantity=float(remaining),
                    quotation_line=line,
                    status="backorder"
                )

        # =====================================
        # 🔥 DECREASE (release stock)
        # =====================================
        elif diff < 0:

            to_remove = abs(diff)

            # 1️⃣ remove backorders first
            backorders = Reservation.objects.filter(
                quotation_line=line,
                status="backorder"
            )

            for b in backorders:

                if to_remove <= 0:
                    break

                b_qty = Decimal(str(b.quantity))
                take = min(b_qty, to_remove)

                new_qty_b = b_qty - take

                if new_qty_b == 0:
                    b.delete()
                else:
                    b.quantity = float(new_qty_b)
                    b.save()

                to_remove -= take

            # 2️⃣ remove reserved
            reservations = Reservation.objects.filter(
                quotation_line=line,
                status="reserved"
            ).order_by("-id")

            for r in reservations:

                if to_remove <= 0:
                    break

                r_qty = Decimal(str(r.quantity))
                take = min(r_qty, to_remove)

                new_qty_r = r_qty - take

                if new_qty_r == 0:
                    r.delete()
                else:
                    r.quantity = float(new_qty_r)
                    r.save()

                to_remove -= take

        # =====================================
        # 🔥 UPDATE LINE (OUTSIDE CONDITIONS)
        # =====================================
        line.qty_m = new_qty
        line.save()

    return JsonResponse({"status": "success"})



def get_colors(request):
    joia_code = request.GET.get("joia_code")

    product = Product.objects.filter(joia_code=joia_code).first()
    price = float(product.selling_price) if product else 0

    stocks = (
        Stock.objects
        .filter(
            joia_code=joia_code,
            status="incoming",
            color_name__isnull=False
        )
        .exclude(color_name="")
    )

    grouped = {}

    for s in stocks:

        color = s.color_name
        unit = (s.unit or "m").lower()

        # 🔥 KEY FIX: group by color + unit
        key = f"{color}_{unit}"

        if unit == "kg":
            qty = float(s.qty_kg or 0)
        else:
            qty = float(s.qty_m or 0)

        if key not in grouped:
            grouped[key] = {
                "color_name": color,
                "total_qty": 0,
                "unit": unit,
                "price": price
            }

        grouped[key]["total_qty"] += qty

    return JsonResponse(list(grouped.values()), safe=False)