# # ==========================================
# # 3. PARSE (cleanup + button classification + structured output)
# # ==========================================

# def app_parse(scraped_data):
#     raw_fields = scraped_data.get("raw_fields", []) or []
#     buttons = scraped_data.get("buttons", []) or []
#     resume_upload = scraped_data.get("resume_upload", {}) or {}
#     counts = scraped_data.get("counts", {}) or {}

#     # ------------------------------------------
#     # DEDUPLICATION
#     # P2-18: selector-less fields bhi ab dedupe hote hain
#     # (name,id,label) identity se — duplicates nahi aate.
#     # ------------------------------------------
#     seen = set()
#     unique_fields = []

#     for field in raw_fields:
#         selector = field.get("selector")
#         if selector:
#             key = ("sel", selector)
#         else:
#             key = (
#                 "nsl",
#                 field.get("name"),
#                 field.get("id"),
#                 field.get("label"),
#             )

#         if key in seen:
#             continue
#         seen.add(key)
#         unique_fields.append(field)

#     # ------------------------------------------
#     # BUTTON CLASSIFICATION
#     # P1-11: exclusion guards — "Save and continue later" NEXT nahi banega,
#     # "Apply profile/resume" SUBMIT nahi banega.
#     # ------------------------------------------
#     NEXT_KEYWORDS = [
#         "next", "continue", "proceed", "go forward",
#         "next step", "save and continue",
#     ]
#     SUBMIT_KEYWORDS = [
#         "submit application", "complete application", "send application",
#         "submit", "apply", "finish",
#     ]
#     NEXT_EXCLUDE = [
#         "later", "draft", "cancel", "exit", "previous", "back", "return to",
#     ]
#     SUBMIT_EXCLUDE = [
#         "later", "draft", "cancel", "exit", "previous", "back",
#         "profile", "resume", "linkedin", "indeed", "saved",
#     ]

#     next_buttons = []
#     submit_buttons = []
#     other_buttons = []

#     for button in buttons:
#         text = (button.get("text") or "").strip().lower()
#         aria_label = (button.get("aria_label") or "").strip().lower()
#         button_text = f"{text} {aria_label}".strip()

#         if any(keyword in button_text for keyword in NEXT_EXCLUDE):
#             button["action"] = "other"
#             other_buttons.append(button)

#         elif any(keyword in button_text for keyword in NEXT_KEYWORDS):
#             button["action"] = "next"
#             next_buttons.append(button)

#         elif any(keyword in button_text for keyword in SUBMIT_EXCLUDE):
#             button["action"] = "other"
#             other_buttons.append(button)

#         elif any(keyword in button_text for keyword in SUBMIT_KEYWORDS):
#             button["action"] = "submit"
#             submit_buttons.append(button)

#         else:
#             button["action"] = "other"
#             other_buttons.append(button)

#     return {
#         "form_found": bool(scraped_data.get("has_form")) or bool(raw_fields),
#         "form_action": scraped_data.get("form_action"),
#         "form_method": scraped_data.get("form_method"),
#         "page_title": scraped_data.get("page_title"),
#         "page_url": scraped_data.get("page_url"),
#         "resume_upload": resume_upload,
#         "fields": unique_fields,
#         "buttons": {
#             "next": next_buttons,
#             "submit": submit_buttons,
#             "other": other_buttons,
#         },
#         "diagnostics": {
#             "forms": counts.get("forms", 0),
#             "native_fields": counts.get("native_fields", 0),
#             "custom_controls": counts.get("custom_controls", 0),
#             "extracted_fields": len(unique_fields),
#             "fields_without_selector": sum(
#                 1 for field in unique_fields if not field.get("selector")
#             ),
#             "readonly_fields": sum(
#                 1
#                 for field in unique_fields
#                 if (field.get("constraints") or {}).get("readonly")
#             ),
#             "extracted_buttons": len(buttons),
#             "next_buttons": len(next_buttons),
#             "submit_buttons": len(submit_buttons),
#             "file_inputs": counts.get("file_inputs", 0),
#             "resume_upload_detected": bool(resume_upload.get("available")),
#         },
#     }


# ==========================================
# 3. PARSE (cleanup + button classification + structured output)
# ==========================================

def app_parse(scraped_data):
    raw_fields = scraped_data.get("raw_fields", []) or []
    buttons = scraped_data.get("buttons", []) or []
    resume_upload = scraped_data.get("resume_upload", {}) or {}
    counts = scraped_data.get("counts", {}) or {}

    # ------------------------------------------
    # DEDUPLICATION
    # P2-18: selector-less fields bhi ab dedupe hote hain
    # (name,id,label) identity se — duplicates nahi aate.
    # ------------------------------------------
    seen = set()
    unique_fields = []

    for field in raw_fields:
        selector = field.get("selector")
        if selector:
            key = ("sel", selector)
        else:
            name = field.get("name")
            field_id = field.get("id")
            label = field.get("label")

            # BUGFIX: all-None identity — two DIFFERENT selector-less
            # fields (e.g. two unlabeled custom radio groups) used to
            # collide on the same key and one question got dropped.
            # Nothing identifies them, so never dedupe these.
            if not name and not field_id and not label:
                unique_fields.append(field)
                continue

            key = (
                "nsl",
                name,
                field_id,
                label,
                field.get("type"),
            )

        if key in seen:
            continue
        seen.add(key)
        unique_fields.append(field)

    # ------------------------------------------
    # BUTTON CLASSIFICATION
    # P1-11: exclusion guards — "Save and continue later" NEXT nahi banega,
    # "Apply profile/resume" SUBMIT nahi banega.
    # ------------------------------------------
    NEXT_KEYWORDS = [
        "next", "continue", "proceed", "go forward",
        "next step", "save and continue",
    ]
    SUBMIT_KEYWORDS = [
        "submit application", "complete application", "send application",
        "submit", "apply", "finish",
    ]
    NEXT_EXCLUDE = [
        "later", "draft", "cancel", "exit", "previous", "back", "return to",
    ]
    SUBMIT_EXCLUDE = [
        "later", "draft", "cancel", "exit", "previous", "back",
        "profile", "resume", "linkedin", "indeed", "saved",
    ]

    next_buttons = []
    submit_buttons = []
    other_buttons = []

    for button in buttons:
        text = (button.get("text") or "").strip().lower()
        aria_label = (button.get("aria_label") or "").strip().lower()
        button_text = f"{text} {aria_label}".strip()

        # BUGFIX: submit check BEFORE next — a button whose text says
        # "submit" (e.g. "Submit and continue") used to match NEXT_KEYWORDS
        # first and was AUTO-CLICKED as a next button, submitting the
        # application prematurely. Anything submit-like now goes to the
        # manual-review path, which is strictly safer.
        if any(keyword in button_text for keyword in NEXT_EXCLUDE) or any(
            keyword in button_text for keyword in SUBMIT_EXCLUDE
        ):
            button["action"] = "other"
            other_buttons.append(button)

        elif any(keyword in button_text for keyword in SUBMIT_KEYWORDS):
            button["action"] = "submit"
            submit_buttons.append(button)

        elif any(keyword in button_text for keyword in NEXT_KEYWORDS):
            button["action"] = "next"
            next_buttons.append(button)

        else:
            button["action"] = "other"
            other_buttons.append(button)

    return {
        "form_found": bool(scraped_data.get("has_form")) or bool(raw_fields),
        "form_action": scraped_data.get("form_action"),
        "form_method": scraped_data.get("form_method"),
        "page_title": scraped_data.get("page_title"),
        "page_url": scraped_data.get("page_url"),
        "resume_upload": resume_upload,
        "fields": unique_fields,
        "buttons": {
            "next": next_buttons,
            "submit": submit_buttons,
            "other": other_buttons,
        },
        "diagnostics": {
            "forms": counts.get("forms", 0),
            "native_fields": counts.get("native_fields", 0),
            "custom_controls": counts.get("custom_controls", 0),
            "extracted_fields": len(unique_fields),
            "fields_without_selector": sum(
                1 for field in unique_fields if not field.get("selector")
            ),
            "readonly_fields": sum(
                1
                for field in unique_fields
                if (field.get("constraints") or {}).get("readonly")
            ),
            "extracted_buttons": len(buttons),
            "next_buttons": len(next_buttons),
            "submit_buttons": len(submit_buttons),
            "file_inputs": counts.get("file_inputs", 0),
            "resume_upload_detected": bool(resume_upload.get("available")),
        },
    }