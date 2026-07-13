
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from RedShop.deployment_checks import (
    collect_deployment_findings,
    has_blocking_findings,
)


class Command(BaseCommand):
    help = "Report deployment-readiness risks in Django settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with an error when blocking deployment findings exist.",
        )

    def handle(self, *args, **options):
        strict = bool(options["strict"])
        findings = collect_deployment_findings()

        if not findings:
            self.stdout.write(self.style.SUCCESS("Deployment check passed."))
            return

        for finding in findings:
            style = self.style.ERROR if finding.level == "ERROR" else self.style.WARNING
            line = f"[{finding.level}] {finding.code}: {finding.message}"

            if finding.hint:
                line = f"{line} Hint: {finding.hint}"

            self.stdout.write(style(line))

        if strict and has_blocking_findings(findings):
            raise CommandError("Deployment check failed with blocking findings.")
