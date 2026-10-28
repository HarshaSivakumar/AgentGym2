from .environment import WorkbenchTask


DEFAULT_TASKS = [
    WorkbenchTask(
        task_id="design-create-booking",
        mode="api_design",
        prompt=(
            "Design a TypeScript POST /bookings contract for creating a booking. "
            "The request requires guestId, propertyId, checkIn, and checkOut. "
            "Validate that checkOut is after checkIn. Model validation, conflict, "
            "and infrastructure errors, then provide a guarded skeleton."
        ),
        expected_terms=(
            "CreateBookingRequest",
            "guestId",
            "propertyId",
            "checkIn",
            "checkOut",
            "ValidationError",
            "ConflictError",
        ),
    ),
    WorkbenchTask(
        task_id="document-booking-api",
        mode="api_documentation",
        prompt=(
            "Document every route in the provided source. Include a short "
            "description, request details, and successful response for each route."
        ),
        expected_terms=(
            "GET",
            "/health",
            "POST",
            "/bookings",
            "Request Payload / Params",
            "Expected Response (Success)",
        ),
        source_code=(
            "app.get('/health', (request, response) => {\n"
            "  response.json({ status: 'ok' });\n"
            "});\n"
            "app.post('/bookings', createBooking);\n"
        ),
    ),
]