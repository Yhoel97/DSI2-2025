# myapp/decorators.py
from functools import wraps
from django.shortcuts import redirect

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/')
        # aquí usábamos is_superuser en tu proyecto; si prefieres is_staff cámbialo
        if not request.user.is_superuser:
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
