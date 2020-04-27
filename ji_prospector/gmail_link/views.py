from django.shortcuts import render

# Create your views here.
def auth_with_gmail_phase0(request):
    # first, redirect to the right Gmail API page, so that we login
    return

def auth_with_gmail_phase1(request):
    # the right Gmail page will redirect here, with an "authorization code"
    # ask the API for an "access token" in exchange for the authorization code. we must do it in "offline" mode, so the user can be logged out of their gmail account
    # this token will last for some time. we need to remember it. there is also a refresh token with it, which we must remember
    return
