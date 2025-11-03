from django.db import migrations
import re

def limpiar_salas(apps, schema_editor):
    Funcion = apps.get_model('myapp', 'Funcion')
    
    for funcion in Funcion.objects.all():
        sala_original = funcion.sala
        
        # Remover paréntesis, corchetes y comillas
        sala_limpia = re.sub(r"[\(\)\[\]'\"]", "", sala_original)
        
        # Si hay coma, tomar solo la primera parte
        if ',' in sala_limpia:
            sala_limpia = sala_limpia.split(',')[0].strip()
        else:
            sala_limpia = sala_limpia.strip()
        
        # Actualizar solo si cambió
        if sala_limpia != sala_original:
            funcion.sala = sala_limpia
            funcion.save()
            print(f"✅ Limpiado: '{sala_original}' → '{sala_limpia}'")

def reversa(apps, schema_editor):
    # No hacer nada en reversa
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_remove_funcion_formato'),  # ✅ Esta es tu última migración
    ]

    operations = [
        migrations.RunPython(limpiar_salas, reversa),
    ]