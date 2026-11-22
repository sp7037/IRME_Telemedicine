from decimal import Decimal

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User, DoctorProfile, PatientProfile, TMCProfile
from consultations import models as m
from consultations.finance import (
    patient_wallet_topup, tmc_account_topup, process_patient_recharge_request,
    process_tmc_recharge_request, reconcile_approved_patient_recharges,
    reconcile_approved_tmc_recharges,
)


class FinancialAdminSafetyTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(email="admin@safety.test", password="testpass")
        self.staff = User.objects.create_user(email="staff@safety.test", password="testpass", is_staff=True)
        self.patient_user = User.objects.create_user(email="patient@safety.test", password="testpass", is_patient=True)
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.operator = User.objects.create_user(email="tmc@safety.test", password="testpass", is_tmc_operator=True)
        self.tmc = TMCProfile.objects.create(user=self.operator)
        self.doctor_user = User.objects.create_user(email="doctor@safety.test", password="testpass", is_doctor=True)
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, consultation_fee="100.00")
        self.consultation = m.Consultation.objects.create(patient=self.patient, doctor=self.doctor, scheduled_time=timezone.now())
        self.payment = m.Payment.objects.create(consultation=self.consultation, amount="100.00")
        self.finance = m.ConsultationFinance.objects.create(
            consultation=self.consultation, payment=self.payment, source_type="DIRECT_PATIENT",
            billing_type="PAID", payer_entity="PATIENT", amount_charged="100.00",
        )
        self.patient_entry = patient_wallet_topup(self.patient, "500.00")
        self.tmc_entry = tmc_account_topup(self.tmc, "500.00")
        self.patient_recharge = m.PatientWalletRechargeRequest.objects.create(patient=self.patient, amount="25.00")
        self.tmc_recharge = m.TMCRechargeRequest.objects.create(tmc=self.tmc, amount="25.00")
        self.request_factory = RequestFactory()
        self.client.force_login(self.superuser)

    def request(self, user):
        request = self.request_factory.get("/admin/")
        request.user = user
        return request

    def change_url(self, obj, action="change"):
        return reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_{action}", args=[obj.pk])

    def test_all_financial_admins_block_add_change_and_delete_even_for_superusers(self):
        names = (
            "Consultation", "ConsultationFollowUpSession", "Payment", "ConsultationEvent",
            "ConsultationFinance", "AdminPlatformAccount", "AdminPlatformEntry", "PatientWallet",
            "PatientWalletEntry", "PatientWalletRechargeRequest", "TMCAccount", "TMCAccountEntry",
            "TMCRechargeRequest", "DoctorEarning",
        )
        for name in names:
            with self.subTest(model=name):
                model = getattr(m, name)
                model_admin = admin.site._registry[model]
                request = self.request(self.superuser)
                self.assertTrue(model_admin.has_view_permission(request))
                self.assertFalse(model_admin.has_add_permission(request))
                self.assertFalse(model_admin.has_change_permission(request))
                self.assertFalse(model_admin.has_delete_permission(request))
                self.assertNotIn("delete_selected", model_admin.get_actions(request))
                self.assertEqual(set(model_admin.get_readonly_fields(request)),
                                 {field.name for field in model._meta.fields})
                add_url = reverse(f"admin:consultations_{model._meta.model_name}_add")
                self.assertEqual(self.client.post(add_url, {"balance": "99999.00"}).status_code, 403)

    def test_forged_change_posts_cannot_modify_balance_payment_finance_or_recharge(self):
        objects = (self.payment, self.finance, self.patient_entry.wallet, self.tmc_entry.account,
                   self.patient_recharge, self.tmc_recharge, self.consultation)
        for obj in objects:
            with self.subTest(model=type(obj).__name__):
                original = type(obj).objects.filter(pk=obj.pk).values().get()
                response = self.client.post(self.change_url(obj), {
                    "balance": "99999.00", "amount": "1.00", "status": "APPROVED",
                    "doctor_fee": "99999.00", "patient": self.patient.pk,
                })
                self.assertEqual(response.status_code, 403)
                self.assertEqual(type(obj).objects.filter(pk=obj.pk).values().get(), original)

    def test_delete_urls_and_bulk_actions_preserve_financial_owners_and_history(self):
        objects = (self.patient_user, self.doctor_user, self.operator, self.patient, self.doctor,
                   self.tmc, self.consultation, self.payment, self.finance, self.patient_entry,
                   self.tmc_entry, self.patient_entry.wallet, self.tmc_entry.account,
                   self.patient_recharge, self.tmc_recharge)
        for obj in objects:
            with self.subTest(model=type(obj).__name__):
                self.assertEqual(self.client.post(self.change_url(obj, "delete"), {"post": "yes"}).status_code, 403)
                model_admin = admin.site._registry[type(obj)]
                self.assertNotIn("delete_selected", model_admin.get_actions(self.request(self.superuser)))
                with self.assertRaises(PermissionDenied):
                    model_admin.delete_queryset(self.request(self.superuser), type(obj).objects.filter(pk=obj.pk))
                self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())
        self.assertEqual(m.PatientWalletEntry.objects.count(), 1)
        self.assertEqual(m.TMCAccountEntry.objects.count(), 1)

    def test_finance_inline_is_read_only_and_cannot_add_or_delete(self):
        inline = admin.site._registry[m.Consultation].get_inline_instances(self.request(self.superuser), self.consultation)[0]
        request = self.request(self.superuser)
        self.assertFalse(inline.has_add_permission(request, self.consultation))
        self.assertFalse(inline.has_change_permission(request, self.consultation))
        self.assertFalse(inline.has_delete_permission(request, self.consultation))
        self.assertIn("amount_charged", inline.get_readonly_fields(request))

    def test_profile_owner_and_usage_counters_are_read_only_but_settings_remain_editable(self):
        request = self.request(self.superuser)
        for profile in (self.patient, self.doctor, self.tmc):
            model_admin = admin.site._registry[type(profile)]
            fields = model_admin.get_form(request, profile).base_fields
            self.assertNotIn("user", fields)
            self.assertIn("is_active", fields)
            self.assertTrue(model_admin.has_change_permission(request, profile))
        fields = admin.site._registry[TMCProfile].get_form(request, self.tmc).base_fields
        self.assertNotIn("free_consultations_used", fields)
        self.assertNotIn("discounted_consultations_used", fields)
        self.assertIn("free_consultation_quota", fields)
        self.assertIn("discount_percentage", fields)
        self.assertIn("consultation_fee", admin.site._registry[DoctorProfile].get_form(request, self.doctor).base_fields)

    def grant(self, user, model, *actions):
        user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label=model._meta.app_label,
            codename__in=[f"{action}_{model._meta.model_name}" for action in actions],
        ))
        return User.objects.get(pk=user.pk)

    def action(self, model, obj, name):
        return self.client.post(reverse(f"admin:consultations_{model._meta.model_name}_changelist"), {
            "action": name, "_selected_action": [obj.pk], "index": "0",
        })

    def test_manual_recharge_approval_credits_once_and_records_actor_time_and_admin_log(self):
        for obj, wallet in ((self.patient_recharge, self.patient_entry.wallet), (self.tmc_recharge, self.tmc_entry.account)):
            with self.subTest(model=type(obj).__name__):
                for _ in range(2):
                    self.assertEqual(self.action(type(obj), obj, "approve_manual_recharges").status_code, 302)
                obj.refresh_from_db(); wallet.refresh_from_db()
                self.assertEqual(obj.status, "APPROVED")
                self.assertEqual(obj.processed_by_id, self.superuser.pk)
                self.assertIsNotNone(obj.processed_at)
                self.assertEqual(wallet.balance, Decimal("525.00"))
                self.assertEqual(wallet.entries.count(), 2)
                self.assertTrue(LogEntry.objects.filter(user=self.superuser, object_id=str(obj.pk),
                    content_type__model=obj._meta.model_name, change_message__contains="via finance service").exists())

    def test_manual_recharge_rejection_does_not_credit_and_cannot_later_be_approved(self):
        for obj in (self.patient_recharge, self.tmc_recharge):
            self.action(type(obj), obj, "reject_manual_recharges")
            self.action(type(obj), obj, "approve_manual_recharges")
            obj.refresh_from_db()
            self.assertEqual(obj.status, "REJECTED")
            self.assertEqual(obj.processed_by_id, self.superuser.pk)
        self.assertEqual(m.PatientWalletEntry.objects.count(), 1)
        self.assertEqual(m.TMCAccountEntry.objects.count(), 1)

    def test_view_only_staff_cannot_invoke_recharge_actions(self):
        staff = self.grant(self.staff, m.TMCRechargeRequest, "view")
        self.client.force_login(staff)
        self.action(m.TMCRechargeRequest, self.tmc_recharge, "approve_manual_recharges")
        self.tmc_recharge.refresh_from_db()
        self.assertEqual(self.tmc_recharge.status, "PENDING")
        model_admin = admin.site._registry[m.TMCRechargeRequest]
        with self.assertRaises(PermissionDenied):
            model_admin.approve_manual_recharges(self.request(staff), m.TMCRechargeRequest.objects.all())
        api = APIClient(); api.force_authenticate(staff)
        response = api.post(reverse("staff-tmc-recharge-process", kwargs={"recharge_id": self.tmc_recharge.pk}), {"action": "approve"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_change_permission_staff_can_process_but_cannot_edit_recharge(self):
        staff = self.grant(self.staff, m.TMCRechargeRequest, "view", "change")
        self.client.force_login(staff)
        self.assertEqual(self.client.post(self.change_url(self.tmc_recharge), {"amount": "9999.00"}).status_code, 403)
        self.assertEqual(self.action(m.TMCRechargeRequest, self.tmc_recharge, "approve_manual_recharges").status_code, 302)
        self.tmc_recharge.refresh_from_db()
        self.assertEqual(self.tmc_recharge.processed_by_id, staff.pk)
        self.assertEqual(self.tmc_recharge.amount, Decimal("25.00"))

    def test_gateway_recharges_cannot_be_manually_approved_by_admin_or_staff_api(self):
        api = APIClient(); api.force_authenticate(self.superuser)
        for obj, route in ((self.patient_recharge, "staff-patient-recharge-process"),
                           (self.tmc_recharge, "staff-tmc-recharge-process")):
            obj.provider = "RAZORPAY"; obj.gateway_order_id = "order_mock"
            obj.save(update_fields=["provider", "gateway_order_id"])
            self.action(type(obj), obj, "approve_manual_recharges")
            response = api.post(reverse(route, kwargs={"recharge_id": obj.pk}), {"action": "approve"}, format="json")
            self.assertEqual(response.status_code, 400)
            obj.refresh_from_db(); self.assertEqual(obj.status, "PENDING")
        self.assertEqual(m.PatientWalletEntry.objects.count(), 1)
        self.assertEqual(m.TMCAccountEntry.objects.count(), 1)

    def test_gateway_approved_recharges_are_not_credited_again_by_legacy_reconciliation(self):
        for obj in (self.patient_recharge, self.tmc_recharge):
            obj.status = "APPROVED"; obj.provider = "RAZORPAY"
            obj.save(update_fields=["status", "provider"])
        for _ in range(2):
            self.assertEqual(reconcile_approved_patient_recharges(self.patient), [])
            self.assertEqual(reconcile_approved_tmc_recharges(self.tmc), [])
        self.assertEqual(m.PatientWalletEntry.objects.count(), 1)
        self.assertEqual(m.TMCAccountEntry.objects.count(), 1)

    def test_legacy_manual_reconciliation_is_once_only_and_skips_gateway_metadata(self):
        for obj in (self.patient_recharge, self.tmc_recharge):
            obj.status = "APPROVED"; obj.save(update_fields=["status"])
        self.assertEqual(len(reconcile_approved_patient_recharges(self.patient)), 1)
        self.assertEqual(len(reconcile_approved_tmc_recharges(self.tmc)), 1)
        self.assertEqual(reconcile_approved_patient_recharges(self.patient), [])
        self.assertEqual(reconcile_approved_tmc_recharges(self.tmc), [])
        contaminated = m.TMCRechargeRequest.objects.create(tmc=self.tmc, amount="25.00", status="APPROVED", gateway_order_id="order_unknown")
        self.assertEqual(reconcile_approved_tmc_recharges(self.tmc), [])
        self.assertTrue(m.TMCRechargeRequest.objects.filter(pk=contaminated.pk).exists())

    def test_manual_service_rejects_missing_nonstaff_and_inactive_actors_without_mutation(self):
        self.staff.is_active = False; self.staff.save(update_fields=["is_active"])
        for actor in (None, self.patient_user, self.staff):
            for fn, obj in ((process_patient_recharge_request, self.patient_recharge),
                            (process_tmc_recharge_request, self.tmc_recharge)):
                with self.assertRaises(ValueError):
                    fn(obj, approve=True, processed_by=actor)
                obj.refresh_from_db(); self.assertEqual(obj.status, "PENDING")

    def test_staff_cannot_grant_admin_privileges_or_change_another_admin(self):
        staff = self.grant(self.staff, User, "view", "change", "add")
        request = self.request(staff); model_admin = admin.site._registry[User]
        for obj in (self.staff, self.patient_user, None):
            fields = model_admin.get_form(request, obj).base_fields
            for name in ("is_staff", "is_superuser", "groups", "user_permissions"):
                self.assertNotIn(name, fields)
        self.assertFalse(model_admin.has_change_permission(request, self.superuser))
        other_staff = User.objects.create_user(email="other-staff@safety.test", password="testpass", is_staff=True)
        self.assertFalse(model_admin.has_change_permission(request, other_staff))
        self.client.force_login(staff)
        self.assertEqual(self.client.post(self.change_url(self.superuser), {"is_active": ""}).status_code, 403)
        response = self.client.post(self.change_url(staff), {
            "email": staff.email, "first_name": "Local staff", "last_name": "", "phone_number": "",
            "is_active": "on", "is_staff": "on", "is_superuser": "on",
            "user_permissions": list(Permission.objects.values_list("pk", flat=True)),
        })
        self.assertEqual(response.status_code, 302)
        staff.refresh_from_db()
        self.assertFalse(staff.is_superuser)
        self.assertTrue(staff.is_staff)
        self.assertEqual(staff.user_permissions.count(), 3)

    def test_staff_topups_keep_auditable_actor_reference_and_inactive_staff_is_denied(self):
        self.staff = self.grant(self.staff, m.PatientWallet, "change")
        api = APIClient(); api.force_authenticate(self.staff)
        response = api.post(reverse("staff-patient-wallet-topup"), {
            "patient_profile_id": self.patient.pk, "amount": "10.00", "description": "Manual cash test",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        entry = m.PatientWalletEntry.objects.get(pk=response.data["entry_id"])
        self.assertTrue(entry.description.startswith(f"Staff #{self.staff.pk}: "))
        self.staff.is_active = False; self.staff.save(update_fields=["is_active"])
        response = api.post(reverse("staff-patient-wallet-topup"), {"patient_profile_id": self.patient.pk, "amount": "10.00"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_authorised_staff_can_still_edit_future_fee_settings(self):
        response = self.client.post(reverse("admin:consultations_consultationfeesetting_add"), {
            "name": "Admin fee test", "direct_patient_fee": "100.00", "tmc_consultation_fee": "100.00",
            "platform_fee_percentage": "10.00", "currency": "INR", "is_active": "on",
        })
        self.assertEqual(response.status_code, 302)
        setting = m.ConsultationFeeSetting.objects.get(name="Admin fee test")
        self.assertEqual(setting.created_by_id, self.superuser.pk)

    def test_staff_offer_api_cannot_rewrite_usage_or_partially_change_config(self):
        self.staff = self.grant(self.staff, TMCProfile, "change")
        api = APIClient(); api.force_authenticate(self.staff)
        response = api.patch(reverse("staff-tmc-list"), {
            "tmc_profile_id": self.tmc.pk, "free_consultation_quota": 10,
            "free_consultations_used": 0, "discounted_consultations_used": 0,
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.tmc.refresh_from_db(); self.assertEqual(self.tmc.free_consultation_quota, 0)
        for value in ("-1", "101", "NaN"):
            response = api.patch(reverse("staff-tmc-list"), {
                "tmc_profile_id": self.tmc.pk, "discount_percentage": value,
            }, format="json")
            self.assertEqual(response.status_code, 400)
        response = api.patch(reverse("staff-tmc-list"), {
            "tmc_profile_id": self.tmc.pk, "free_consultation_quota": 2, "discount_percentage": "30.00",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.tmc.refresh_from_db()
        self.assertEqual(self.tmc.free_consultation_quota, 2)
        self.assertEqual(self.tmc.discount_percentage, Decimal("30.00"))
        self.assertEqual(self.tmc.free_consultations_used, 0)
        self.assertTrue(LogEntry.objects.filter(user=self.staff, content_type__model="tmcprofile",
            object_id=str(self.tmc.pk)).exists())

    def test_each_financial_write_api_requires_its_specific_permission(self):
        cases = (
            ("staff-patient-wallet-topup", {}, "post", m.PatientWallet, "change", {"patient_profile_id": self.patient.pk, "amount": "5.00"}),
            ("staff-tmc-wallet-topup", {}, "post", m.TMCAccount, "change", {"tmc_profile_id": self.tmc.pk, "amount": "5.00"}),
            ("staff-admin-platform-wallet-topup", {}, "post", m.AdminPlatformAccount, "change", {"amount": "5.00"}),
            ("staff-tmc-recharge-process", {"recharge_id": self.tmc_recharge.pk}, "post", m.TMCRechargeRequest, "change", {"action": "approve"}),
            ("staff-patient-recharge-process", {"recharge_id": self.patient_recharge.pk}, "post", m.PatientWalletRechargeRequest, "change", {"action": "approve"}),
            ("staff-tmc-list", {}, "patch", TMCProfile, "change", {"tmc_profile_id": self.tmc.pk, "discount_percentage": "10.00"}),
            ("staff-fee-settings", {}, "post", m.ConsultationFeeSetting, "add", {"direct_patient_fee": "100.00"}),
        )
        api = APIClient()
        for route, kwargs, method, model, action, payload in cases:
            with self.subTest(route=route):
                self.staff.user_permissions.clear()
                staff = User.objects.get(pk=self.staff.pk)
                api.force_authenticate(staff)
                url = reverse(route, kwargs=kwargs)
                self.assertEqual(getattr(api, method)(url, payload, format="json").status_code, 403)
                staff = self.grant(staff, model, action)
                api.force_authenticate(staff)
                self.assertIn(getattr(api, method)(url, payload, format="json").status_code, (200, 201))

    def test_invalid_fee_configuration_does_not_deactivate_existing_settings(self):
        setting = m.ConsultationFeeSetting.objects.create(name="Valid prior configuration", is_active=True)
        api = APIClient(); api.force_authenticate(self.superuser)
        for payload in ({"direct_patient_fee": "bad"}, {"platform_fee_percentage": "101"}, {"tmc_consultation_fee": "-1"}):
            self.assertEqual(api.post(reverse("staff-fee-settings"), payload, format="json").status_code, 400)
            setting.refresh_from_db(); self.assertTrue(setting.is_active)
            self.assertEqual(m.ConsultationFeeSetting.objects.count(), 1)
