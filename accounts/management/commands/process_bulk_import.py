import json
import tempfile

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.bulk_import import process_import_file
from accounts.models import BulkImportJob, Sponsor, UserType


#recheck permissions before processing each line
def authorized_lines(source, job):
    for line in source:
        job.uploaded_by.refresh_from_db()
        uploader = job.uploaded_by

        if not uploader.is_active:
            raise ValueError("The uploader's account is inactive.")

        if job.organization_id is None:
            if uploader.user_type != UserType.ADMIN:
                raise ValueError("The uploader no longer has admin access.")
        else:
            authorized = (
                uploader.user_type == UserType.SPONSOR
                and Sponsor.objects.filter(
                    user=uploader,
                    organization_id=job.organization_id,
                    organization__is_active=True,
                ).exists()
            )

            if not authorized:
                raise ValueError(
                    "The uploader no longer has access to this organization."
                )

        yield line


class Command(BaseCommand):
    help = "Process one pending bulk-import job."

    def add_arguments(self, parser):
        parser.add_argument("job_id", type=int)

    def handle(self, *args, **options):
        #claim the job so two workers cannot process it together
        with transaction.atomic():
            try:
                job = BulkImportJob.objects.select_for_update().get(
                    id=options["job_id"]
                )
            except BulkImportJob.DoesNotExist:
                raise CommandError("Import job not found.")

            if job.status != BulkImportJob.Status.PENDING:
                raise CommandError("Only pending jobs can be processed.")

            job.status = BulkImportJob.Status.RUNNING
            job.started_at = timezone.now()
            job.save(update_fields=["status", "started_at"])

        #use a temporary disk file instead of keeping all results in memory
        with tempfile.TemporaryFile(mode="w+b") as results_file:
            try:
                with job.source_file.open("rb") as source:
                    results = process_import_file(
                        authorized_lines(source, job),
                        job.uploaded_by,
                        settings.ACCOUNT_SETUP_BASE_URL,
                    )

                    for result in results:
                        results_file.write(
                            (json.dumps(result) + "\n").encode("utf-8")
                        )

                        job.processed_rows += 1

                        if result["status"] == "success":
                            job.successful_rows += 1
                        else:
                            job.failed_rows += 1

                        job.save(update_fields=[
                            "processed_rows",
                            "successful_rows",
                            "failed_rows",
                        ])

                job.status = BulkImportJob.Status.COMPLETED

            except Exception:
                job.status = BulkImportJob.Status.FAILED
                job.error_message = (
                    "Processing stopped unexpectedly. Some rows may already "
                    "have been applied. Review the results before uploading again."
                )
                self.stderr.write(
                    "Import stopped. Check the worker traceback."
                )
                import traceback
                traceback.print_exc()

            #preserve results even when processing stopped partway through
            results_file.seek(0)
            job.result_file.save(
                "results.ndjson",
                File(results_file),
                save=False,
            )

            job.finished_at = timezone.now()
            job.save()

        self.stdout.write(
            f"Job {job.id}: {job.status}; "
            f"{job.successful_rows} successful, "
            f"{job.failed_rows} failed rows."
        )