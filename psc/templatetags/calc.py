from django import template

register = template.Library()

@register.filter(name='percentage')  
def percentage(fraction, population):
    try:
        return "%.2f%%" % ((float(fraction) / float(population)) * 100)
    except ValueError:
        return ''

