from django.conf.urls import patterns, include, url

from service_order import views, data_views

urlpatterns = patterns('',

     url(r'^$', views.index),
     url(r'^order_state_machine/$', views.order_state_machine),
     url(r'^make_order/$', views.make_order),
     url(r'^make_order2/$', views.make_order2),
     url(r'^make_order3/$', views.make_order3),
     url(r'^create_order/$', views.create_order),
     url(r'^view_refund_sheet/$', views.view_refund_sheet),
     url(r'^data/validate_code/', data_views.validate_code),
     

)
