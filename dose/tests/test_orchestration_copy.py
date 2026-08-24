from django.test import SimpleTestCase

from dose.orchestration_copy import describe_instruction_match


class OrchestrationCopyTests(SimpleTestCase):
    def test_success_shows_method_path_and_consumer(self):
        text = describe_instruction_match(
            {
                "status": "processed",
                "matched": 1,
                "results": [
                    {
                        "method": "POST",
                        "direction": "REQ",
                        "path": "/events/slack/webhook/contact",
                        "executescript": "OdooCreatePartner",
                        "status": "success",
                    }
                ],
            }
        )
        self.assertEqual(
            text,
            "POST REQ /events/slack/webhook/contact → OdooCreatePartner",
        )

    def test_no_consumer_is_explicit(self):
        text = describe_instruction_match(
            {
                "status": "no_instruction",
                "matched": 0,
                "action_path": "/events/slack/webhook/sale",
                "method": "POST",
                "results": [],
            }
        )
        self.assertEqual(
            text,
            "No instruction match for POST /events/slack/webhook/sale",
        )

    def test_empty_result_is_blank(self):
        self.assertEqual(describe_instruction_match({}), "")
