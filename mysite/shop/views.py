from django.forms import forms
from django.shortcuts import render,redirect
from django.views.generic import FormView
from .models import Product, Contact, Orders, OrderUpdate,Customer
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password,check_password
from .paytm import Checksum
from django.views import View

MERCHANT_KEY = 'kPON4QTZ2ZdkP3_u';
def index(request):
    products= Product.objects.all()
    allProds=[]
    catprods= Product.objects.values('category', 'id')
    cats= {item["category"] for item in catprods}
    for cat in cats:
        prod=Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    params={'allProds':allProds,'cats':cats }
    return render(request,"shop/index.html", params)

def searchMatch(query,item):
    if query in item.desc.lower() or  query in item.desc or query in item.desc.upper() or query in item.product_name or query in item.product_name.upper() or query in item.product_name.lower() or query in item.category.lower() or query in item.category or query in item.category.upper():
        return True
    else:
        return False

def Search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item["category"] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query,item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if (len(prod)!=0):
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds,"msg":""}
    if len(allProds)==0 or len(query)<4:
        params={'msg':"Please Make Sure to enter relavent search query"}
    return render(request, "shop/search.html", params)

def about(request):
    return render(request,'shop/about.html')

def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        phone = request.POST.get('phone','')
        desc = request.POST.get('desc','')
        contact = Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()
        thank = True
    return render(request,'shop/contactus.html',{'thank':thank})

def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"status": "success", "updates": updates, "itemsJson": order[0].items_json},
                                          default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')
    return render(request, 'shop/tracker.html')

def productview(request, myid):
    product=Product.objects.filter(id=myid)
    return render(request, "shop/prodview.html", {'product':product[0]})

def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')

        customer_email = Customer.get_customer_by_email(email)
        error_message = None

        if customer_email:
            order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                           state=state, zip_code=zip_code, phone=phone, amount=amount)

            order.save()

            update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
            update.save()

            thank = True
            id = order.order_id

            param_dict = {
                'MID': 'FUuxvQ92840896867495',
                'ORDER_ID': str(order.order_id),
                'TXN_AMOUNT': str(amount),
                'CUST_ID': email,
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL': 'http://127.0.0.1:8000/shop/handlerequest/',
            }
            param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
            return render(request, 'shop/paytm.html', {'param_dict': param_dict,'id':id})
        else:
            error_message = "Please enter the registered Email !!"
            return render(request, 'shop/checkout.html', {'error': error_message})
    else:
        return render(request,'shop/checkout.html')

@csrf_exempt
def handlerequest(request):
    # paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]
    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            #IF the Payment is not successful then delete the order details regarding the order id has to be removed
            instance = Orders.objects.get(id=id)
            instance.delete()
            instance1 = OrderUpdate.objects.get(id=id)
            instance1.delete()
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})

class Signup(View):
    def get(self,request):
        return render(request, 'shop/signup.html')

    def post(self,request):
        postData = request.POST
        first_name = postData.get('firstname')
        last_name = postData.get('lastname')
        phone = postData.get('phone')
        email = postData.get('email')
        password = postData.get('password')
        nickname = postData.get('nickname')

        value = {'first_name': first_name, 'last_name': last_name, 'phone': phone, 'email': email}
        error_message = None

        customer = Customer(first_name=first_name, last_name=last_name, phone=phone, email=email, password=password, nickname=nickname)
        if customer.isExists():
            error_message = 'Email Address Already Registered'
            data = {'error': error_message, 'values': value}
            return render(request, 'shop/signup.html', data)
        else:
            customer.password = make_password(customer.password)
            customer.save()
            return redirect("ShopHome")

class Login(View):
    def get(self,request):
        return render(request,'shop/login.html')
    def post(self,request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        customer = Customer.get_customer_by_email(email)
        error_message = None
        if customer:
            flag = check_password(password, customer.password)
            if flag:
                request.session['customer']=customer.id
                request.session['customer_email'] = customer.email
                return redirect("ShopHome")
            else:
                error_message = "Email or Password invalid !!"
        else:
            error_message = "Email or Password invalid !!"
        return render(request, 'shop/login.html', {'error': error_message})
def logout(request):
    request.session.clear()
    return redirect('login')

def contact(request):
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        customer_email = Customer.get_customer_by_email(email)
        error_message = None
        if customer_email:
            contact.save()
            return redirect("ShopHome")
        else:
            error_message = "Invalid User !!"
            return render(request, 'shop/contactus.html', {'error': error_message})
    else:
        return render(request,'shop/contactus.html')

def changePwd(request):
    nname = request.POST.get('nickname')
    email = request.POST.get('email')
    customer_email = Customer.get_customer_by_email(email)

    cust = Customer.get_customer_by_email(email)
    if not customer_email:
        error_message = "Invalid email address "
        return render(request, 'shop/forgot.html', {'error': error_message})
    elif cust.nickname == nname and customer_email:
        return render(request, 'shop/changepwd.html')
    else:
        error_message = "Invalid Nick Name "
        return render(request, 'shop/forgot.html', {'error': error_message})



def successChanged(request):
    email = request.POST.get('email')
    newpsd = request.POST.get('newpwd')
    # print(newpsd)
    repwd = request.POST.get('repwd')
    cust = Customer.get_customer_by_email(email)
    customer_email = Customer.get_customer_by_email(email)
    if not customer_email:
        error_message = "Invalid email address "
        return render(request, 'shop/changepwd.html', {'error': error_message})
    elif repwd!=newpsd:
        error_message = "Please Enter same password for new password and re-entered password"
        return render(request, 'shop/changepwd.html', {'error': error_message})
    elif  customer_email and (repwd==newpsd):
        cust.password = newpsd
        print(cust.password)
        print('changed')
        cust.password = make_password(cust.password)
    # print(cust.password)
        cust.save()
        return render(request, 'shop/successmessage.html')

def forgot(request):
    return render(request, 'shop/forgot.html')
