from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Source, UserIncome
from django.core.paginator import Paginator
from userpreferences.models import UserPreference
from django.contrib import messages
import json
from django.http import JsonResponse

# Create your views here.


@login_required(login_url="authentication/login")
def index(req):
    categories = Source.objects.all()
    income = UserIncome.objects.filter(owner=req.user)
    paginator = Paginator(income, 10)
    page_number = req.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    currency = UserPreference.objects.get(user=req.user)
    # import pdb
    # pdb.set_trace()
    context = {
        'income': income,
        'page_obj': page_obj,
        'currency': currency
    }
    return render(req, 'income/index.html', context)


@login_required(login_url="authentication/login")
def add_income(req):
    sources = Source.objects.all()
    context = {
        'sources': sources,
        'values': req.POST
    }
    if req.method == 'GET':
        return render(req, 'income/add_income.html', context)

    if req.method == 'POST':
        amount = req.POST['amount']
        description = req.POST['description']
        date = req.POST['income_date']
        source = req.POST['source']

        if not amount:
            messages.error(req, 'Amount is required')
            return render(req, 'income/add_income.html', context)

        if not description:
            messages.error(req, 'description is required')
            return render(req, 'incomes/add_income.html', context)

        UserIncome.objects.create(owner=req.user, amount=amount, date=date,
                                  source=source, description=description)
        messages.success(req, 'Record saved successfully')

        return redirect('income')


def edit_income(req, id):
    sources = Source.objects.all()
    income = UserIncome.objects.get(pk=id)
    # import pdb
    # pdb.set_trace()
    context = {
        'income': income,
        'values': income,
        "sources": sources
    }
    if req.method == "GET":

        return render(req, 'income/edit_income.html', context)

    if req.method == "POST":
        amount = req.POST['amount']
        description = req.POST['description']
        date = req.POST['income_date']
        source = req.POST['source']

        if not amount:
            messages.error(req, 'Amount is required')
            return render(req, 'income/edit_income.html', context)

        if not description:
            messages.error(req, 'description is required')
            return render(req, 'income/edit_income.html', context)

        income.amount = amount
        income.date = date
        income.source = source
        income.description = description

        income.save()
        messages.success(req, 'Record updated successfully')

        return redirect('income')

        # messages.info(req, "Handling post form")
        # return render(req, 'expenses/edit-expense.html', context)


def delete_income(req, id):
    income = UserIncome.objects.get(pk=id)
    income.delete()
    messages.success(req, "record removed")
    return redirect('income')


def search_income(req):
    if req.method == "POST":
        search_str = json.loads(req.body).get("searchText")

        income = UserIncome.objects.filter(
            amount__istartswith=search_str, owner=req.user) | UserIncome.objects.filter(
            date__istartswith=search_str, owner=req.user) | UserIncome.objects.filter(
            description__icontains=search_str, owner=req.user) | UserIncome.objects.filter(
            source__icontains=search_str, owner=req.user)

        data = income.values()

        return JsonResponse(list(data), safe=False)
