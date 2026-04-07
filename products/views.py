from itertools import product
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Count

from products.models import Product
from inventory.models import Stock
from Sales_Order.models import SalesOrderLine


# ================= PRODUCTS VIEW =================
def products_view(request):

    # ================= STOCK =================
    stocks = Stock.objects.values('joia_code', 'status', 'unit').annotate(
        total_m=Sum('qty_m'),
        total_kg=Sum('qty_kg'),
        rolls=Count('id')
    )

    stock_map = {}

    for s in stocks:
        code = s['joia_code']
        status = s['status']
        unit = (s['unit'] or "m").lower()

        if code not in stock_map:
            stock_map[code] = {
                "actual_m": 0,
                "reserved_m": 0,
                "actual_kg": 0,
                "reserved_kg": 0,
                "total_m": 0,
                "total_kg": 0,
                "rolls": 0,
                "unit": unit
            }

        # ✅ always update unit from stock
        stock_map[code]["unit"] = unit

        if status == "actual":
            stock_map[code]["actual_m"] += s["total_m"] or 0
            stock_map[code]["actual_kg"] += s["total_kg"] or 0

        elif status == "reserved":
            stock_map[code]["reserved_m"] += s["total_m"] or 0
            stock_map[code]["reserved_kg"] += s["total_kg"] or 0

        stock_map[code]["total_m"] += s["total_m"] or 0
        stock_map[code]["total_kg"] += s["total_kg"] or 0
        stock_map[code]["rolls"] += s["rolls"] or 0


    # ================= SALES =================
    sales_data = SalesOrderLine.objects.values('product__joia_code').annotate(
        sold_qty=Sum('delivered_qty')
    )

    sales_map = {
        s["product__joia_code"]: s["sold_qty"] or 0
        for s in sales_data
    }


    # ================= PRODUCTS =================
    products = Product.objects.filter(
        joia_code__in=stock_map.keys()
    ).prefetch_related("colors").order_by("joia_code")


    data = []
    total_inventory = 0

    for product in products:

        s = stock_map.get(product.joia_code, {})
        unit = s.get("unit", "m")

        total_m = s.get("total_m", 0)
        total_kg = s.get("total_kg", 0)

        actual_m = s.get("actual_m", 0)
        reserved_m = s.get("reserved_m", 0)

        actual_kg = s.get("actual_kg", 0)
        reserved_kg = s.get("reserved_kg", 0)

        rolls = s.get("rolls", 0)
        sold_qty = sales_map.get(product.joia_code, 0)

        # ✅ UNIT LOGIC (FROM STOCK)
        if unit == "kg":
            available = actual_kg - reserved_kg
            total_inventory += total_kg
        else:
            available = actual_m - reserved_m
            total_inventory += total_m
        
        margin = 0
        if product.costing_price:
          margin = ((product.selling_price - product.costing_price) / product.costing_price) * 100
        data.append({
            "product": product,
            "total_m": total_m,
            "total_kg": total_kg,
            "available": available,
            "colors": product.colors.all(),
            "rolls": rolls,
            "sold_qty": sold_qty,
            "unit": unit
        })

    low_stock = sum(1 for p in data if p["available"] < 300)

    return render(request, "dashboard/products.html", {
        "products": data,
        "total_inventory": total_inventory,
        "low_stock": low_stock
    })


# ================= UPDATE PRICE =================
def update_price(request):

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            product = get_object_or_404(Product, id=data["product_id"])
            value = float(data["value"])

            if data["field"] == "selling_price":
                product.selling_price = value

            elif data["field"] == "costing_price":
                product.costing_price = value

            else:
                return JsonResponse({"error": "Invalid field"}, status=400)

            product.save()

            return JsonResponse({
                "status": "success",
                "value": value
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)