from django.shortcuts import redirect, render
from .models import Factory
from .forms import FactoryForm

# Create your views here.

def factories(request):

    if request.method == "POST":
        factory_id = request.POST.get("factory_id")
        if factory_id:
            factory = Factory.objects.get(id=factory_id)
            form = FactoryForm(request.POST, instance=factory)

        else:
            form = FactoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("factories")

    else:
        form = FactoryForm()

    factories = Factory.objects.all()

    return render(request, "dashboard/factories.html", {"form": form, "factories": factories})


def edit_factory(request, factory_id):
    factory = Factory.objects.get(id=factory_id)

    if request.method == "POST":
        form = FactoryForm(request.POST, instance=factory)

        if form.is_valid():
            form.save()
            return redirect("factories")

    else:
        form = FactoryForm(instance=factory)
    factories = Factory.objects.all()
    return render(request, "factories.html", {"form": form, "factories": factories})

def delete_factory(request, factory_id):
    factory = Factory.objects.get(id=factory_id)
    factory.delete()
    return redirect("factories")
