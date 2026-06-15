import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand

from ...models import UserProfile

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cpf/%s"


class Command(BaseCommand):
    help = "Verifica CPFs pendentes na ReceitaWS (respeita rate limit de 3 req/min)"

    def handle(self, *args, **options):
        pendentes = UserProfile.objects.filter(
            cpf_status="pending_verification", cpf__isnull=False
        ).exclude(cpf="")

        total = pendentes.count()
        if not total:
            self.stdout.write(self.style.SUCCESS("Nenhum CPF pendente."))
            return

        self.stdout.write(f"Verificando {total} CPF(s)...")
        ok = 0
        fail = 0

        for i, profile in enumerate(pendentes):
            if i > 0:
                self.stdout.write(f"  Aguardando 21s (rate limit)...")
                time.sleep(21)

            cpf_limpo = "".join(c for c in profile.cpf if c.isdigit())
            self.stdout.write(f"  [{i + 1}/{total}] {cpf_limpo}... ", ending="")

            try:
                req = Request(
                    RECEITAWS_URL % cpf_limpo,
                    headers={"User-Agent": "HIVEE-ADMIN/1.0"},
                )
                with urlopen(req, timeout=10) as res:
                    data = json.loads(res.read().decode())

                if data.get("status") == "ERROR":
                    self.stdout.write(self.style.WARNING("indisponível"))
                    fail += 1
                    continue

                nome_receita = (data.get("nome") or "").strip().upper()
                nome_usuario = (profile.user.first_name or "").strip().upper()

                if nome_receita and nome_receita == nome_usuario:
                    profile.cpf_status = "verified"
                    profile.cpf_name = nome_receita
                    status_label = "verificado"
                elif nome_receita:
                    profile.cpf_status = "mismatch"
                    profile.cpf_name = nome_receita
                    status_label = self.style.ERROR("nome divergente")
                else:
                    self.stdout.write(self.style.WARNING("sem nome retornado"))
                    fail += 1
                    continue

                profile.save(update_fields=["cpf_status", "cpf_name"])
                self.stdout.write(self.style.SUCCESS(status_label))
                ok += 1

            except (URLError, json.JSONDecodeError, OSError) as e:
                self.stdout.write(self.style.WARNING(f"erro: {e}"))
                fail += 1

        self.stdout.write(
            self.style.SUCCESS(f"\n{ok} verificado(s), {fail} falha(s).")
        )
