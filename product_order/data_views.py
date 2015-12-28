
import json
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from product_order.models import Order_State_Machine


#TODO: think of making this restful
def get_actions(request, role):
    c_state = request.REQUEST.get('current_state','')
    ras = Order_State_Machine.get_role_actions(c_state)
    actions = ras.get(role, None)
    return HttpResponse(json.dumps(actions, "application/json"))



