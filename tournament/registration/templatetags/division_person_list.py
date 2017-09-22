from django import template

register = template.Library()

@register.inclusion_tag('registration/division_person_list.html')
def division_person_list(people):
    return {'people': people}