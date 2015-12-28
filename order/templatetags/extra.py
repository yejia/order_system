
import django
from django import template
from order_system import settings

register = template.Library()


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


#probably from http://stackoverflow.com/questions/14481205/catching-templatedoesnotexist-in-django
@register.simple_tag(takes_context=True)
def include_fallback(context, *template_choices):
    t = django.template.loader.select_template(template_choices)
    return t.render(context)    