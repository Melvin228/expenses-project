from django.shortcuts import render

# Create your views here.


def index(req):
    return render(req, 'expenses/index.html')


def add_expense(req):
    return render(req, 'expenses/add-expense.html')
