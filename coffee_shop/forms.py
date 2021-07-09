from django import forms
from django.forms.fields import DateField
from .models import Product, StaffInfo, Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
    class Meta():
        model = Category
        fields = ('name',)
        
class ProductForm(forms.ModelForm):
    description = forms.CharField(label='Mô tả', widget=forms.Textarea(attrs={'id': "description", "class": "control-form"}))
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
    class Meta():
        model = Product
        exclude = ('added_date', 'topping', 'sub_category', 'deleted')




    
     


class OrderForm(forms.Form):
    name = forms.CharField(max_length=50, required=True, label='Tên người đặt hàng')
    phone_number = forms.CharField(max_length=15, required=True, label='Số điện thoại:')
    address = forms.CharField(max_length=200, required=True, label='Địa chỉ nhận hàng')

    def __init__(self, *args, **kwargs):
            super(OrderForm, self).__init__(*args, **kwargs)
            for visible in self.visible_fields():
                visible.field.widget.attrs['class'] = 'form-control'
    




class StaffForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2'] 
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Tài khoản'
        self.fields['username'].label=''
        self.fields['username'].help_text='<div class="form-text text-muted"><small>Bắt buộc. Chỉ bao gôm ký tự chữ, số và các ký tự đặc biệt @/./+/-/_ .</small></div>'

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Mật khẩu'
        self.fields['password1'].label=''
        self.fields['password1'].help_text='<ul class="form-text text-muted small"><li>Mật khẩu của bạn cần ít nhất 6 ký tự.</li></ul>'

        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Xác nhận mật khẩu'
        self.fields['password2'].label=''
        self.fields['password2'].help_text=''

class StaffInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StaffInfoForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
                visible.field.widget.attrs['class'] = 'form-control'
                self.fields['phone_number'].required = False
    class Meta():
        model = StaffInfo
        fields = ('phone_number',)
        labels = {
            'phone_number': 'Số điện thoại'
        }


class ImageForm(forms.Form):
    image = forms.ImageField(required=False, label="Ảnh")

class DateInput(forms.DateInput):
    input_type = "date"


class DateForm(forms.Form):
    start_date = forms.DateField(widget=DateInput, label="Từ", required=True)
    end_date = forms.DateField(widget=DateInput, label="Đến", required=True)

    def __init__(self, *args, **kwargs):
            super(DateForm, self).__init__(*args, **kwargs)
            for visible in self.visible_fields():
                visible.field.widget.attrs['class'] = 'form-control'