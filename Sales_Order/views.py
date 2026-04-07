from decimal import Decimal
import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template

from xhtml2pdf import pisa

from inventory.models import Stock
from .models import Invoice, SalesOrder, SalesOrderLine


# ===============================
# 🔥 LIST VIEW
# ===============================
def sales_orders_list(request):

    orders = (
        SalesOrder.objects
        .select_related("customer", "quotation")
        .prefetch_related("lines")
        .order_by("-id")
    )

    return render(request, "sales_orders/list.html", {
        "orders": orders
    })


# ===============================
# 🔥 DETAILS VIEW
# ===============================
def sales_order_detail(request, order_id):

    order = get_object_or_404(
        SalesOrder.objects.select_related("customer", "quotation"),
        id=order_id
    )

    # ✅ Copy notes ONCE from quotation
    if not order.notes and order.quotation.notes:
        order.notes = order.quotation.notes
        order.save()

    lines = (
        SalesOrderLine.objects
        .filter(order=order)
        .select_related("product")
        .prefetch_related("reservations")
    )

    for line in lines:
        reserved = line.reservations.filter(
            status="reserved"
        ).aggregate(total=Sum("quantity"))["total"] or 0

        line.reserved_qty_calc = reserved

    return render(request, "sales_orders/detail.html", {
        "order": order,
        "lines": lines,
        "is_fully_delivered": order.is_fully_delivered
    })


# ===============================
# 🔥 DELIVER LINE
# ===============================
@csrf_exempt
def deliver_line(request, line_id):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid"}, status=400)

    data = json.loads(request.body)
    qty = float(data.get("qty", 0))

    line = get_object_or_404(SalesOrderLine, id=line_id)

    if qty <= 0:
        return JsonResponse({"error": "Invalid qty"})

    if qty > line.remaining_qty():
        return JsonResponse({"error": "Exceeds remaining"})

    remaining = qty

    stocks = Stock.objects.filter(
        product=line.product,
        color_name=line.color,
        status="actual"
    ).order_by("id")

    for stock in stocks:

        if remaining <= 0:
            break

        available = stock.qty_m
        take = min(available, remaining)

        stock.qty_m -= take
        stock.save()

        remaining -= take

    if remaining > 0:
        return JsonResponse({"error": "Not enough stock"})

    # ✅ update delivered quantity ONLY (no status dependency)
    line.delivered_qty += qty
    line.save()

    return JsonResponse({"status": "success"})


# ===============================
# 🔥 UPDATE UNIT PRICE
# ===============================
@csrf_exempt
def update_price(request, line_id):

    data = json.loads(request.body)
    line = get_object_or_404(SalesOrderLine, id=line_id)

    line.unit_price = Decimal(str(data.get("price", 0)))
    line.save()

    return JsonResponse({"status": "ok"})


# ===============================
# 🔥 UPDATE NOTES
# ===============================
@csrf_exempt
def update_notes(request, order_id):

    data = json.loads(request.body)
    order = get_object_or_404(SalesOrder, id=order_id)

    order.notes = data.get("notes")
    order.save()

    return JsonResponse({"status": "ok"})


# ===============================
# 🔥 CONFIRM ORDER → CREATE INVOICE
# ===============================
@transaction.atomic
def confirm_final_order(request, order_id):

    order = get_object_or_404(SalesOrder, id=order_id)

    if not order.is_fully_delivered:
        return JsonResponse({"error": "Order not fully delivered"})

    if hasattr(order, "invoice"):
        return JsonResponse({"error": "Invoice already exists"})

    total = Decimal("0")

    for line in order.lines.all():
        price = Decimal(str(line.unit_price or 0))
        qty = Decimal(str(line.delivered_qty or 0))

        total += qty * price

    invoice = Invoice.objects.create(
        customer=order.customer,
        sales_order=order,
        total=total,
        status="confirmed",
        notes=order.notes
    )

    order.status = "delivered"
    order.save()

    return JsonResponse({
        "status": "success",
        "redirect_url": f"/orders/invoice/pdf/{invoice.id}/"
    })


# ===============================
# 🔥 GENERATE INVOICE PDF
# ===============================
def generate_invoice_pdf(request, invoice_id):

    invoice = Invoice.objects.select_related(
        "customer", "sales_order"
    ).prefetch_related(
        "sales_order__lines__product"
    ).get(id=invoice_id)

    lines = invoice.sales_order.lines.all()

    subtotal = Decimal("0")

    for line in lines:
        price = Decimal(str(line.unit_price or 0))
        qty = Decimal(str(line.delivered_qty or 0))

        # ✅ Calculations
        line.line_total = qty * price

        # ✅ FIX missing fields
        line.unit = "m"
        line.rolls = 1

        subtotal += line.line_total

    vat = subtotal * Decimal("0.14")
    total = subtotal + vat

    template = get_template("pdf/invoice_pdf.html")

    html = template.render({
        "invoice": invoice,
        "lines": lines,
        "subtotal": subtotal,
        "vat": vat,
        "total": total
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response