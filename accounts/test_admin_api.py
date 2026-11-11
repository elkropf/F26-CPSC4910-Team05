import json

from django.test import TestCase, override_settings

from .models import Admin, Driver, DriverOrganization, Organization, Sponsor, User, UserType


class AdminApiTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_tester", password="AdminTestPass!123", user_type=UserType.ADMIN)
        Admin.objects.create(user=self.admin_user)
        self.driver_user = User.objects.create_user(
            username="driver_tester", password="DriverTestPass!123", email="driver@example.com",
            user_type=UserType.DRIVER)
        self.driver = Driver.objects.create(user=self.driver_user)
        self.org_a = Organization.objects.create(organization_name="Test Sponsor A")
        self.org_b = Organization.objects.create(organization_name="Test Sponsor B")
        self.sponsor_user = User.objects.create_user(
            username="sponsor_tester", password="SponsorTestPass!123", user_type=UserType.SPONSOR)
        self.sponsor = Sponsor.objects.create(user=self.sponsor_user, organization=self.org_a)
        self.sponsor_user_b = User.objects.create_user(
            username="sponsor_tester_b", password="SponsorTestPass!123", user_type=UserType.SPONSOR)
        self.sponsor_b = Sponsor.objects.create(user=self.sponsor_user_b, organization=self.org_b)

    def post_json(self, path, data=None):
        return self.client.post(path, data=json.dumps(data or {}), content_type="application/json")

    def test_non_admin_cannot_read_or_write(self):
        self.client.force_login(self.driver_user)
        self.assertEqual(self.client.get("/api/admin/directory/").status_code, 403)
        self.assertEqual(self.post_json("/api/admin/sponsors/create/", {
            "username": "notallowed", "password": "SomeLongPassword!123",
            "organization_id": self.org_a.pk,
        }).status_code, 403)

    def test_create_sponsor_and_admin(self):
        self.client.force_login(self.admin_user)
        response = self.post_json("/api/admin/sponsors/create/", {
            "username": "new_sponsor", "email": "new@example.com",
            "password": "Valid-Sponsor-Pass-123", "organization_name": "Brand New Organization",
        })
        self.assertEqual(response.status_code, 201, response.content)
        sponsor = Sponsor.objects.get(user__username="new_sponsor")
        self.assertEqual(sponsor.organization.organization_name, "Brand New Organization")
        self.assertEqual(sponsor.fee_percentage, 1)
        response = self.post_json("/api/admin/admins/create/", {
            "username": "second_admin", "email": "second@example.com",
            "password": "Valid-Admin-Pass-123",
        })
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(Admin.objects.filter(user__username="second_admin").exists())

    def test_assign_driver_moves_only_active_membership(self):
        self.client.force_login(self.admin_user)
        DriverOrganization.objects.create(driver=self.driver, organization=self.org_a)
        response = self.post_json(f"/api/admin/drivers/{self.driver.pk}/assign/", {
            "sponsor_id": self.sponsor_b.pk,
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(DriverOrganization.objects.filter(driver=self.driver).count(), 1)
        self.assertTrue(DriverOrganization.objects.filter(driver=self.driver, organization=self.org_b).exists())

    def test_fee_change_and_report(self):
        self.client.force_login(self.admin_user)
        response = self.post_json(f"/api/admin/sponsors/{self.sponsor.pk}/fee/", {
            "fee_percentage": "2.75",
        })
        self.assertEqual(response.status_code, 200, response.content)
        self.sponsor.refresh_from_db()
        self.assertEqual(str(self.sponsor.fee_percentage), "2.75")
        response = self.client.get("/api/admin/reports/sponsors/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"sponsor_tester", response.content)

    def test_admin_cannot_delete_self(self):
        self.client.force_login(self.admin_user)
        response = self.post_json(f"/api/admin/users/{self.admin_user.pk}/delete/")
        self.assertEqual(response.status_code, 400)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_driver_reset_sends_email(self):
        from django.core import mail
        self.client.force_login(self.admin_user)
        response = self.post_json(f"/api/admin/drivers/{self.driver.pk}/reset-password/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/account/setup/", mail.outbox[0].body)