from io import open_code
from django.db import models
from django.db.models.fields import CharField, IntegerField, TextField
from django.db.models.fields.related import ManyToManyField
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
# Receive the pre_delete signal and delete the file associated with the model instance.
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

# Create your models here.
class Company(models.Model):
    sales = IntegerField(default = 0)
    orders = IntegerField(default = 0)
    success_order_title = CharField(max_length=200, default="Đặt hàng thành công")
    success_order_message = TextField(blank=True)


class SubCategory(models.Model):
    name = CharField(max_length=100, verbose_name="Tên loại cụ thể", unique=True)
    def __str__(self):
        return self.name


class Category(models.Model):
    name = CharField(max_length=100, verbose_name="Tên loại", unique=True)
    sub_categories = ManyToManyField(SubCategory, blank=True, verbose_name="Loại cụ thể")
    sales = IntegerField(default = 0)
    def get_rename_url(self):
        return reverse('coffee_shop:rename-category', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class Topping(models.Model):
    description = models.CharField(max_length=50,verbose_name="Mô tả" )
    price = models.IntegerField(verbose_name="Giá")
    def __str__(self):
        return self.description


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name=('Tên sản phẩm'))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=False, default=True, verbose_name="Loại")
    sub_category = models.CharField(max_length=100, blank=True, verbose_name=("Loại cụ thể"))
    topping = ManyToManyField(Topping, verbose_name="Topping", blank=True)
    description = models.TextField(blank=True, verbose_name=('Mô tả'))
    price = models.IntegerField(verbose_name=('Giá'))
    image = models.ImageField(upload_to='images/%Y/%m/%d/', verbose_name=('Ảnh'))
    added_date = models.DateTimeField(default=timezone.now)
    deleted = models.BooleanField(default=False)
    def replace_image(self, *args, **kwargs):
        # delete old file when replacing by updating the file
        try:
            this = Product.objects.get(pk=self.pk)
            if this.image != self.image:
                this.image.delete(save=False)
        except: pass
        super(Product, self).save(*args, **kwargs)
    
    def add_option(self):
        return reverse('coffee_shop:add_product_option', kwargs={'pk': self.pk})

    def get_edit_product_detail_url(self):
        return reverse('coffee_shop:edit_product_detail', kwargs={'pk': self.pk})

    def get_mark_deleted_url(self):
        return reverse('coffee_shop:mark_product_deleted', kwargs={'pk': self.pk})

    def get_detail_view_url(self):
        return reverse('coffee_shop:product_detail', kwargs={'pk': self.pk})

    def get_add_to_cart_url(self):
        return reverse('coffee_shop:add-to-cart', kwargs={'pk': self.pk})

    def get_remove_from_cart_url(self):
        return reverse('coffee_shop:remove-from-cart', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class OrderProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    topping = ManyToManyField(Topping, blank=True)
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=50)
    
    def get_one_product_price(self):
        sum = self.product.price
        topping_list = self.topping.all()
        if topping_list:
            for topping in topping_list:
                sum += topping.price    
        return sum

    def get_price(self):
        sum = self.product.price
        topping_list = self.topping.all()
        if topping_list:
            for topping in topping_list:
                sum += topping.price    
        return sum * self.quantity
            
    def get_remove_from_cart_url(self):
        return reverse('coffee_shop:remove-from-cart', kwargs={'pk': self.pk})

    def get_reduce_from_cart_url(self):
        return reverse('coffee_shop:reduce-from-cart', kwargs={'pk': self.pk})
    
    def get_increase_from_cart_url(self):
        return reverse('coffee_shop:increase-from-cart', kwargs={'pk': self.pk})
    def get_topping_list(self):
        return self.topping.all()
    
    def get_original_name(self):
        return self.product.name
    
    def get_name(self):
        str = self.product.name
        if self.topping.all().exists():
            str += "("
            for topping in self.topping.all():
                if topping == self.topping.all().last():
                    str += topping.description
                else:
                    str += topping.description
                    str += " + "
            str += ")"
        return  str


    def __str__(self) -> str:
        str = f'{self.quantity} {self.product.name}'
        if self.topping.all().exists():
            str += "("
            for topping in self.topping.all():
                if topping == self.topping.all().last():
                    str += topping.description
                else:
                    str += topping.description
                    str += " + "
            str += ")"
        return  str


class Order(models.Model):
    name = models.CharField(max_length=40)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    products = models.ManyToManyField(OrderProduct)
    ip_address = models.CharField(max_length=50)
    ordered = models.BooleanField(default=False)
    confirm = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    ordered_date = models.DateTimeField(default=timezone.now())
    total = IntegerField(default = 0)
    handler = models.CharField(max_length=100, blank=True)
    
    def get_mark_confirm_url(self):
        return reverse('coffee_shop:order_mark_confirm', kwargs={'pk': self.pk})

    def get_mark_shipping_url(self):
        return reverse('coffee_shop:order_mark_shipping', kwargs={'pk': self.pk})
    
    def get_mark_success_url(self):
        return reverse('coffee_shop:order_mark_success', kwargs={'pk': self.pk})
    
    def get_delete_url(self):
        return reverse('coffee_shop:order_delete', kwargs={'pk': self.pk})

    def get_unmark_cancel_url(self):
        return reverse('coffee_shop:order_unmark_cancel', kwargs={'pk': self.pk})

    def get_all_items_quantity(self):
        n = 0
        order_products = self.products.all()
        if order_products.exists():
            for order_product in order_products:
                n += order_product.quantity
        return n

    def get_total(self):
        price = 0
        for product in self.products.all():
            price += product.get_price()
        return price
    
    def get_ordered_products(self):
        return self.products.all()
    
    def get_detail_view_url(self):
        return reverse('coffee_shop:order_detail', kwargs={'pk': self.pk})

    def __str__(self) -> str:
        return self.name


class StaffInfo(models.Model):

    # Create relationship (don't inherit from User!)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    # Add any additional attributes you want
    phone_number = models.IntegerField()
    def __str__(self):
        # Built-in attribute of django.contrib.auth.models.User !
        return self.user.username

# Receive the pre_delete signal and delete the file associated with the model instance.

@receiver(pre_delete, sender=Product)
def product_delete(sender, instance, **kwargs):
    instance.image.delete(False)