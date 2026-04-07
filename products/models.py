from django.db import models
import re
import webcolors


class Product(models.Model):
    joia_code = models.CharField(max_length=50, unique=True, db_index=True)
    style_number = models.CharField(max_length=50)
    composition = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20, default="m")
    avg_roll = models.FloatField(default=0)
    selling_price = models.FloatField(default=0)
    costing_price = models.FloatField(default=0)

    def __str__(self):
        return f"{self.style_number} ({self.joia_code})"


class Color(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="colors"
    )

    color_code = models.CharField(max_length=50)
    color_name = models.CharField(max_length=50, default="unknown")

    def get_display_color(self):  # ✅ جوه الكلاس
        name = (self.color_name or "").lower()

        try:
            return webcolors.name_to_hex(name)
        except:
            pass

        color_map = {
            "black": "#000000",
            "white": "#ffffff",
            "red": "#ff0000",
            "blue": "#0000ff",
            "green": "#008000",
            "yellow": "#ffff00",
            "gray": "#808080",
            "grey": "#808080",
            "navy": "#000080",
            "beige": "#f5f5dc",
            "brown": "#8b4513",
            "pink": "#ffc0cb",
            "purple": "#800080",
            "orange": "#ffa500",
        }

        for key in color_map:
            if key in name:
                return color_map[key]

        return "#999999"

    def __str__(self):
        return f"{self.product.joia_code} - {self.color_name}"

    def __str__(self):
        return f"{self.product.joia_code} - {self.color_name}"