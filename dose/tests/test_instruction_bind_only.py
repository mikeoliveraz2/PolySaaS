from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib import admin
from django.test import RequestFactory, SimpleTestCase

from dose.admin import InstructionAdmin, TenantAwareModelAdmin
from dose.models import Instruction


class InstructionBindOnlyTests(SimpleTestCase):
    @patch("django.contrib.messages.add_message")
    @patch.object(TenantAwareModelAdmin, "save_model")
    def test_bind_only_saves_without_executing_atomic_service(
        self, parent_save, _message
    ):
        model_admin = InstructionAdmin(Instruction, admin.site)
        request = RequestFactory().post(
            "/admin/dose/instruction/add/?bind_only=1"
        )
        request.GET = {"bind_only": "1"}
        request.tenant = SimpleNamespace(schema_name="polysaasonline")
        instruction = SimpleNamespace(
            requestpath="/events/slack/command/poly",
            requestmethod="POST",
            direction="REQ",
            executescript="OdooCreatePartner",
            execute_atomic_service=MagicMock(),
        )

        model_admin.save_model(request, instruction, MagicMock(), change=False)

        parent_save.assert_called_once()
        instruction.execute_atomic_service.assert_not_called()
