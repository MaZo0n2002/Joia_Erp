from django.shortcuts import render, redirect
from customers.models import Customer
from .forms import CustomerForm


def customers(request):

    if request.method == "POST":
        customer_id = request.POST.get("customer_id")
        if customer_id:
            customer = Customer.objects.get(id=customer_id)
            form = CustomerForm(request.POST, instance=customer)

        else:
            form = CustomerForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("customers")

    else:
        form = CustomerForm()

    customers = Customer.objects.all()

    return render(
        request,
        "dashboard/customer.html",
        {
            "form": form,
            "customers": customers
        }
    )


def edit_customer(request, customer_id):
    customer = Customer.objects.get(id=customer_id)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)

        if form.is_valid():
            form.save()
            return redirect("customers")

    else:
        form = CustomerForm(instance=customer)
    customers = Customer.objects.all()
    return render(
        request,
        "dashboard/customer.html",
        {
            "form": form,
            "customer": customers
        }
    )


def delete_customer(request, customer_id):
    customer = Customer.objects.get(id=customer_id)
    customer.delete()
    return redirect("customers")
    