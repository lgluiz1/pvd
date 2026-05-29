from rest_framework.authtoken.models import Token
import sys

t = Token.objects.filter(key='d36031a38675093a2526e90c81ff5d4645d305cd410e6c47971e7146f61774a5').first()
if t:
    print(f"User: {t.user.username}")
    if hasattr(t.user, 'empresa'):
        print(f"Empresa: {t.user.empresa.nome_fantasia}")
        print(f"MP Access Token: {t.user.empresa.mp_access_token}")
    else:
        print("No empresa attr")
else:
    print("Token not found")
