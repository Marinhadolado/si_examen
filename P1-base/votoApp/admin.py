# admin.py
from django.contrib import admin
from .models import Censo, Voto

# Register Censo model
@admin.register(Censo)
class CensoAdmin(admin.ModelAdmin):
    pass

# Register Voto model
@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    pass
