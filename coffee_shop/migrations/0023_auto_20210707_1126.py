# Generated by Django 3.2.4 on 2021-07-07 04:26

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('coffee_shop', '0022_auto_20210706_0022'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='success_order_title',
            field=models.CharField(default='Đặt hàng thành công', max_length=200),
        ),
        migrations.AlterField(
            model_name='order',
            name='ordered_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 7, 7, 4, 26, 54, 632059, tzinfo=utc)),
        ),
    ]
