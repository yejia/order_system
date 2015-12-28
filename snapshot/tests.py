"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from snapshot.models import Service_Commodity, Product_Commodity, Commodity



class Service_Commodity_Test(TestCase):

    def setUp(self):

        service_dict = {
            'commodity_id': '1256734536',
            'name': 'tudou fighting',
            'valid_date_start': '2014-03-03',
            'valid_date_end': '2014-08-03',
            'price': 10.20,
            'unit_price': 1.00,
            'seller_name': 'tudou',
            'seller_id': '734897941',
            'platform_percentage': 5,
            'support_anytime_refund': 0,
            'support_expiration_refund': 0,
            'service_addr': 'beijing tudou hutong #23',
        }
        sc = Service_Commodity(**service_dict)
        sc.save()
        self.commodity_id = sc.commodity_id


    def test_get_commodity_type(self):
        c = Commodity.objects.get(commodity_id=self.commodity_id)
        #print c.get_commodity_type()
        self.assertTrue(c.get_commodity_type(), 'service_commodity')


class Product_Commodity_Test(TestCase):
    def setUp(self):
        service_dict = {
            'commodity_id': '7654895124',
            'name': 'peapod souce',
            'purchase_num': 1,
            'price': 110.20,
            'service_supplier_name': 'smurf meimei',
            'service_supplier_id': '278786743',
            'seller_name': 'smurf congcong',
            'seller_id': '57663632',
            'distributor_percentage': 12,
            'platform_percentage': 6,
            'support_7day_refund': 0,
        }

        pc = Product_Commodity(**service_dict)
        pc.save()
        self.commodity_id = pc.commodity_id

    def test_get_commodity_type(self):
        c = Commodity.objects.get(commodity_id=self.commodity_id)
        #print c.get_commodity_type()
        self.assertTrue(c.get_commodity_type(), 'product_commodity')
