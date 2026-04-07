import pandas as pd
import tempfile
import os

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import DPLForm
from inventory.models import Stock
from products.models import Color, Product


def dpl(request):

    preview_data = None

    if request.method == 'POST':
        form = DPLForm(request.POST, request.FILES)

        if form.is_valid():

            # ================= PREVIEW =================
            if 'preview' in request.POST:

                uploaded_file = request.FILES.get('uploaded_file')

                if not uploaded_file:
                    return render(request, 'dashboard/dpl.html', {
                        'form': form,
                        'error': 'Please select an Excel file ❌'
                    })

                temp_file = tempfile.NamedTemporaryFile(delete=False)

                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)

                temp_file.close()

                request.session['file_path'] = temp_file.name

                df = pd.read_excel(temp_file.name)
                df.columns = df.columns.str.strip()

                df.rename(columns={
                    "STYLE#": "style",
                    "Joia Code": "joia_code",
                    "COLOR#": "color_code",
                    "COLOR Name": "color_name",
                    "COLOR Na": "color_name",
                    "Showroom Col.": "showroom_color",
                    "LOT#": "lot",
                    "ROLL#": "roll",
                    "QTY(KGS)": "qty_kg",
                    "QTY(M)": "qty_m",
                    "Unit": "unit",
                    "Composition": "composition"
                }, inplace=True)

                preview_data = df.to_dict(orient='records')

            # ================= UPLOAD =================
            elif 'upload' in request.POST:

                uploaded_file = request.FILES.get('uploaded_file')

                if uploaded_file:
                    temp_file = tempfile.NamedTemporaryFile(delete=False)

                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)

                    temp_file.close()

                    file_path = temp_file.name
                else:
                    file_path = request.session.get('file_path')

                if not file_path:
                    return render(request, 'dashboard/dpl.html', {
                        'form': form,
                        'error': 'Please upload file ❌'
                    })

                df = pd.read_excel(file_path)
                df.columns = df.columns.str.strip()

                df.rename(columns={
                    "STYLE#": "style",
                    "Joia Code": "joia_code",
                    "COLOR#": "color_code",
                    "COLOR Name": "color_name",
                    "COLOR Na": "color_name",
                    "Showroom Col.": "showroom_color",
                    "LOT#": "lot",
                    "ROLL#": "roll",
                    "QTY(KGS)": "qty_kg",
                    "QTY(M)": "qty_m",
                    "Unit": "unit",
                    "Composition": "composition"
                }, inplace=True)

                dpl_record = form.save()
                
                for row in df.to_dict(orient='records'):
                    
                    unit = (row.get("unit") or "").strip().lower()

                    if not unit: unit = "kg" if row.get("qty_kg") else "m"
                    # 🔥 create product + composition
                    product, _ = Product.objects.get_or_create(
                        joia_code=row.get("joia_code"),
                        defaults={
                            "style_number": row.get("style"),
                            "composition": row.get("composition") or ""
                        }
                    )
               
                    # 🔥 update composition لو موجود
                    if row.get("composition"):
                        product.composition = row.get("composition")
                        product.save()
                    
                    Color.objects.get_or_create(
                         product=product,
                         color_name=row.get("color_name") or "unknown",
                         color_code=row.get("color_code") or "unknown"
                     )
                    Stock.objects.create(
                        dpl=dpl_record,
                        product=product,
                        style_number=row.get("style"),
                        joia_code=row.get("joia_code"),

                        color_code=row.get("color_code") or "unknown",
                        color_name=row.get("color_name") or "unknown",
                        showroom_color=row.get("showroom_color") or row.get("color_name"),

                        lot_number=row.get("lot") or 0,
                        roll_number=row.get("roll") or 0,
                        qty_kg=row.get("qty_kg") or 0,
                        qty_m=row.get("qty_m") or 0,
                        unit=unit,
                        status="incoming"
                    )

                if os.path.exists(file_path):
                    os.remove(file_path)

                request.session.pop('file_path', None)

                messages.success(request, "DPL uploaded successfully ✅")

                return redirect('stock')

    else:
        form = DPLForm()

    return render(request, 'dashboard/dpl.html', {
        'form': form,
        'preview_data': preview_data
    })