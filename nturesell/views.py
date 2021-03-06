from django.shortcuts import render, redirect   # 加入 redirect 套件
from django.contrib.auth import authenticate
from django.contrib import auth
from django.http import HttpResponse
from django.contrib.auth.models import User as AbstractUser
from users.models import User, Product, Message, Comment, UserProfile, ChatRoom, Wallet
from users.form import UploadProductForm, UploadProfileForm
from django.contrib.auth.decorators import login_required
from itertools import chain
import hashlib
import os
import random

from typing import List
from datetime import datetime
from .algo.estimator import Estimator
from .algo.model import Task, Tug

def estimate_example(algo_id):
    """
    An example to estimate the build-in dispatching algorithm
    See cool_dispatch in algo/greedy/cool.py for reference
    """
    est = Estimator()
    from .algo.greedy.cool import cool_dispatch
    from .algo.greedy.timeline import timeline_dispatch
    est.set_range(100, 110)
    if algo_id == "1":
        kh = est.run(cool_dispatch, verbose=False)
        est.print_result(kh)
        est.draw(kh)
    elif algo_id == "2":
        kh = est.run(timeline_dispatch, verbose=False)
        est.print_result(kh)
        est.draw(kh)


@login_required
def home(request):
    next_weight = random.randint(10000,100000)
    harbor1 = random.randint(1,121)
    harbor2 = random.randint(1,121)
    if harbor1 < 40:
        nextpilot = "信穎棒"
    elif harbor1 >= 40 and harbor1 < 90:
        nextpilot = "王小明"
    else:
        nextpilot = "料理鼠"

    task_in = random.randint(0,10)
    task_out = random.randint(0,10-task_in)
    task_trans = random.randint(0,15-task_in - task_out)
    event = ["開始時間延遲","工作時間延遲","工作取消","加船","換船"]
    pre_event = event[0]
    tug_first = 350
    tug_second = 432  
    username = request.user.username
    print(request.POST)
    if 'change_algo' in request.POST:
        algo_id = request.POST['change_algo']
    else:
        algo_id = "1"
    algorithm = ["關鍵資源優先演算法","開始時間優先演算法"]
    algo = algorithm[int(algo_id)-1] 
    if 'searchproduct' in request.POST:
        productname = request.POST["productname"]
        products1 = Product.objects.filter(productname__icontains=productname)
        products2 = Product.objects.filter(information__icontains=productname)
        products = (list(set(chain(products1, products2))))

    # elif 'start_dispatch' in request.POST:
    #     estimate_example(algo_id)

    elif 'update' in request.POST:
        next_weight = random.randint(10000,100000)
        harbor1 = random.randint(1,121)
        harbor2 = random.randint(1,121)
        if harbor1 < 40:
            nextpilot = "信穎棒"
        elif harbor1 >= 40 and harbor1 < 90:
            nextpilot = "王小明"
        else:
            nextpilot = "料理鼠"

        task_in = random.randint(0,10)
        task_out = random.randint(0,10-task_in)
        task_trans = random.randint(0,15-task_in - task_out)
        event = ["開始時間延遲","工作時間延遲","工作取消","加船","換船"]
        pre_event = event[random.randint(0,4)]
        tug_first = random.randint(100,405)
        tug_second = random.randint(300, 605)   
    else:
        products = Product.objects.filter(status=1)

    return render(request, 'index.html', locals())

def event(request):
    event_type = ["開始時間延遲","工作時間延遲","工作取消","加船","換船"]
    tugs = [106,309,456,778,990,341,331,109,107,310,331,234,450,550,880]
    if request.method == "POST":
        return redirect('home')
    return render(request, 'cards.html', locals())

def register(request):
    if request.method == "POST" and request.POST["username"] != "":
        print("in")
        username = request.POST["username"]
        nickname = request.POST["nickname"]
        ntumail = request.POST["ntumail"]
        password = request.POST["password"]
        confirmpassword = request.POST["confirm-password"]
        if(password == confirmpassword):
            try:
                user = AbstractUser.objects.filter(username=uname)
            except:
                user = None

            if user is not None:
                message = "Username used by another"
                return render(request, "login.html", locals())
            else:
                user = AbstractUser.objects.create_user(
                    username=username, password=password)
                userinfo = User.objects.create(
                    user=user, nickname=nickname, ntumail=ntumail)
                userinfo.save()
                message = "Successfully register"
                return render(request,"login.html", locals())
        else:
            message = "confirm password is different from password"
            return render(request, "login.html", locals())
    return render(request, "register.html", locals())


def authenticate(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return redirect('home')
        else:
            message = "Username or password wrong"
            return render(request, "login.html", locals())
    return render(request, "index.html", locals())

def login(request):
    if request.method == "POST":
        try:
            if request.POST['submit-type'] == "Log In":
                return authenticate(request)
            elif request.POST['submit-type'] == "Register Now":
                return register(request)
        except:
            message="Register unsucessful"
    return render(request, "login.html", locals())


# @login_required
# def profile(request):
#     if 'submit' in request.POST:
#         if (UserProfile.objects.filter(user_id=request.user.pk).exists()):
#             oldavatar = UserProfile.objects.filter(user_id=request.user.pk)
#             oldavatar.delete()
#         form = UploadProfileForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()

#     elif 'searchproduct' in request.POST:
#         productname = request.POST["productname"]
#         products1 = Product.objects.filter(
#             productname__icontains=productname, seller__username=request.user.username)
#         products2 = Product.objects.filter(
#             information__icontains=productname, seller__username=request.user.username)
#         products = (list(set(chain(products1, products2))))
#         return render(request, 'selldisplay.html', locals())

#     elif 'whatisell' in request.POST:
#         products = Product.objects.filter(
#             seller__username=request.user.username)
#         return render(request, 'selldisplay.html', locals())

#     if request.user.is_authenticated:
#         profile = User.objects.get(user__id=request.user.pk)
#         if UserProfile.objects.filter(user__id=request.user.pk).exists():
#             avatar = UserProfile.objects.get(
#                 user_id=request.user.pk)
#         return render(request, 'profile.html', locals())
#     return render(request, 'profile.html', locals())


# @login_required
# def sell(request):
#     if request.method == "POST":
#         form = UploadProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('home')
#     return render(request, 'sell.html', locals())


def logout(request):
    auth.logout(request)
    return redirect('/register')


# @login_required
# def productdetail(request):
#     if 'commenting' in request.POST:
#         commenter = AbstractUser.objects.get(username=request.user.username)
#         comment = request.POST['comment']
#         productpk = request.POST['productpk']
#         Comment.objects.create(commenter=commenter,
#                                 productpk=productpk, comment=comment)
#         products = Product.objects.get(id=productpk)
#         comment = Comment.objects.filter(productpk=productpk)
#         return render(request, 'productdetail.html', locals())
#     if request.method == "POST":
#         productpk = request.POST["productpk"]
#         products = Product.objects.get(id=productpk)
#         comment = Comment.objects.filter(productpk=productpk)
#         return render(request, 'productdetail.html', locals())
#     return render(request, 'productdetail.html', locals())

# @login_required
# def editproduct(request):
#     if 'deleteitem' in request.POST:
#         productpk=request.POST['productpk']
#         Product.objects.get(
#             id=productpk).delete()
#         products = Product.objects.filter(
#             seller__username=request.user.username)
#         return render(request,'selldisplay.html',locals())
#     if 'solditem' in request.POST:
#         productpk=request.POST['productpk']
#         buyername = request.POST['buyername']
#         if(buyername != request.user.username):
#             try:
#                 buyer = AbstractUser.objects.get(username=buyername)
#             except:
#                 buyer = None
#             if buyer is None:
#                 error="User not Found!Please make sure you enter correct username"
#                 products = Product.objects.get(id=productpk)
#                 return render(request,'editproduct.html',locals())
#             else:
#                 buyer = AbstractUser.objects.get(username=buyername)
#                 products=Product.objects.get(id=productpk)
#                 try:
#                     wallet = Wallet.objects.get(user=buyer)
#                 except:
#                     wallet = None
#                 if wallet is None:
#                     Wallet.objects.create(user=buyer,amount=products.price)
#                 else:
#                     newbuyupdate=Wallet.objects.get(user=buyer)
#                     nowspend=0
#                     nowspend=newbuyupdate.amount
#                     newbuyupdate.amount=nowspend+products.price
#                     newbuyupdate.save()
#             products.buyer=buyer
#             products.status = 0
#             products.save()
#             products = Product.objects.get(id=productpk)
#             return render(request,'editproduct.html',locals())
#         else:
#             products = Product.objects.get(id=productpk)
#             error="cant sell item to yourself"
#             return render(request,'editproduct.html',locals())
#     if 'changebuyer' in request.POST:
#         productpk=request.POST['productpk']
#         buyername = request.POST['buyername']
#         if(buyername != request.user.username):
#             try:
#                 buyer = AbstractUser.objects.get(username=buyername)
#             except:
#                 buyer = None
#             if buyer is None:
#                 error="User not Found!Please make sure you enter correct username"
#                 products = Product.objects.get(id=productpk)
#                 return render(request,'editproduct.html',locals())
#             else:
#                 buyer = AbstractUser.objects.get(username=buyername)
#                 products=Product.objects.get(id=productpk)
#                 reducebuyupdate=Wallet.objects.get(user=products.buyer)
#                 newreducebuyer=0
#                 newreducebuyer=reducebuyupdate.amount
#                 reducebuyupdate.amount=newreducebuyer-products.price
#                 reducebuyupdate.save()
#                 try:
#                     wallet = Wallet.objects.get(user=buyer)
#                 except:
#                     wallet = None
#                 if wallet is None:
#                     Wallet.objects.create(user=buyer,amount=products.price)
#                 else:
#                     newchangebuyerupdate=Wallet.objects.get(user=buyer)
#                     nowspend=0
#                     nowspend=newchangebuyerupdate.amount
#                     newchangebuyerupdate.amount=nowspend+products.price
#                     newchangebuyerupdate.save()
#                 products.buyer=buyer
#                 products.save()
#                 products = Product.objects.get(id=productpk)
#             return render(request,'editproduct.html',locals())
#         else:
#             products = Product.objects.get(id=productpk)
#             error="cant sell item to yourself"
#             return render(request,'editproduct.html',locals())
#     if request.method == "POST":
#         productpk = request.POST["productpk"]
#         products = Product.objects.get(id=productpk)
#     return render(request,'editproduct.html',locals())
    
# def boughthistory(request):
#     try:
#         wallet = Wallet.objects.get(user=request.user)
#     except:
#         wallet = None
#     if wallet is None:
#         message="You havent bought anything"
#         return render(request,'boughthistory.html',locals())
#     else:
#         products=Product.objects.filter(buyer=request.user)
#         return render(request,'boughthistory.html',locals())