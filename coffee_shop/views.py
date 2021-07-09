from json import encoder
from os import stat
from django.dispatch.dispatcher import NO_RECEIVERS
from django.http import JsonResponse, request
from django.core import serializers
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import TemplateView, CreateView, DetailView, ListView
from django.views.generic.edit import FormMixin
from django.urls import reverse
from django.utils import timezone
from .models import Category, OrderProduct, Product, Order, SubCategory, Topping, Company
from .forms import CategoryForm, ProductForm, OrderForm, StaffForm, StaffInfoForm, ImageForm, DateForm
from django.db.models.functions import TruncMonth
from django.db.models import Count, Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from ratelimit.decorators import ratelimit
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta, date
import json


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Create your views here.
################### Customer View ####################################

def products(request):
    sub_category = request.GET.get('sub_category')
    category_name = request.GET.get('category')
    sub_categories = None
    if sub_category is not None:
        product_list = Product.objects.filter(sub_category=sub_category, deleted=False).order_by('-added_date')
        category = Category.objects.filter(sub_categories__name=sub_category)[0]
        sub_categories = category.sub_categories.all()

    elif category_name is not None:
        product_list = Product.objects.filter(category__name=category_name, deleted=False).order_by('-added_date')
        category = get_object_or_404(Category, name=category_name)
        sub_categories = category.sub_categories.all()
    else:
         product_list = Product.objects.filter(deleted=False).order_by('-added_date')
         category = Category.objects.first()
         sub_categories = category.sub_categories.all()

    current_ip = get_client_ip(request)
    category_list = Category.objects.all()
    order_qs = Order.objects.filter(ip_address=current_ip, ordered=False)
    order = None
    if order_qs.exists():
        order = order_qs[0]
    return render(request, 'coffee_shop/products.html', context={'product_list': product_list, 'order': order, 'category_list': category_list, 'category': category, 'sub_categories': sub_categories, 'sub_category': sub_category})

def home_page(request):
    product_list = Product.objects.all()[:9]
    current_ip = get_client_ip(request)
    category_list = Category.objects.all()
    order_qs = Order.objects.filter(ip_address=current_ip, ordered=False)
    order = None
    if order_qs.exists():
        order = order_qs[0]
    return render(request, 'coffee_shop/home-page.html', context={'product_list': product_list, 'order': order, 'category_list': category_list})


def add_to_cart(request, pk):
    total_price = 0
    current_ip = get_client_ip(request)
    if request.is_ajax and request.method == "GET":
        product = get_object_or_404(Product, pk=pk)
        order_product_qs = OrderProduct.objects.filter(product=product, topping=None, ip_address=current_ip, ordered=False)
        if order_product_qs.exists():
            order_product = order_product_qs[0]
        else:
            order_product = OrderProduct.objects.create(product=product, ip_address=current_ip)
        order_qs = Order.objects.filter(ip_address=current_ip, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.products.filter(product__pk=product.pk).exists():
                order_product.quantity += 1
                order_product.save()
            else:
                order.products.add(order_product)

        else:
            order = Order.objects.create(ip_address=current_ip)
            order.products.add(order_product)
        total_price = order.get_total()
        data ={
            "total_price": total_price,
            "product_name": product.name,
        }
        # For sales statistic only
        return HttpResponse(json.dumps(data), content_type="application/json")
        # return HttpResponse(json.dumps(data), content_type='application/json')
    return redirect('coffee_shop:index')


def increase_from_cart(request, pk):
    order_product = get_object_or_404(OrderProduct, pk=pk)
   
    order = Order.objects.filter(ip_address=get_client_ip(request), ordered=False)[0]
    price = order_product.get_price() + order_product.get_one_product_price()
    total_price = order.get_total() + order_product.get_one_product_price()
    order_product.quantity += 1
    order_product.save()
    quantity = order_product.quantity



    return JsonResponse({'price': price, "quantity": quantity, "total_price": total_price, "difference": 1}, status=200)

def remove_from_cart(request, pk):
    order_product = get_object_or_404(OrderProduct, pk=pk)
    quantity = order_product.quantity
    order = Order.objects.filter(ip_address=get_client_ip(request), ordered=False)[0]
    total_price = order.get_total() - order_product.get_price()
    order_product.delete()
    if len(order.products.all()) == 0:
        order.delete()
    return JsonResponse({"total_price": total_price, "quantity": quantity}, status=200)

def reduce_from_cart(request, pk):
    order_product = get_object_or_404(OrderProduct, pk=pk)
    order = Order.objects.filter(ip_address=get_client_ip(request), ordered=False)[0]
    if order_product.quantity - 1 == 0:
        quantity = order_product.quantity
        price = order_product.get_price()
        total_price = order.get_total()
        difference = 0
    else:
        price = order_product.get_price() - order_product.get_one_product_price()
        total_price = order.get_total() - order_product.get_one_product_price()
        order_product.quantity -= 1
        order_product.save()
        quantity = order_product.quantity    
        difference = -1
    return JsonResponse({'price': price, "quantity": quantity, "total_price": total_price, "difference": difference}, status=200)




@ratelimit(key='ip', rate='1/h', method=ratelimit.UNSAFE)
def check_out(request):
    current_ip = get_client_ip(request)
    order_qs = Order.objects.filter(ip_address=current_ip, ordered=False)
    category_list = Category.objects.all()
    order = None
    if order_qs.exists():
        order = order_qs[0]
    if request.method == 'POST':
        if order == None:
            return render(request, "coffee_shop/empty-cart.html")
        form = OrderForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            address = form.cleaned_data['address']
            order_qs = Order.objects.filter(ip_address=current_ip, ordered=False)
            if order_qs.exists():
                order = order_qs[0]
                order.name = name
                order.phone_number = phone_number
                order.address = address
                order.ordered = True
                order.ordered_date = timezone.now()
                product_list = order.get_ordered_products()
                for product in product_list:
                    product.ordered = True
                    product.save()
                order.save()
            company = Company.objects.all()[0]
            return render(request, "coffee_shop/success-message.html", context={"company": company})
    else:
        form = OrderForm()
    return render(request, 'coffee_shop/checkout-page.html', context={'form': form, 'order': order, 'ip': current_ip, 'category_list': category_list})

################### End - Customer View ####################################


##################### Manager view #############################
@login_required
def manage_index(request):
    category_list = Category.objects.all()
    return render(request, 'manage/index.html', context={'category_list': category_list})


#### Add Category #######
class CategoryCreateView(LoginRequiredMixin, CreateView):
    form_class = CategoryForm
    model = Category

    def get_success_url(self):
        return reverse('coffee_shop:product_list')
    
    def get_context_data(self, *args, **kwargs):
        context = super(CategoryCreateView, self).get_context_data(*args, **kwargs)
        category_list = Category.objects.all()
        context['category_list'] = category_list
        return context

def rename_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        rename_category = request.POST.get('rename_category')
        category.name = rename_category
        category.save()


    return render(request, "manage/category-edit.html")

######## PRoduct View    #######


class ProductCreateView(LoginRequiredMixin, CreateView):
    form_class = ProductForm
    model = Product
    def get_success_url(self):
        return reverse('coffee_shop:product_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, *args, **kwargs):
        context = super(ProductCreateView, self).get_context_data(*args, **kwargs)
        category_list = Category.objects.all()
        context['category_list'] = category_list
        return context

def edit_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    category_list = Category.objects.all()
    sub_categories = product.category.sub_categories.all()
    if request.method == "POST":
        product.name = request.POST.get('name')
        category_name = request.POST.get('category')
        category = Category.objects.get(name=category_name)
        product.category = category
        product.sub_category = request.POST.get('sub_category')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.save()
        form = ImageForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            if form.cleaned_data['image']:
                product.image = request.FILES['image']
                product.replace_image()
                product.save()
    else:
        form = ImageForm()
    
    return render(request, 'manage/product-edit.html', context = {'product': product, 'form': form, 'category_list': category_list, 'sub_categories': sub_categories})



def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    current_ip = get_client_ip(request)
    topping_list = product.topping.all()
    category_list = Category.objects.all()
    order_qs = Order.objects.filter(ip_address= current_ip, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
    else:
        order = None
    if request.is_ajax and request.method == 'POST':
        demand_quantity = int(request.POST.get("demand_quantity"))
        topping_pk_list = request.POST.getlist('object_list')
        if topping_pk_list:
            topping_list = Topping.objects.filter(pk__in=topping_pk_list)

        #     # Get product need to add to cart
            order_product_qs = OrderProduct.objects.filter(product=product, ip_address=current_ip, ordered=False)
            for topping in topping_list:
                order_product_qs = order_product_qs.filter(topping=topping)
            if order_product_qs.exists():
                order_product = None
                for temp_order_product in order_product_qs:
                    if len(temp_order_product.topping.all()) == len(topping_list):
                        order_product = temp_order_product
                if order_product is None:
                    order_product = OrderProduct.objects.create(product=product, ip_address=current_ip)
                    for topping in topping_list:
                        order_product.topping.add(topping)
                    order_product.save()
            else:
                order_product = OrderProduct.objects.create(product=product, ip_address=current_ip)
                for topping in topping_list:
                    order_product.topping.add(topping)
                order_product.save()
            # check if order exists to add to cart
            if order:
                if order.products.filter(pk=order_product.pk).exists():
                    order_product.quantity += demand_quantity
                    order_product.save()
                else:
                    order_product.quantity = demand_quantity
                    order.products.add(order_product)
                    order.save()
            else:
                order = Order.objects.create(ip_address=current_ip)
                order_product.quantity = demand_quantity
                order_product.save()
                order.products.add(order_product)
        else:
            order_product_qs = OrderProduct.objects.filter(product=product, topping=None, ordered=False, ip_address=current_ip)
            if order_product_qs.exists():
                order_product = order_product_qs[0]
            else:
                order_product = OrderProduct.objects.create(product=product, ip_address=current_ip)

            if order:
                if order.products.filter(product=product, topping=None, ordered=False):
                    order_product.quantity += demand_quantity
                    order_product.save()
                else:
                    order_product.quantity = demand_quantity
                    order_product.save()
                    order.products.add(order_product)
            else:
                order = Order.objects.create(ip_address=current_ip)
                order_product.quantity = demand_quantity
                order_product.save()
                order.products.add(order_product)
        total_price = order.get_total()
        data = {
            "total_price": total_price,
            "product_name": order_product.get_name(),
        }
        return HttpResponse(json.dumps(data), content_type="application/json")

                
       

    return render(request, 'coffee_shop/product_detail.html', context={'product': product, 'order': order, 'category_list': category_list, 'topping_list': topping_list})
    



class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    paginate_by = 5
    qs = Product.objects.filter(deleted=False).order_by('-added_date')

    # def post(self, request, *args, **kwargs):
    #     sub_category_name = request.POST.get('sub_category')
    #     if sub_category_name != "":
    #         sub_category, created = SubCategory.objects.get_or_create(name=sub_category_name)
    #         category_name = request.POST.get('category')
    #         category, created = Category.objects.get_or_create(name=category_name)
    #         category.sub_categories.add(sub_category)
    #         return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
    #     assigned_sub_category = request.POST.get('assigned_sub_category')
    #     object_list_pk = request.POST.getlist('object_list')
    #     if object_list_pk is not None:
    #         product_list = Product.objects.filter(pk__in=object_list_pk)
    #         for product in product_list:
    #             product.sub_category = assigned_sub_category
    #             product.save()
    #         return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

    #     return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
       

    def get_queryset(self):
        return self.qs

    def get_context_data(self, *args, **kwargs):  
        context = super(ProductListView, self).get_context_data(*args, **kwargs)
        sub_category_name = self.request.GET.get('sub_category')
        category_list = Category.objects.all()
        category_name = self.request.GET.get('category')
        if sub_category_name is not None:
            category = Category.objects.filter(sub_categories__name=sub_category_name)[0]
            context['product_list']= Product.objects.filter(sub_category=sub_category_name, deleted=False).order_by('-added_date')
            context['sub_category_name'] = sub_category_name
            context['sub_categories'] = category.sub_categories.all()
            context['category'] = category
        elif category_name is not None:
            category = get_object_or_404(Category, name=category_name)
            context['product_list']= Product.objects.filter(category__name=category_name, deleted=False).order_by('-added_date')
            context['sub_categories'] = category.sub_categories.all()
            context['category'] = category
        context['category_list'] = category_list
        return context

def mark_product_deleted(request, pk):
    if request.is_ajax:
        product = get_object_or_404(Product, pk=pk)
        product.deleted = True
        product.save()

    return JsonResponse({'nothing': ""}, status=200)



# Order View #################3


class OrderDetailView(DetailView):
    model = Order

    def get_context_data(self, *args, **kwargs):
        context = super(OrderDetailView, self).get_context_data(*args, **kwargs)
        category_list = Category.objects.all()
        context['category_list'] = category_list
        return context



class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    paginate_by = 100
    qs = Order.objects.filter(ordered=True).order_by('-ordered_date')
    template_name = 'manage/order_list.html'
    def post(self, request, *args, **kwargs ):
        order_pk_list = request.POST.getlist('object_list')
        if order_pk_list is not None:
            order_list = Order.objects.filter(pk__in=order_pk_list)
            status = request.POST.get('status')
            if status == "success":
                for order in order_list:
                    if not order.success:
                        company = Company.objects.all()[0]
                        order.confirm = True
                        order.success = True
                        order.total = order.get_total()
                        order.save()
                        product_list = order.products.all()
                        for product in product_list:
                            product.product.category.sales += product.get_price()
                            product.product.category.save()
                            company.sales += product.get_price()
                            company.orders += 1
                            company.save()
            elif status == "confirmed":
                for order in order_list:
                    if order.success:
                        company = Company.objects.all()[0]
                        product_list = order.products.all()
                        for product in product_list:
                            product.product.category.sales -= product.get_price()
                            product.product.category.save()
                            company.sales -= product.get_price()
                            company.orders -= 1
                            company.save()
                    order.confirm = True
                    order.success = False
                    order.save()
            elif status == "delete":
                for order in order_list:
                    product_list = order.products.all()
                    if order.success:
                        company = Company.objects.all()[0]
                        for product in product_list:
                            product.product.category.sales -= product.get_price()
                            product.product.category.save()
                            company.sales -= product.get_price()
                            company.orders -= 1
                            company.save()
                            product.delete()
                    else:
                        for product in product_list:
                            product.delete()
                    order.delete()

        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


            

    def get_queryset(self):
        return self.qs
        
    def get_context_data(self, *args, **kwargs):
        context = super(OrderListView, self).get_context_data(*args, **kwargs)
        category_list = Category.objects.all()
        today_orders = Order.objects.filter(ordered_date__gte=date.today(), success=True)
        total_income_today = 0
        for today_order in today_orders:
            total_income_today += today_order.get_total()
        context['category_list'] = category_list
        context['total_income_today'] = total_income_today
        if today_orders:
            context['orders_len'] = len(today_orders)
        return context

def mark_confirm(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.confirm = True
    order.save()
    return redirect('coffee_shop:order_detail', pk=order.pk)



def mark_success(request, pk):
    company = Company.objects.all()[0]
    order = get_object_or_404(Order, pk=pk)
    order.confirm= True
    order.success = True
    product_list = order.products.all()
    for product in product_list:
        product.product.category.sales += product.get_price()
        product.product.category.save()
        company.sales += product.get_price()
        company.orders += 1
        company.save()

    order.total = order.get_total()
    order.save()
    return redirect('coffee_shop:order_list')


def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    product_list = order.products.all()
    if order.success:
        company = Company.objects.all()[0]
        for product in product_list:
            product.product.category.sales -= product.get_price()
            product.product.category.save()
            company.sales -= product.get_price()
            company.orders -= 1
            company.save()
            product.delete()
    else:
        for product in product_list:
            product.delete()
    order.delete()
    return redirect('coffee_shop:order_list')


@login_required
def create_staff_account(request):
    category_list = Category.objects.all()
    if not request.user.is_superuser:
        return HttpResponse("Không thể tạo tài khoản nhân viên với tài khoản hiện tại")
    registered = False
    if request.method == 'POST':

        # Get info from "both" forms
        # It appears as one form to the user on the .html page
        staff_form = StaffForm(data=request.POST)
        staff_info_form = StaffInfoForm(data=request.POST)

        # Check to see both forms are valid
        if staff_form.is_valid() and staff_info_form.is_valid():

            # Save User Form to Database
            staff = staff_form.save()

            # Hash the password
            staff.set_password(staff.password)
            staff.is_staff = True

            # Update with Hashed password
            staff.save()

            # Now we deal with the extra info!

            # Can't commit yet because we still need to manipulate
            staff_info = staff_info_form.save(commit=False)

            # Set One to One relationship between
            # UserForm and UserProfileInfoForm
            staff_info.user = staff

            # Check if they provided a profile picture
            # Now save model
            staff_info.save()

            # Registration Successful!
            registered = True

        else:
            # One of the forms was invalid if this else gets called.
            print(staff_form.errors, staff_info_form.errors)

    else:
        # Was not an HTTP post so we just render the forms as blank.
        staff_form = StaffForm(initial={'is_staff': True})
        staff_info_form = StaffInfoForm()

    # This is the render and context dictionary to feed
    # back to the registration.html file page.
    return render(request, 'manage/create-staff-account.html', {'staff_form': staff_form, 'staff_info_form': staff_info_form, 'registered': registered, 'category_list': category_list})


# Sales

def sales(request):
    category_list = Category.objects.all()
    company = Company.objects.all()[0]
    filter_range = request.GET.get('filter_range')
    if request.method == "POST":
        form = DateForm(request.POST)
        if form.is_valid():
            total_sales = 0
            sales_list = []
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            order_list = Order.objects.filter(success=True, ordered_date__gte=start_date, ordered_date__lte=end_date + timedelta(days=1))
            order_count = len(order_list)
            for order in order_list:
                total_sales += order.total
            for category in category_list:
                sum = 0
                qs_list = []
                for order in order_list:
                    qs_list.append(order.products.filter(product__category=category))
                for qs in qs_list:
                    if qs.exists():
                        for product in qs:
                            sum += product.get_price()
                sales_list.append(sum)
            for i in range(len(sales_list)):
                category_list[i].sales = sales_list[i]
            company.orders = order_count
            company.sales = total_sales
    else:
        form = DateForm
        if filter_range is not None:
            total_sales = 0
            sales_list = []
            if filter_range == "week":
                order_list = Order.objects.filter(success=True, ordered_date__gte=date.today() - timedelta(days=7))
            elif filter_range == "month":
                order_list = Order.objects.filter(success=True, ordered_date__gte=date.today() - timedelta(days=30))
            elif filter_range == "year":
                order_list = Order.objects.filter(success=True, ordered_date__gte=date.today() - timedelta(days=365))
            
            order_count = len(order_list)
            for order in order_list:
                total_sales += order.total
            for category in category_list:
                sum = 0
                qs_list = []
                for order in order_list:
                    qs_list.append(order.products.filter(product__category=category))
                for qs in qs_list:
                    if qs.exists():
                        for product in qs:
                            sum += product.get_price()
                sales_list.append(sum)
            for i in range(len(sales_list)):
                category_list[i].sales = sales_list[i]
            company.orders = order_count
            company.sales = total_sales
    # order_list_test = Order.objects.filter(success=True).annotate(month=TruncMonth("ordered_date")).values('month').annotate(c=Count('id')).annotate(sum=Sum('total'))
    return render(request, 'manage/sales.html', context={"category_list": category_list, "company": company, "filter_range": filter_range, "form": form})




def order_success_message_edit(request):
    company = Company.objects.all()[0]
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("message")
        company.success_order_title = title
        company.success_order_message = description
        company.save()
        print(company.success_order_title)
    
    return render(request, "manage/success-message-edit.html", context={"company": company})