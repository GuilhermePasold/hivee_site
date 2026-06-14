"""Autenticacao por token que tambem aceita um cookie httpOnly.

Smell fix (#2 - armazenamento inseguro de credencial): em vez de o front-end
guardar o token em localStorage (legivel por qualquer script, alvo facil de
XSS), o servidor passa a enviar o token num cookie `httpOnly`. O JavaScript da
pagina nao consegue mais ler o token, mas o navegador continua o enviando
automaticamente a cada requisicao.

Mantemos tambem o fluxo classico via header `Authorization: Token <key>`, usado
por clientes como o Swagger e o Postman (passo a passo do DRF).
"""
from django.conf import settings
from rest_framework.authentication import TokenAuthentication


class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        # 1) Header Authorization tem prioridade (clientes de API / Swagger).
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        # 2) Caso contrario, tenta o token guardado no cookie httpOnly.
        key = request.COOKIES.get(settings.AUTH_COOKIE_NAME)
        if not key:
            return None
        return self.authenticate_credentials(key)
