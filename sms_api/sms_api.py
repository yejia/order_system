#!/usr/bin/env python

import sys
# from settings import BASE_DIR
import os

# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(base_dir)

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "order_system.settings") 
# import django
# django.setup()



import django

from django.core import management
import order_system
import order_system.settings as settings
management.setup_environ(settings)





from order_system.settings import SMS_USER, SMS_PASS, SMS_PROID, SMS_X_URL


class Mobile_Msg_Client(object):
    """
     Client for sending mobile msg
    """
    def __init__(self, username=SMS_USER, passwd=SMS_PASS, product_id=SMS_PROID):        
        self.username = username
        self.passwd = passwd
        self.product_id = product_id
  

    def sendXSms(self, mobile, content):
        #Fill your own sms sending code above following your service provider's documentation
        # data = {'username':self.username,
        #         'passwd':self.passwd,
        #         'mobile':mobile,
        #         'content':content,
        #         'dstime':dstime,
        #         'product_id':self.product_id,
        #         'xh':xh
        #         }
        # try:            
        #     r = requests.get(SMS_X_URL, data=data, headers={}, timeout=90)
        # except Exception as inst:
        #      print type(inst)    
        #      print inst.args     
        #      print inst          
        
        # return r.json()
        
        return 'Sent successfully!'
        

        
if __name__ == "__main__":        
    mobile_num = sys.argv[1]
    cl = Mobile_Msg_Client()        
    msg="hello world!"    
    print 'msg sent, and return is:', cl.sendXSms('mobile_num', msg)
    

