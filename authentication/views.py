from django.shortcuts import render, redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib import auth
from django.urls import reverse
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import account_activation_token
from django.contrib.auth.tokens import PasswordResetTokenGenerator

import threading

# Create your views here.


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=False)


class RegistrationView(View):
    def get(self, req):
        return render(req, "authentication/register.html")

    def post(self, req):
        # Get user data
        # VALIDATE
        # create user data

        username = req.POST['username']
        email = req.POST['email']
        password = req.POST['password']

        context = {
            'fieldValues': req.POST
        }

        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password) < 6:
                    messages.error(req, "Password is too short")
                    return render(req, 'authentication/register.html', context)

                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.is_active = False
                user.save()
                email_subject = "Activate your account"

                # path_to_view
                # -getting domain we are on
                # - relative url to verification
                # - encode ul
                # - token
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                domain = get_current_site(req).domain
                link = reverse('activate', kwargs={
                               'uidb64': uidb64, 'token': account_activation_token .make_token(user)})

                activate_url = "http://"+domain+link

                email_body = 'Hi ' + user.username + \
                    " Please use this link to verify this account\n" + activate_url
                email = EmailMessage(
                    email_subject,
                    email_body,
                    "noreply@email.com",
                    [email],


                )

                EmailThread(email).start()
                messages.success(req, "Account successfully created")
                return render(req, 'authentication/register.html')
        return render(req, "authentication/register.html")


class UsernameValidationView(View):
    def post(self, req):
        data = json.loads(req.body)
        username = data['username']

        if not str(username).isalnum():
            return JsonResponse({'username_error': "Username should only contain alphanumberic characters "}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({"username_error": "User already exist"}, status=409)

        return JsonResponse({'username_valid': True})


class EmailValidationView(View):
    def post(self, req):
        data = json.loads(req.body)
        email = data['email']

        if not validate_email(email):
            return JsonResponse({"email_error": "Email is invalid"}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({"email_error": "Email already exist"}, status=409)

        return JsonResponse({"email_valid": True})


class VerificationView(View):
    def get(self, request, uidb64, token):
        try:
            id = force_text(urlsafe_base64_decode(uidb64))
            print("The user id is" + id)
            user = User.objects.get(pk=id)

            if not account_activation_token.check_token(user, token):
                return redirect('login'+'?message' + "User already activated")

            if user.is_active:
                return redirect('login')
            user.is_active = True
            user.save()

            messages.success(request, "Account activated successfully")
            return redirect('login')
        except Exception as ex:
            pass

        return redirect('login')


class LoginView(View):
    def get(self, req):
        return render(req, "authentication/login.html")

    def post(self, req):
        username = req.POST['username']
        password = req.POST['password']

        if username and password:
            user = auth.authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    auth.login(req, user)
                    messages.success(req, "Welcome, " +
                                     user.username + " You are now logged in")
                    return redirect('expenses')

                messages.error(
                    req, "Account is not active, please check your email")
                return render(req, "authentication/login.html")
            messages.error(
                req, "Invalid credentials/ Your account is not activated yet")
            return render(req, "authentication/login.html")

        messages.error(req, "Please fill in all fields")
        return render(req, "authentication/login.html")


class LogoutView(View):
    def post(self, req):
        auth.logout(req)
        messages.success(req, 'You have been logged out!')
        return redirect('login')


class RequestPasswordResetEmail(View):
    def get(self, req):
        return render(req, 'authentication/reset-password.html')

    def post(self, req):
        email = req.POST['email']
        context = {
            'values': req.POST
        }

        if not validate_email(email):
            messages.error(req, "Please provide a valid email")
            return render(req, 'authenticaiton/reset-password.html', context)

        current_site = get_current_site(req)

        user = User.objects.filter(email=email)

        if user.exists():
            email_contents = {
                'user': user[0],
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token': PasswordResetTokenGenerator().make_token(user[0])
            }
            link = reverse('reset-user-password', kwargs={
                'uidb64': email_contents['uid'], 'token': email_contents['token']})

            email_subject = "Password reset instructions"
            reset_url = "http://"+current_site.domain+link

            email = EmailMessage(
                email_subject,
                'Hi there, Please click the link below to reset your password \n' + reset_url,
                "noreply@email.com",
                [email],
            )

        EmailThread(email).start()

        messages.success(req, "We have sent an email to reset the password")

        return render(req, 'authentication/reset-password.html')


class CompletePasswordReset(View):
    def get(self, req, uidb64, token):

        context = {
            'uidb64': uidb64,
            'token': token
        }
        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))

            user = User.objects.get(pk=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(
                    req, "Password link is invalid, please request a new one")
                return render(req, 'authentication/reset-password.html')

        except Exception as identifier:
            messages.info(req, 'Error occured')
            return render(req, 'authentication/reset-password.html')
        return render(req, "authentication/set-new-password.html", context)

    def post(self, req, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token
        }

        password = req.POST['password']
        password2 = req.POST['password2']

        if password != password2:
            messages.error(req, "Passwords do not match")
            return render(req, 'authentication/set-new-password.html', context)

        if len(password) < 6:
            messages.error(req, 'Password too short')
            return render(req, 'authentication/set-new-password.html', context)

        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))

            user = User.objects.get(pk=user_id)
            user.password = password
            user.save()
            messages.success(req, "New password saved successfully")
            return redirect('login')
        except Exception as identifier:
            messages.info(req, 'Something went wrong')
            return render(req, 'authentication/set-new-password.html', context)
