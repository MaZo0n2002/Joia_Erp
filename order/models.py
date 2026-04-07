from decimal import Decimal

from django.db import models
from django.forms import ValidationError
from customers.models import Customer
from django.db import transaction
# Create your models here.





class Quotation(models.Model):
    quotation_number = models.PositiveIntegerField(unique=True, editable=False)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=14)

    notes = models.TextField(blank=True, null=True)  # 🔥 added

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def subtotal(self):
        return sum((line.line_total() for line in self.lines.all()), Decimal("0."))

    @property
    def vat_amount(self):
        return self.subtotal * (self.vat_percentage / Decimal("100"))
    

    @property
    def total(self):
        return self.subtotal + self.vat_amount

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            with transaction.atomic():
                last = Quotation.objects.select_for_update().order_by('-quotation_number').first()
                self.quotation_number = (last.quotation_number + 1) if last else 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Quotation #{self.quotation_number}"

class QuotationLine(models.Model):

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name="lines"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    joia_code = models.CharField(max_length=100)

    color_code = models.CharField(max_length=50, default="unknown")
    color_name = models.CharField(max_length=100, default="unknown")

    rolls = models.IntegerField()

    qty_m = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
      return (self.qty_m or 0) * (self.unit_price or 0)
 
    def line_total(self):
        return self.qty_m * self.unit_price

    def __str__(self):
        return f"{self.joia_code} - {self.color_name}"

    def clean(self):
        if self.qty_m <= 0:
            raise ValidationError("Quantity must be greater than 0")