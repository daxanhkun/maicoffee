# Generated by Django 3.2.4 on 2021-06-30 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coffee_shop', '0013_product_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Tên sản phẩm'),
        ),
    ]
