from collections import namedtuple
from django.contrib.auth import login
from django.urls import path
from django.views.generic.base import TemplateView
from coffee_shop import views
from coffee_shop.models import Order

app_name = 'coffee_shop'
urlpatterns = [
    path('', views.home_page, name="home-page"),
    path('products/', views.ProductListView.as_view(template_name="coffee_shop/products.html", paginate_by=5), name='products'),
    path('login/', views.login, name="login"),
    path('products/<int:pk>', views.product_detail,name='product_detail'),
    path('product/add-to-cart/<int:pk>',views.add_to_cart, name='add-to-cart'),
    path('product/reduce-from-cart/<int:pk>',views.reduce_from_cart, name='reduce-from-cart'),
    path('product/remove-from-cart/<int:pk>',views.remove_from_cart, name='remove-from-cart'), 
    path('product/increase-from-cart/<int:pk>', views.increase_from_cart, name='increase-from-cart'),
    path('check-out/', views.check_out, name='check-out'),
    ############################## Management view ############################
    path('manage/create-staff-account/', views.create_staff_account, name = 'create_staff_account'),
    ###### Products #######
    path('manage/products/', views.ProductListView.as_view(template_name="manage/product_list.html"), name="product_list"),
    path('manage/products/add-product/', views.ProductCreateView.as_view(template_name='manage/product_create.html'), name='add_product'),
    path('manage/product/edit-detail/<int:pk>', views.edit_product_detail, name='edit_product_detail'),
    path('manage/product/mark-deleted/<int:pk>', views.mark_product_deleted, name='mark_product_deleted'),
    path('manage/product/add-category/', views.CategoryCreateView.as_view(template_name="manage/category_create.html"), name="add_category"),
    path('manage/product/rename-category/<int:pk>', views.rename_category, name="rename-category"),
    ###### Orders ######
    path('manage/', views.manage_index, name = 'manage_index'),
    ###### List View ####
    path('manage/orders/', views.OrderListView.as_view(), name='order_list'),
    path('manage/orders/unconfirmed/', views.OrderListView.as_view(qs = Order.objects.filter(confirm=False, ordered=True).order_by('-ordered_date')), name='unconfirmed_order_list'),
    path('manage/orders/confirmed/', views.OrderListView.as_view(qs = Order.objects.filter(confirm=True, success=False).order_by('-ordered_date')), name='confirmed_order_list'),
    path('manage/orders/success/', views.OrderListView.as_view(qs = Order.objects.filter(success=True).order_by('-ordered_date')), name='success_order_list'),
    ###### Detail view ######
    path('manage/order/<int:pk>', views.OrderDetailView.as_view(template_name='manage/order_detail.html'), name='order_detail'),


    ###### Handling order #######
    path('manage/order/mark-confirm/<int:pk>', views.mark_confirm, name='order_mark_confirm'),
    path('manage/order/mark-success/<int:pk>', views.mark_success, name='order_mark_success'),
    path('manage/order/delete/<int:pk>', views.order_delete, name='order_delete'),
    # Sales #
    path('manage/sales/', views.sales, name='sales'),
    # Success message #
    path('manage/order-success-message/', views.order_success_message_edit, name="success-message-edit")
]   
