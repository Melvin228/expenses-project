from django.shortcuts import render
from django.views import View

# Create your views here.

class RegistrationView(View):
    def get(self,req):
        return render(req,"authentication/register.html")