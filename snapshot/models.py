from django.db import models
from django.shortcuts import get_object_or_404



class Commodity(models.Model):
    """
    >>> from snapshot.models import *
    >>> c = Commodity(order_id="746823468", commodity_id="86346142", name="soccer ball", seller_name="zidan")
    >>> cs1 = Commodity_SKU(order_id="746823468", commodity_id="86346142", field_name="color", field_value="white")
    >>> cs1.save()
    >>> cs2 = Commodity_SKU(order_id="746823468", commodity_id="86346142", field_name="size", field_value=12)
    >>> cs2.save()
    >>> 
    >>> c.get_sku_value('color')
    u'white'
    >>> c.get_sku_value('size')
    u'12'
    >>> c.get_skus()
    [(u'color', u'white'), (u'size', u'12')]


    """
    order_id = models.CharField(max_length=18)
    commodity_id = models.CharField(max_length=18)
    name = models.CharField(max_length=64) 
    seller_name = models.CharField(max_length=125, null=True, blank=True, verbose_name='seller name')
    seller_id = models.CharField(max_length=18)
    seller_qq = models.CharField(max_length=32)
    seller_phone = models.CharField(max_length=18, blank=True, verbose_name='seller phone')
    seller_addr = models.CharField(max_length=256, null=True, blank=True, verbose_name='seller address')    
    pic = models.CharField(max_length=64)  
    purchase_num = models.SmallIntegerField(null=True, blank=True, default=1)
    commodity_sku_id = models.CharField(max_length=18, null=True, blank=True)

    class Meta:
        #TODO:abstract?
        #abstract = True 
        unique_together = (('order_id', 'commodity_id'),)

    def get_commodity_type(self):
        try:
           self.service_commodity
           return 'service_commodity'
        except:
           return 'product_commodity'    


    def get_sku_value(self, field_name):
        #return None if find nothing
        try: 
            cs = Commodity_SKU.objects.get(order_id=self.order_id, commodity_id=self.commodity_id, field_name=field_name)
            return cs.field_value
        except Commodity_SKU.DoesNotExist:
            return None
    

    def get_skus(self):
        """
        
        """
        return Commodity.get_sku_class().objects.filter(order_id=self.order_id, commodity_id=self.commodity_id).values_list("field_name", "field_value")


    @classmethod
    def get_sku_class(cls):
        return Commodity_SKU


#Commodity_SKU is used to store unknown fields. So for price, unit_price, original_price, service_times, although they belong to
#sku values, we put them here since they are common for all service commodities. 
#TODO:add service_sku_name, and thus don't save it as name in sku
class Service_Commodity(Commodity):
    valid_date_start = models.DateField(null=True, blank=True) 
    valid_date_end = models.DateField(null=True, blank=True)
    price = models.DecimalField(null=True, max_digits=9, decimal_places=2, verbose_name='service price') 
    unit_price = models.DecimalField(null=True, max_digits=9, decimal_places=2, verbose_name='service unit price') 
    original_price = models.DecimalField(null=True, max_digits=9, decimal_places=2, verbose_name='service original price') 
    service_times = models.SmallIntegerField(null=True, blank=True)  
    platform_percentage = models.SmallIntegerField(null=True, blank=True)    
    support_anytime_refund = models.BooleanField(default=True)  #TODO:default True for now
    support_expiration_refund = models.BooleanField(default=True) #TODO:default True for now 
    service_addr = models.CharField(max_length=256, null=True, blank=True, verbose_name='service address')    
    sale_num = models.SmallIntegerField(null=True, blank=True) 
    






class Product_Commodity(Commodity):
    price = models.DecimalField(null=True, max_digits=9, decimal_places=2, verbose_name='product price')     
    service_supplier_name = models.CharField(max_length=125, null=True, blank=True, verbose_name='service supplier name')
    service_supplier_id = models.CharField(max_length=18)    
    distributor_percentage = models.SmallIntegerField(null=True, blank=True)     
    platform_percentage = models.SmallIntegerField(null=True, blank=True)    
    support_7day_refund = models.BooleanField(default=False)  
    


# COMMODITY_TYPE_CHOICES = (
#         ('P', _('Product')),('S', _('Service')),
#     )

class Commodity_SKU(models.Model):
    #commodity_type = models.CharField(max_length=1, choices=ORDER_STATE_CHOICES) #remove this? TODO:
    order_id = models.CharField(max_length=18)
    commodity_id = models.CharField(max_length=18)
    field_name = models.CharField(max_length=24)  
    field_value = models.CharField(max_length=64)

    class Meta:
       unique_together = (("order_id", "commodity_id", "field_name"),)  
