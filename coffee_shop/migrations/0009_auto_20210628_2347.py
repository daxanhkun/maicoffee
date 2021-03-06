# Generated by Django 3.2.4 on 2021-06-28 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coffee_shop', '0008_auto_20210628_2206'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sub_category',
            field=models.CharField(blank=True, max_length=100, verbose_name='Loại cụ thể'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Tên loại'),
        ),
        migrations.AlterField(
            model_name='category',
            name='sub_categories',
            field=models.ManyToManyField(blank=True, to='coffee_shop.SubCategory', verbose_name='Loại cụ thể'),
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Tên loại cụ thể'),
        ),
    ]
