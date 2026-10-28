import unittest

from agentenv_api_workbench.environment import ApiWorkbenchEnvironment
from agentenv_api_workbench.fixtures import DEFAULT_TASKS


def score_response(task_id: str, response: str) -> dict[str, object]:
    task = next(task for task in DEFAULT_TASKS if task.task_id == task_id)
    environment = ApiWorkbenchEnvironment([task])
    environment.reset(0)
    return environment.step(response)


class FixtureRubricTests(unittest.TestCase):
    def test_cancel_fields_accept_declared_string_aliases(self) -> None:
        response = (
            "export type BookingId = string;\n"
            "export type CancellationReason = string;\n"
            "interface CancelBookingPathParams { bookingId: BookingId; }\n"
            "interface CancelBookingRequestBody { cancellationReason?: CancellationReason; }\n"
        )

        result = score_response("design-cancel-booking", response)

        self.assertIn("booking identifier", result["info"]["passed_checks"])
        self.assertIn("cancellation reason", result["info"]["passed_checks"])

    def test_alias_names_and_declaration_order_are_not_prescribed(self) -> None:
        result = score_response(
            "design-cancel-booking",
            "interface Params { bookingId: Identifier; cancellationReason?: ReasonText; }\n"
            "type ReasonText = string;\ntype Identifier = string;\n",
        )

        self.assertIn("booking identifier", result["info"]["passed_checks"])
        self.assertIn("cancellation reason", result["info"]["passed_checks"])

    def test_cancel_fields_reject_unproven_string_aliases(self) -> None:
        for declarations in (
            "",
            "type BookingId = number; type CancellationReason = number;",
            "type BookingId = string[]; type CancellationReason = string[];",
        ):
            with self.subTest(declarations=declarations):
                result = score_response(
                    "design-cancel-booking",
                    declarations
                    + "\ninterface Params { bookingId: BookingId; "
                    "cancellationReason?: CancellationReason; }\n",
                )

                self.assertIn("booking identifier", result["info"]["failed_checks"])
                self.assertIn("cancellation reason", result["info"]["failed_checks"])

    def test_held_out_design_fields_accept_declared_string_aliases(self) -> None:
        result = score_response(
            "design-search-availability",
            "type PropertyId = string;\ntype DateText = string;\n"
            "interface AvailabilityQuery { propertyId: PropertyId; "
            "checkIn: DateText; checkOut: DateText; guests: number; }\n"
            "type AvailabilityResult = { available: boolean };\n"
            "if (!input) return false;",
        )

        self.assertEqual(result["reward"], 1.0)

    def test_held_out_design_rejects_undeclared_date_alias(self) -> None:
        result = score_response(
            "design-search-availability",
            "interface AvailabilityQuery { checkIn: ISODateString; checkOut: ISODateString; }",
        )

        self.assertIn("check-in query", result["info"]["failed_checks"])
        self.assertIn("check-out query", result["info"]["failed_checks"])

    def test_held_out_design_accepts_template_literal_date_alias(self) -> None:
        result = score_response(
            "design-search-availability",
            "export type ISODateString = `${number}-${number}-${number}`;\n"
            "interface AvailabilityQuery { checkIn: ISODateString; checkOut: ISODateString; }",
        )

        self.assertIn("check-in query", result["info"]["passed_checks"])
        self.assertIn("check-out query", result["info"]["passed_checks"])

    def test_held_out_design_rejects_template_literal_array_alias(self) -> None:
        result = score_response(
            "design-search-availability",
            "type ISODateString = `${number}-${number}-${number}`[];\n"
            "interface AvailabilityQuery { checkIn: ISODateString; checkOut: ISODateString; }",
        )

        self.assertIn("check-in query", result["info"]["failed_checks"])
        self.assertIn("check-out query", result["info"]["failed_checks"])

    def test_each_held_out_route_requires_its_own_sections(self) -> None:
        sections = (
            ("description section", "**Description:** Booking operation"),
            ("request section", "**Request Payload / Params:** bookingId"),
            ("success response section", "**Expected Response (Success):** {}"),
        )
        for method in ("PATCH", "DELETE"):
            for check_name, omitted_section in sections:
                with self.subTest(method=method, section=check_name):
                    response = "\n".join(
                        f"### `[{route_method}]` `/bookings/:bookingId`\n"
                        + "\n".join(
                            text for _, text in sections
                            if route_method != method or text != omitted_section
                        )
                        for route_method in ("PATCH", "DELETE")
                    )

                    result = score_response("document-booking-update-and-cancel", response)

                    self.assertEqual(
                        result["info"]["failed_checks"], [f"{method} {check_name}"]
                    )
                    self.assertAlmostEqual(result["reward"], 0.9)

    def test_complete_held_out_documentation_accepts_both_path_formats(self) -> None:
        for path in (":bookingId", "{bookingId}"):
            with self.subTest(path=path):
                response = "\n".join(
                    f"### `[{method}]` `/bookings/{path}`\n"
                    "**Description:** Booking operation\n"
                    "**Request Payload / Params:** bookingId\n"
                    "**Expected Response (Success):** {}"
                    for method in ("PATCH", "DELETE")
                )

                result = score_response("document-booking-update-and-cancel", response)

                self.assertEqual(result["reward"], 1.0)


if __name__ == "__main__":
    unittest.main()
