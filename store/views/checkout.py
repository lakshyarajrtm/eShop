from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from store.models.customer import Customer
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from store.models.product import Products
from store.models.orders import Order
import paytmchecksum
import json
from django.conf import settings



class CheckOut(View):
    def post(self, request):
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        customer = request.session.get('customer')
        cart = request.session.get('cart')
        products = Products.get_products_by_id(list(cart.keys()))
        print(address, phone, customer, cart, products)
        amount = 0
        for product in products:
            print(cart.get(str(product.id)))
            order = Order(customer=Customer(id=customer),
                          product=product,
                          price=product.price,
                          address=address,
                          phone=phone,
                          quantity=cart.get(str(product.id)))
            order.save()
            amount += order.price
            print(amount)
        request.session['cart'] = {}
        paytmParams = dict()
        
        paytmParams["body"] = {
            "requestType"   : "Payment",
            "mid"           : "YOUR_MID_HERE",
            "websiteName"   : "WEBSTAGING",
            "orderId"       : "ORDERID_98765",
            "callbackUrl"   : "https://localhotst/handlepayment",
            "txnAmount"     : {
                "value"     : "1.00",
                "currency"  : "INR",
            },
            "userInfo"      : {
                "custId"    : "CUST_001",
            },
        }

        # Generate checksum by parameters we have in body
        # Find your Merchant Key in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys 
        checksum = paytmchecksum.generateSignature(json.dumps(paytmParams["body"]), "YOUR_MERCHANT_KEY")

        paytmParams["head"] = {
            "signature"    : checksum
        }

        post_data = json.dumps(paytmParams)

        # for Staging
        url = "https://securegw-stage.paytm.in/theia/api/v1/initiateTransaction?mid=YOUR_MID_HERE&orderId=ORDERID_98765"

        # for Production
        # url = "https://securegw.paytm.in/theia/api/v1/initiateTransaction?mid=YOUR_MID_HERE&orderId=ORDERID_98765"
        
        response = request.post(url, data = post_data, headers = {"Content-type": "application/json"}).json()
        print(response)
        return render(request, 'paymenthandler.html' ,{'param_dict': paytmParams})
        

        
    @csrf_exempt
    def handlepayment(request):
        paystat = 'done'
        return render(request, "paymentstatus.html", {"paystat": paystat})

