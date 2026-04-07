from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils.timezone import now


# ================= SALES ORDER =================
class SalesOrder(models.Model):

    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE)

    quotation = models.OneToOneField(
        "order.Quotation",
        on_delete=models.CASCADE,
        related_name="sales_order"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
        ],
        default="draft"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=now)  # ✅ IMPORTANT

    # ✅ FIXED (safe)
    @property
    def is_fully_delivered(self):
        return all(line.is_delivered for line in self.lines.all())

    def __str__(self):
        return f"SO-{self.id}"


# ================= SALES ORDER LINE =================
class SalesOrderLine(models.Model):

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name="lines"
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    color = models.CharField(max_length=50)

    requested_qty = models.FloatField()
    delivered_qty = models.FloatField(default=0)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    @property
    def is_delivered(self):
     return self.remaining_qty() == 0

    @property
    def is_partial(self):
      return 0 < self.delivered_qty < self.requested_qty

    @property
    def is_ready(self):
      return self.reserved_qty() > 0 and self.delivered_qty == 0

    def reserved_qty(self):
        return sum(r.quantity for r in self.reservations.filter(status='reserved'))

    def remaining_qty(self):
        return max(0, self.requested_qty - self.delivered_qty)

    def clean(self):
        if self.delivered_qty > self.requested_qty:
            raise ValidationError("Delivered > Requested")

    def __str__(self):
        return f"{self.product or 'No Product'} - {self.color}"


# ================= RESERVATION =================
class Reservation(models.Model):

    stock = models.ForeignKey(
        "inventory.Stock",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    color = models.CharField(max_length=50)

    quantity = models.FloatField()

    quotation_line = models.ForeignKey(
        "order.QuotationLine",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    order_line = models.ForeignKey(
        SalesOrderLine,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reservations"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('reserved', 'Reserved'),
            ('consumed', 'Consumed'),
            ('backorder', 'Backorder'),
        ],
        default='reserved'
    )

    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.product or 'No Product'} - {self.quantity} ({self.status})"


# ================= INVOICE =================
class Invoice(models.Model):

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE
    )

    sales_order = models.OneToOneField(
        "Sales_Order.SalesOrder",
        on_delete=models.CASCADE,
        related_name="invoice"
    )

    total = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("paid", "Paid"),
        ],
        default="confirmed"
    )

    created_at = models.DateTimeField(default=now)  # ✅ IMPORTANT
    notes = models.TextField(blank=True, null=True)


    # ✅ OPTIONAL (better PDF)
    @property
    def subtotal(self):
        return self.total / Decimal("1.14")

    @property
    def vat(self):
        return self.total - self.subtotal

    def __str__(self):
        return f"INV-{self.id}"