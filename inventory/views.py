from django.shortcuts import render, redirect
from django.db.models import Sum
from decimal import Decimal

from .models import Stock
from Sales_Order.models import Reservation


def stock(request):

    # =======================
    # ACTUAL STOCK
    # =======================
    actual_stock = (
        Stock.objects
        .select_related("dpl", "product")
        .filter(status="actual")
    )

    # =======================
    # INCOMING STOCK
    # =======================
    raw_incoming = (
        Stock.objects
        .select_related("dpl", "product")
        .filter(status="incoming")
    )

    incoming_stock = []

    for s in raw_incoming:

        # 🔥 احسب reserved من reservations
        reserved_qty = (
            Reservation.objects.filter(
                stock=s,
                status="reserved"
            ).aggregate(total=Sum("quantity"))["total"] or 0
        )

        reserved_qty = Decimal(str(reserved_qty))

        # ✅ أهم fix هنا
        if s.product and s.product.unit == "kg":
            total_qty = Decimal(str(s.qty_kg))
        else:
            total_qty = Decimal(str(s.qty_m))

        available = total_qty - reserved_qty

        incoming_stock.append({
            "obj": s,
            "available": float(available),
        })

    # =======================
    # RESERVED STOCK
    # =======================
    reserved_stock = (
        Reservation.objects
        .select_related("quotation_line__quotation__customer")
        .values(
            "quotation_line__quotation__customer__name",
            "quotation_line__quotation__quotation_number",
            "quotation_line__joia_code",
            "quotation_line__color_name",
            "status"
        )
        .annotate(total_qty=Sum("quantity"))
        .order_by("-quotation_line__quotation__id")
    )

    return render(request, "inventory/stock.html", {
        "actual_stock": actual_stock,
        "incoming_stock": incoming_stock,
        "reserved_stock": reserved_stock,
    })


# ===============================
# 🔥 TRANSFER DPL
# ===============================
def transfer_dpl_stock(request):
    if request.method == "POST":
        dpl_id = request.POST.get("dpl_id")

        Stock.objects.filter(
            dpl_id=dpl_id,
            status="incoming"
        ).update(status="actual")

    return redirect('stock')