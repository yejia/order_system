
import json
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from service_order.models import Order_Item_Rel


#TODO: 
#@csrf_protect
def validate_code(request):
    code = request.POST.get('code')
    item_id = request.POST.get('item_id')
    item = get_object_or_404(Order_Item_Rel, id=item_id)
    msg = item.validate(code)    
    return HttpResponse(json.dumps({'code':code,'msg':msg}, "application/json"))



