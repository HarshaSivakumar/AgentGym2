from .environment import RubricCheck, WorkbenchTask


DEFAULT_TASKS = [
    WorkbenchTask(
        task_id="design-create-booking",
        mode="api_design",
        prompt=(
            "Design a TypeScript POST /bookings contract for creating a hotel booking. "
            "The request requires guestId, propertyId, checkIn, and checkOut. "
            "Validate that checkOut is after checkIn. Model validation, conflict, "
            "and infrastructure errors, then provide a guarded skeleton."
        ),
        rubric=(
            RubricCheck("request interface", r"\binterface\s+CreateBookingRequest\b", 2),
            RubricCheck("typed guest field", r"guestId\s*:\s*string"),
            RubricCheck("typed property field", r"propertyId\s*:\s*string"),
            RubricCheck("check-in field", r"checkIn\s*:\s*string"),
            RubricCheck("check-out field", r"checkOut\s*:\s*string"),
            RubricCheck("validation error", r"ValidationError"),
            RubricCheck("booking conflict error", r"ConflictError"),
            RubricCheck("guard clause", r"if\s*\("),
            RubricCheck("no untyped any", r"\bany\b", must_match=False),
        ),
    ),
    WorkbenchTask(
        task_id="design-cancel-booking",
        mode="api_design",
        prompt=(
            "Design a TypeScript POST /bookings/{bookingId}/cancel contract. "
            "Accept an optional cancellationReason, make cancellation idempotent, "
            "and reject bookings that are already checked in. Define typed success "
            "and error results and a guarded implementation skeleton."
        ),
        rubric=(
            RubricCheck("request interface", r"\binterface\s+CancelBookingRequest\b", 2),
            RubricCheck("booking identifier", r"bookingId\s*:\s*string"),
            RubricCheck("cancellation reason", r"cancellationReason\??\s*:\s*string"),
            RubricCheck("idempotency", r"idempotenc", weight=2),
            RubricCheck("checked-in conflict", r"checked.?in|already.?started|not.?cancellable"),
            RubricCheck("typed result", r"type\s+CancelBookingResult\s*=|interface\s+CancelBookingResult\b"),
            RubricCheck("guard clause", r"if\s*\("),
            RubricCheck("no untyped any", r"\bany\b", must_match=False),
        ),
    ),
    WorkbenchTask(
        task_id="design-search-availability",
        mode="api_design",
        prompt=(
            "Design a TypeScript GET /properties/{propertyId}/availability contract. "
            "Inputs are checkIn, checkOut, and guests. Validate the date range and "
            "guest count, and model unavailable dates as a normal result rather than "
            "an infrastructure error. Include typed errors and guarded skeleton logic."
        ),
        rubric=(
            RubricCheck("query interface", r"\binterface\s+AvailabilityQuery\b", 2),
            RubricCheck("property identifier", r"propertyId\s*:\s*string"),
            RubricCheck("check-in query", r"checkIn\s*:\s*string"),
            RubricCheck("check-out query", r"checkOut\s*:\s*string"),
            RubricCheck("guest count", r"guests\s*:\s*number"),
            RubricCheck("availability result", r"Availability(Result|Response)"),
            RubricCheck("validation guard", r"if\s*\("),
            RubricCheck("no untyped any", r"\bany\b", must_match=False),
        ),
    ),
    WorkbenchTask(
        task_id="document-health-and-bookings",
        mode="api_documentation",
        prompt=(
            "Document every route in the provided source. Give each route its own "
            "heading, a brief description, request details, and successful response."
        ),
        rubric=(
            RubricCheck("GET health route", r"(?m)^###\s+.*GET.*/health", 2),
            RubricCheck("POST bookings route", r"(?m)^###\s+.*POST.*/bookings", 2),
            RubricCheck("description sections", r"(?i)\*\*Description:\*\*", 2),
            RubricCheck("request sections", r"(?i)Request Payload\s*/\s*Params", 2),
            RubricCheck("success response sections", r"(?i)Expected Response\s*\(Success\)", 2),
        ),
        source_code=(
            "app.get('/health', (request, response) => {\n"
            "  response.json({ status: 'ok' });\n"
            "});\n"
            "app.post('/bookings', createBooking);\n"
        ),
    ),
    WorkbenchTask(
        task_id="document-property-availability",
        mode="api_documentation",
        prompt=(
            "Document this property availability endpoint. Explain its path and query "
            "parameters and show the successful response shape."
        ),
        rubric=(
            RubricCheck(
                "availability route",
                r"(?m)^###\s+.*GET.*/properties/[:{]propertyId[}/]availability",
                2,
            ),
            RubricCheck("description section", r"(?i)\*\*Description:\*\*"),
            RubricCheck("query parameter section", r"(?i)Request Payload\s*/\s*Params", 2),
            RubricCheck("date parameters", r"checkIn[\s\S]{0,160}checkOut|checkOut[\s\S]{0,160}checkIn"),
            RubricCheck("success response section", r"(?i)Expected Response\s*\(Success\)"),
        ),
        source_code=(
            "app.get('/properties/:propertyId/availability', (request, response) => {\n"
            "  const { checkIn, checkOut, guests } = request.query;\n"
            "  response.json({ propertyId: request.params.propertyId, available: true, checkIn, checkOut, guests });\n"
            "});\n"
        ),
    ),
    WorkbenchTask(
        task_id="document-booking-update-and-cancel",
        mode="api_documentation",
        prompt=(
            "Document both booking routes separately. Include request details and "
            "the successful response for each route."
        ),
        rubric=(
            RubricCheck("PATCH booking route", r"(?m)^###\s+.*PATCH.*/bookings/[:{]bookingId[}/]", 2),
            RubricCheck("DELETE booking route", r"(?m)^###\s+.*DELETE.*/bookings/[:{]bookingId[}/]", 2),
            RubricCheck("description sections", r"(?i)\*\*Description:\*\*", 2),
            RubricCheck("request sections", r"(?i)Request Payload\s*/\s*Params", 2),
            RubricCheck("success response sections", r"(?i)Expected Response\s*\(Success\)", 2),
        ),
        source_code=(
            "app.patch('/bookings/:bookingId', updateBooking);\n"
            "app.delete('/bookings/:bookingId', cancelBooking);\n"
        ),
    ),
]