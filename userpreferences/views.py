from django.shortcuts import render
import os
import json
from django.conf import settings
from .models import UserPreference
from django.contrib import messages
# Create your views here.


def index(req):
    currency_data = []

    file_path = os.path.join(settings.BASE_DIR, 'currencies.json')

    with open(file_path, "r") as json_file:
        data = json.load(json_file)

        for k, v in data.items():
            currency_data.append({"name": k, "value": v})
    exists = UserPreference.objects.filter(
        user=req.user).exists()
    user_preferences = None
    if exists:
        user_preferences = UserPreference.objects.get(user=req.user)

    if req.method == "GET":

        return render(req, 'preferences/index.html', {"currencies": currency_data, "user_preferences": user_preferences})
    else:
        currency = req.POST['currency']
        if exists:
            user_preferences.currency = currency
            user_preferences.save()
        else:
            UserPreference.objects.create(user=req.user, currency=currency)

        messages.success(req, "Changes saved!")
        return render(req, 'preferences/index.html', {"currencies": currency_data, "user_preferences": user_preferences})
