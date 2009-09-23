from django import template
from django.core.cache import cache
from compressor import CssCompressor, JsCompressor
from compressor.conf import settings


register = template.Library()

class CompressorNode(template.Node):
    def __init__(self, nodelist, kind=None, xhtml=False, output_filename=None):
        self.nodelist = nodelist
        self.kind = kind
        self.xhtml = xhtml
        self.output_filename = output_filename

    def render(self, context):
        content = self.nodelist.render(context)
        if self.kind == 'css':
            compressor = CssCompressor(content, xhtml=self.xhtml, output_filename=self.output_filename)
        if self.kind == 'js':
            compressor = JsCompressor(content, xhtml=self.xhtml)
        in_cache = cache.get(compressor.cachekey)
        if in_cache: 
            return in_cache
        else:
            output = compressor.output()
            cache.set(compressor.cachekey, output, 86400) # rebuilds the cache once a day if nothing has changed.
            return output

@register.tag
def compress(parser, token):
    """
    Compresses linked and inline javascript or CSS into a single cached file.

    Syntax::

        {% compress <js/css> %}
        <html of inline or linked JS/CSS>
        {% endcompress %}

    Examples::

        {% compress css %}
        <link rel="stylesheet" href="/media/css/one.css" type="text/css">
        <style type="text/css">p { border:5px solid green;}</style>
        <link rel="stylesheet" href="/media/css/two.css" type="text/css">
        {% endcompress %}

    Which would be rendered something like::

        <link rel="stylesheet" href="/media/CACHE/css/f7c661b7a124.css" type="text/css">

    or::

        {% compress js %}
        <script src="/media/js/one.js" type="text/javascript"></script>
        <script type="text/javascript">obj.value = "value";</script>
        {% endcompress %}

    Which would be rendered something like::

        <script type="text/javascript" src="/media/CACHE/js/3f33b9146e12.js"></script>

    Linked files must be on your COMPRESS_URL (which defaults to MEDIA_URL).
    If DEBUG is true off-site files will throw exceptions. If DEBUG is false
    they will be silently stripped.
    """

    nodelist = parser.parse(('endcompress',))
    parser.delete_first_token()

    args = token.split_contents()

    if len(args) not in range(2,6):
        raise template.TemplateSyntaxError("%r tag requires 1-3 arguments." % args[0])

    kind = args[1]
    if not kind in ['css', 'js']:
        raise template.TemplateSyntaxError("%r's argument must be 'js' or 'css'." % (args[0], ', '.join(ALLOWED_ARGS)))
    
    try:
        xhtml = args[2] == "xhtml"
    except:
        xhtml = False
        
    if args[-2] == 'as':
        output_filename = args[-1]
    else:
        output_filename = None    
        
    return CompressorNode(nodelist, kind, xhtml, output_filename)
