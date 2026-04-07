from django.core.management.base import BaseCommand
from inventory.models import Stock
from products.models import Product


class Command(BaseCommand):
    help = "Sync products from stock"

    def handle(self, *args, **kwargs):

        codes = Stock.objects.values_list('joia_code', flat=True).distinct()

        created = 0

        for code in codes:
            obj, is_created = Product.objects.get_or_create(
                joia_code=code,
                defaults={"style_number": code}
            )

            if is_created:
                created += 1

        self.stdout.write(f"✅ Created: {created} products")