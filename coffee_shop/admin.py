from django.contrib import admin
from .models import Product, OrderProduct, Order, Category, Topping, SubCategory, StaffInfo, Company
# Register your models here.
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product)
admin.site.register(Topping)
admin.site.register(OrderProduct)
admin.site.register(Order)
admin.site.register(StaffInfo)
admin.site.register(Company)




