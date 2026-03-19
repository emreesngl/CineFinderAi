import markdown
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(is_safe=True)
@stringfilter
def convert_markdown(value):
    """Markdown metnini HTML'e dönüştürür."""
    # Güvenlik için escape_html=True kullanılabilir ancak Gemini'den gelen
    # basit markdown (bold, list) için genellikle gereksizdir.
    # markdown.markdown(...) çeşitli uzantıları da destekler.
    html = markdown.markdown(value)
    return mark_safe(html) 