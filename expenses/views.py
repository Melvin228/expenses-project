from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . models import Category, Expense
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
from userpreferences.models import UserPreference
import datetime
import csv
import xlwt

from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.db.models import Sum
# Create your views here.


@login_required(login_url="authentication/login")
def index(req):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=req.user)
    paginator = Paginator(expenses, 10)
    page_number = req.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    currency = UserPreference.objects.get(user=req.user)
    # import pdb
    # pdb.set_trace()
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency
    }
    return render(req, 'expenses/index.html', context)


@login_required(login_url="authentication/login")
def add_expense(req):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values': req.POST
    }
    if req.method == 'GET':
        return render(req, 'expenses/add_expense.html', context)

    if req.method == 'POST':
        amount = req.POST['amount']
        description = req.POST['description']
        date = req.POST['expense_date']
        category = req.POST['category']

        if not amount:
            messages.error(req, 'Amount is required')
            return render(req, 'expenses/add_expense.html', context)

        if not description:
            messages.error(req, 'description is required')
            return render(req, 'expenses/add_expense.html', context)

        Expense.objects.create(owner=req.user, amount=amount, date=date,
                               category=category, description=description)
        messages.success(req, 'Expense saved successfully')

        return redirect('expenses')


def edit_expense(req, id):
    categories = Category.objects.all()
    expense = Expense.objects.get(pk=id)
    # import pdb
    # pdb.set_trace()
    context = {
        'expense': expense,
        'values': expense,
        "categories": categories
    }
    if req.method == "GET":

        return render(req, 'expenses/edit-expense.html', context)

    if req.method == "POST":
        amount = req.POST['amount']
        description = req.POST['description']
        date = req.POST['expense_date']
        category = req.POST['category']

        if not amount:
            messages.error(req, 'Amount is required')
            return render(req, 'expenses/edit-expense.html', context)

        if not description:
            messages.error(req, 'description is required')
            return render(req, 'expenses/edit-expense.html', context)

        expense.owner = req.user
        expense.amount = amount
        expense.date = date
        expense.category = category
        expense.description = description

        expense.save()
        messages.success(req, 'Expense updated successfully')

        return redirect('expenses')

        # messages.info(req, "Handling post form")
        # return render(req, 'expenses/edit-expense.html', context)


def delete_expense(req, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(req, "Expense removed")
    return redirect('expenses')


def search_expense(req):
    if req.method == "POST":
        search_str = json.loads(req.body).get("searchText")

        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=req.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=req.user) | Expense.objects.filter(
            description__icontains=search_str, owner=req.user) | Expense.objects.filter(
            category__icontains=search_str, owner=req.user)

        data = expenses.values()

        return JsonResponse(list(data), safe=False)


def expense_category_summary(req):
    today_date = datetime.date.today()
    six_months_ago = today_date - datetime.timedelta(days=30*6)
    expenses = Expense.objects.filter(
        owner=req.user,
        date__gte=six_months_ago, date__lte=today_date)
    finalrep = {}

    def get_category(expense):
        return expense.category

    category_list = list(set(map(get_category, expenses)))

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category=category)
        # print(filtered_by_category)
        for item in filtered_by_category:

            amount += item.amount

        return amount

    for x in expenses:
        for y in category_list:
            finalrep[y] = get_expense_category_amount(y)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)


def stats_view(req):
    return render(req, 'expenses/stats.html')


def export_csv(req):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachments; filename=Expenses' + \
        str(datetime.datetime.now()) + ".csv"
    writer = csv.writer(response)

    writer.writerow(['Amount', "Description", "Category", "Date"])
    expenses = Expense.objects.filter(owner=req.user)

    for expense in expenses:
        writer.writerow([expense.amount, expense.description,
                        expense.category, expense.date])

    return response


def export_excel(req):
    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachments; filename=Expenses' + \
        str(datetime.datetime.now()) + ".xls"
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Expenses")
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Amount', "Description", "Category", "Date"]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = Expense.objects.filter(owner=req.user).values_list(
        'amount', 'description', 'category', 'date')

    for row in rows:
        row_num += 1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    return response


def export_pdf(req):
    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'inline;attachments; filename=Expenses' + \
        str(datetime.datetime.now()) + ".pdf"
    response['Content-Transfer-Encoding'] = 'binary'

    expenses = Expense.objects.filter(owner=req.user)

    sum = expenses.aggregate(Sum('amount'))

    html_string = render_to_string(
        'expenses/pdf-output.html', {'expenses': expenses, 'total': "sum"})
    html = HTML(string=html_string)

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()

        output = open(output.name, 'rb')

        response.write(output.read())

    return response
