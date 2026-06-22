import json


def load_complaints():

    with open(
        "data/complaints.json",
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def find_connections(extracted_data):

    complaints = load_complaints()

    connected_cases = []

    current_phones = set(
        extracted_data.get(
            "phone_numbers",
            []
        )
    )

    current_upis = set(
        extracted_data.get(
            "upi_ids",
            []
        )
    )

    current_urls = set(
        extracted_data.get(
            "urls",
            []
        )
    )

    for complaint in complaints:

        complaint_phones = set(
            complaint.get(
                "phone_numbers",
                []
            )
        )

        complaint_upis = set(
            complaint.get(
                "upi_ids",
                []
            )
        )

        complaint_urls = set(
            complaint.get(
                "urls",
                []
            )
        )

        if (
            current_phones & complaint_phones
            or current_upis & complaint_upis
            or current_urls & complaint_urls
        ):

            connected_cases.append(
                complaint
            )

    return connected_cases