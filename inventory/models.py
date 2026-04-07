from django.db import models
from products.models import Product
from order.models import Quotation


class Stock(models.Model):

    # ✅ FIX (important جدًا)
    dpl = models.ForeignKey(
        'dpl.DPL',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stocks",
        null=True,
        blank=True
    )

    style_number = models.CharField(max_length=100, blank=True, null=True)
    joia_code = models.CharField(max_length=50)

    color_code = models.CharField(max_length=50, default="unknown")
    color_name = models.CharField(max_length=100, default="unknown")
    showroom_color = models.CharField(max_length=100, default="unknown")

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_stocks"
    )

    unit = models.CharField(
        max_length=10,
        choices=[
            ("m", "Meter"),
            ("kg", "Kilogram")
        ],
        default="m"
    )

    # ✅ FIXED fields
    lot_number = models.IntegerField(default=0)
    roll_number = models.IntegerField(default=0)
    qty_kg = models.FloatField(default=0)
    qty_m = models.FloatField(default=0)
    
    quotation_line = models.ForeignKey(
    "order.QuotationLine",
    on_delete=models.CASCADE,
    null=True,
    blank=True
)
    status = models.CharField(
        max_length=20,
        choices=[
            ("incoming", "Incoming"),
            ("actual", "Actual"),
            ("reserved", "Reserved"),
            ("backorder", "Backorder"),
        ],
        default="incoming"
    )

    def __str__(self):
        return f"{self.joia_code} - {self.color_name}"