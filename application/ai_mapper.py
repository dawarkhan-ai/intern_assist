# import json
# import re
# import ollama


# def ai_map(remaining_fields, resume_data, candidate_profile):

#     # ==========================================
#     # 1. NORMALIZE INPUT DATA
#     # ==========================================

#     if isinstance(remaining_fields, str):
#         remaining_fields = json.loads(remaining_fields)

#     if isinstance(resume_data, str):
#         resume_data = json.loads(resume_data)

#     if isinstance(candidate_profile, str):
#         candidate_profile = json.loads(candidate_profile)

#     if not remaining_fields:

#         return {
#             "fields": [],
#             "manual_required_fields": []
#         }

#     website_fields = remaining_fields.get("fields", [])

#     if not website_fields:

#         return {
#             "fields": [],
#             "manual_required_fields": []
#         }

#     resume_personal = resume_data.get("personal_information", {})
#     candidate_personal = candidate_profile.get("personal_information", {})

#     application_answers = candidate_profile.get("application_answers", {})

#     # ==========================================
#     # 2. HELPER FUNCTIONS
#     # ==========================================

#     def get_value(data, *keys):

#         for key in keys:

#             value = data.get(key)

#             if value is not None and str(value).strip():
#                 return str(value).strip()

#         return None

#     def is_empty(value):

#         return (
#             value is None
#             or (isinstance(value, str) and not value.strip())
#         )

#     def normalize(text):

#         return re.sub(
#             r"[^a-z0-9]+",
#             " ",
#             str(text).lower()
#         ).strip()

#     def validate_dropdown(value, options):

#         if value is None:
#             return None

#         if not isinstance(value, (str, int, float)):
#             return None

#         value = str(value).strip()

#         for option in options:

#             if option.get("disabled"):
#                 continue

#             option_value = str(
#                 option.get("value", "")
#             ).strip()

#             option_label = str(
#                 option.get("label", option.get("text", ""))
#             ).strip()

#             if not option_value and not option_label:
#                 continue

#             placeholder = normalize(option_label)

#             if placeholder in [
#                 "please select",
#                 "select",
#                 "choose"
#             ]:
#                 continue

#             if value == option_value or value == option_label:

#                 return option_value if option_value else option_label

#         return None

#     def validate_multiple_dropdown(values, options):

#         if not isinstance(values, list):
#             return None

#         validated = []

#         for value in values:

#             matched = validate_dropdown(value, options)

#             if matched is None:
#                 return None

#             validated.append(matched)

#         return validated if validated else None

#     # ==========================================
#     # 3. PERSONAL / LEGAL DECLARATIONS
#     # ==========================================

#     MANUAL_KEYWORDS = [

#         "government employment",
#         "government organization",
#         "government organisation",
#         "government institution",
#         "public institution",
#         "public body",
#         "government employee",
#         "government contractor",

#         "citizenship",
#         "citizen",
#         "passport",
#         "dual citizenship",
#         "permanent resident",
#         "permanent residency",
#         "refugee",
#         "asylum",

#         "conflict of interest",
#         "family member",
#         "close personal relationship",
#         "personal relationship",

#         "non compete",
#         "noncompete",
#         "non competition",
#         "non solicitation",
#         "non disclosure",
#         "nda",
#         "prior employer agreement",
#         "employment agreement",
#         "restrictive agreement",

#         "work permit",
#         "residency permit",
#         "residence permit",
#         "sponsorship",
#         "visa sponsorship",

#         "regulatory authority",
#         "purchasing from"

#     ]

#     def requires_manual_answer(field):

#         label = normalize(field.get("label", ""))
#         field_id = normalize(field.get("id", ""))

#         combined_text = label + " " + field_id

#         return any(
#             keyword in combined_text
#             for keyword in MANUAL_KEYWORDS
#         )

#     # ==========================================
#     # 4. APPLICATION ANSWER LOOKUP
#     # ==========================================

#     def get_application_answer(field):

#         field_id = field.get("id")

#         # Exact field ID matching

#         if field_id and field_id in application_answers:

#             answer = application_answers[field_id]

#             if answer is not None:

#                 if not isinstance(answer, str) or answer.strip():
#                     return answer

#         # Semantic key matching

#         label = normalize(field.get("label", ""))

#         answer_key_map = {

#             "government employment": "government_employment",
#             "citizenship": "citizenship",
#             "conflict of interest": "conflict_of_interest",
#             "work permit": "work_permit",
#             "residency permit": "residency_permit",
#             "residence permit": "residency_permit",
#             "family member": "family_relationship",
#             "close personal relationship": "family_relationship",
#             "sponsorship": "employment_sponsorship"

#         }

#         for keyword, answer_key in answer_key_map.items():

#             if keyword in label and answer_key in application_answers:

#                 answer = application_answers[answer_key]

#                 if answer is not None:

#                     if not isinstance(answer, str) or answer.strip():
#                         return answer

#         return None

#     # ==========================================
#     # 5. PERSONAL INFORMATION
#     # ==========================================

#     full_name = (
#         get_value(candidate_personal, "full_name", "name")
#         or get_value(resume_personal, "full_name", "name")
#     )

#     email = (
#         get_value(candidate_personal, "email")
#         or get_value(resume_personal, "email")
#     )

#     phone = (
#         get_value(candidate_personal, "phone", "phone_number")
#         or get_value(resume_personal, "phone", "phone_number")
#     )

#     # ==========================================
#     # 6. PREPARE NAME
#     # ==========================================

#     first_name = (
#         get_value(candidate_personal, "first_name", "firstname")
#         or get_value(resume_personal, "first_name", "firstname")
#     )

#     last_name = (
#         get_value(candidate_personal, "last_name", "lastname", "surname")
#         or get_value(resume_personal, "last_name", "lastname", "surname")
#     )

#     # Full name fallback

#     if full_name:

#         name_parts = full_name.split()

#         if not first_name and name_parts:
#             first_name = name_parts[0]

#         if not last_name and len(name_parts) >= 2:
#             last_name = " ".join(name_parts[1:])

#     # ==========================================
#     # 7. MATCH FIELDS
#     # ==========================================

#     mapped_fields = []
#     manual_required_fields = []

#     for index, field in enumerate(website_fields, start=1):

#         label = str(field.get("label") or "")
#         field_type = (field.get("type") or "").lower()
#         label_lower = label.lower()

#         print(
#             f"\nProcessing {index}/{len(website_fields)}: {label}"
#         )

#         value = None
#         value_source = None
#         manual_required = False

#         constraints = field.get("constraints") or {}

#         # ======================================
#         # 8. READONLY FIELDS
#         # ======================================

#         if constraints.get("readonly"):

#             value = field.get("value")

#             if not is_empty(value):
#                 value_source = "website_readonly"

#             else:
#                 value = None

#         # ======================================
#         # 9. PERSONAL / LEGAL DECLARATIONS
#         # ======================================

#         elif requires_manual_answer(field):

#             value = get_application_answer(field)

#             if value is not None:

#                 value_source = "candidate_application_answers"

#             else:

#                 manual_required = True

#                 print("MANUAL REQUIRED:", label)

#         # ======================================
#         # 10. RADIO / CHECKBOX
#         # ======================================

#         elif field_type in ["radio", "radiogroup", "checkbox"]:

#             value = None
#             manual_required = True

#             print("MANUAL REQUIRED:", label)

#         # ======================================
#         # 11. PYTHON-BASED EXACT MATCHING
#         # ======================================

#         elif "first name" in label_lower:

#             value = first_name
#             value_source = "personal_information"

#         elif "last name" in label_lower:

#             value = last_name
#             value_source = "personal_information"

#         elif "email" in label_lower:

#             value = email
#             value_source = "personal_information"

#         elif "phone" in label_lower or "mobile" in label_lower:

#             value = phone
#             value_source = "personal_information"

#         # ======================================
#         # 12. QWEN3 MATCHING
#         # ======================================

#         else:

#             current_field = {

#                 "label": label,
#                 "type": field_type,
#                 "options": field.get("options", []),
#                 "required": field.get("required"),
#                 "constraints": constraints

#             }

#             prompt = f"""
# You are a website application form field matching assistant.

# TASK:
# Find information that directly matches the given field.

# FIELD:
# {json.dumps(current_field, ensure_ascii=False)}

# RESUME:
# {json.dumps(resume_data, ensure_ascii=False)}

# CANDIDATE PROFILE:
# {json.dumps(candidate_profile, ensure_ascii=False)}

# STRICT RULES:

# 1. Use only explicitly available information.
# 2. Never invent, assume, calculate or guess information.
# 3. Missing information must return null.
# 4. Never guess personal, legal, citizenship, government employment,
#    eligibility or declaration questions.
# 5. For city or country, use only explicitly available information.
# 6. For dropdown fields, return an exact available option value or label.
# 7. Never select an unavailable dropdown option.
# 8. Do not confuse different concepts.
# 9. Respect field constraints.
# 10. Return only JSON.

# OUTPUT:
# {{"value": null}}
# """

#             try:

#                 response = ollama.chat(

#                     model="phi4-mini:3.8b-q4_K_M",

#                     messages=[
#                         {
#                             "role": "user",
#                             "content": prompt
#                         }
#                     ],

#                     format="json",

#                     options={
#                         "temperature": 0,
#                         "num_ctx": 16384,
#                         "num_predict": 256
#                     }

#                 )

#                 content = response["message"]["content"]

#                 result = json.loads(content)

#                 value = result.get("value")

#                 if not is_empty(value):
#                     value_source = "qwen"

#                 else:
#                     value = None

#             except Exception as e:

#                 print("Model error:", e)

#                 value = None

#         # ======================================
#         # 13. DROPDOWN VALIDATION
#         # ======================================

#         options = field.get("options", [])

#         if value is not None:

#             if field_type in ["select", "select-one"]:

#                 value = validate_dropdown(
#                     value,
#                     options
#                 )

#                 if value is None:
#                     value_source = None

#             elif field_type == "select-multiple":

#                 value = validate_multiple_dropdown(
#                     value,
#                     options
#                 )

#                 if value is None:
#                     value_source = None

#         # ======================================
#         # 14. TEXT CONSTRAINT VALIDATION
#         # ======================================

#         if value is not None and isinstance(value, str):

#             max_length = constraints.get("max_length")
#             min_length = constraints.get("min_length")

#             if max_length is not None and len(value) > max_length:

#                 print("Warning: Maximum length exceeded.")

#                 value = None
#                 value_source = None

#             elif min_length is not None and len(value) < min_length:

#                 print("Warning: Minimum length not satisfied.")

#                 value = None
#                 value_source = None

#         print("Matched value:", value)
#         print("Value source:", value_source)

#         # ======================================
#         # 15. MANUAL REQUIRED TRACKING
#         # ======================================

#         required = field.get("required")

#         is_required = (
#             required is True
#             or required == 1
#             or str(required).lower() == "true"
#         )

#         if is_required and is_empty(value):

#             manual_required = True

#         if manual_required:

#             manual_required_fields.append({

#                 "id": field.get("id"),
#                 "label": label

#             })

#         # ======================================
#         # 16. SAVE MAPPED OUTPUT
#         # ======================================

#         mapped_fields.append({

#             "selector": field.get("selector"),
#             "widget_selector": field.get("widget_selector"),
#             "is_custom_select": field.get("is_custom_select", False),
#             "container_selector": field.get("container_selector"),

#             "options": options,
#             "constraints": constraints,

#             "name": field.get("name"),
#             "id": field.get("id"),

#             "required": field.get("required", False),
#             "control_visible": field.get("control_visible", True),

#             "label": label,
#             "value": value,
#             "type": field_type,

#             "value_source": value_source,
#             "manual_required": manual_required

#         })

#     # ==========================================
#     # 17. FINAL OUTPUT
#     # ==========================================

#     return {

#         "fields": mapped_fields,

#         "manual_required_fields": manual_required_fields

#     }





import json
import re
import ollama


def ai_map(remaining_fields, resume_data, candidate_profile):

    # ==========================================
    # 1. NORMALIZE INPUT DATA
    # ==========================================

    if isinstance(remaining_fields, str):
        remaining_fields = json.loads(remaining_fields)

    if isinstance(resume_data, str):
        resume_data = json.loads(resume_data)

    if isinstance(candidate_profile, str):
        candidate_profile = json.loads(candidate_profile)

    # BUGFIX: callers may pass None — never crash on .get()
    resume_data = resume_data or {}
    candidate_profile = candidate_profile or {}

    # BUGFIX: accept a bare list of fields too; always work with a dict
    if isinstance(remaining_fields, list):
        remaining_fields = {"fields": remaining_fields}
    if not isinstance(remaining_fields, dict):
        remaining_fields = {}

    if not remaining_fields:

        return {
            "fields": [],
            "manual_required_fields": []
        }

    website_fields = remaining_fields.get("fields", [])

    if not website_fields:

        return {
            "fields": [],
            "manual_required_fields": []
        }

    resume_personal = resume_data.get("personal_information", {})
    candidate_personal = candidate_profile.get("personal_information", {})

    application_answers = candidate_profile.get("application_answers", {})

    # ==========================================
    # 2. HELPER FUNCTIONS
    # ==========================================

    def get_value(data, *keys):

        for key in keys:

            value = data.get(key)

            if value is not None and str(value).strip():
                return str(value).strip()

        return None

    def is_empty(value):

        return (
            value is None
            or (isinstance(value, str) and not value.strip())
        )

    def normalize(text):

        return re.sub(
            r"[^a-z0-9]+",
            " ",
            str(text).lower()
        ).strip()

    def validate_dropdown(value, options):

        if value is None:
            return None

        if not isinstance(value, (str, int, float)):
            return None

        value = str(value).strip()

        for option in options:

            if option.get("disabled"):
                continue

            option_value = str(
                option.get("value", "")
            ).strip()

            option_label = str(
                option.get("label", option.get("text", ""))
            ).strip()

            if not option_value and not option_label:
                continue

            placeholder = normalize(option_label)

            if placeholder in [
                "please select",
                "select",
                "select one",
                "select an option",
                "choose",
                "choose one",
                "please choose one"
            ]:
                continue

            if value == option_value or value == option_label:

                return option_value if option_value else option_label

        return None

    def validate_multiple_dropdown(values, options):

        if not isinstance(values, list):
            return None

        validated = []

        for value in values:

            matched = validate_dropdown(value, options)

            if matched is None:
                return None

            validated.append(matched)

        return validated if validated else None

    # ==========================================
    # 3. PERSONAL / LEGAL DECLARATIONS
    # ==========================================

    MANUAL_KEYWORDS = [

        "government employment",
        "government organization",
        "government organisation",
        "government institution",
        "public institution",
        "public body",
        "government employee",
        "government contractor",

        "citizenship",
        "citizen",
        "passport",
        "dual citizenship",
        "permanent resident",
        "permanent residency",
        "refugee",
        "asylum",

        "conflict of interest",
        "family member",
        "close personal relationship",
        "personal relationship",

        "non compete",
        "noncompete",
        "non competition",
        "non solicitation",
        "non disclosure",
        "nda",
        "prior employer agreement",
        "employment agreement",
        "restrictive agreement",

        "work permit",
        "residency permit",
        "residence permit",
        "sponsorship",
        "visa sponsorship",

        "regulatory authority",
        "purchasing from"

    ]

    def requires_manual_answer(field):

        label = normalize(field.get("label", ""))
        field_id = normalize(field.get("id", ""))

        combined_text = label + " " + field_id

        return any(
            keyword in combined_text
            for keyword in MANUAL_KEYWORDS
        )

    # ==========================================
    # 4. APPLICATION ANSWER LOOKUP
    # ==========================================

    def get_application_answer(field):

        field_id = field.get("id")

        # Exact field ID matching

        if field_id and field_id in application_answers:

            answer = application_answers[field_id]

            if answer is not None:

                if not isinstance(answer, str) or answer.strip():
                    return answer

        # Semantic key matching

        label = normalize(field.get("label", ""))

        answer_key_map = {

            "government employment": "government_employment",
            "citizenship": "citizenship",
            "conflict of interest": "conflict_of_interest",
            "work permit": "work_permit",
            "residency permit": "residency_permit",
            "residence permit": "residency_permit",
            "family member": "family_relationship",
            "close personal relationship": "family_relationship",
            "sponsorship": "employment_sponsorship"

        }

        for keyword, answer_key in answer_key_map.items():

            if keyword in label and answer_key in application_answers:

                answer = application_answers[answer_key]

                if answer is not None:

                    if not isinstance(answer, str) or answer.strip():
                        return answer

        return None

    # ==========================================
    # 5. PERSONAL INFORMATION
    # ==========================================

    full_name = (
        get_value(candidate_personal, "full_name", "name")
        or get_value(resume_personal, "full_name", "name")
    )

    email = (
        get_value(candidate_personal, "email")
        or get_value(resume_personal, "email")
    )

    phone = (
        get_value(candidate_personal, "phone", "phone_number")
        or get_value(resume_personal, "phone", "phone_number")
    )

    # ==========================================
    # 6. PREPARE NAME
    # ==========================================

    first_name = (
        get_value(candidate_personal, "first_name", "firstname")
        or get_value(resume_personal, "first_name", "firstname")
    )

    last_name = (
        get_value(candidate_personal, "last_name", "lastname", "surname")
        or get_value(resume_personal, "last_name", "lastname", "surname")
    )

    # Full name fallback

    if full_name:

        name_parts = full_name.split()

        if not first_name and name_parts:
            first_name = name_parts[0]

        if not last_name and len(name_parts) >= 2:
            last_name = " ".join(name_parts[1:])

    # ==========================================
    # 7. MATCH FIELDS
    # ==========================================

    mapped_fields = []
    manual_required_fields = []

    for index, field in enumerate(website_fields, start=1):

        label = str(field.get("label") or "")
        field_type = (field.get("type") or "").lower()
        label_lower = label.lower()

        print(
            f"\nProcessing {index}/{len(website_fields)}: {label}"
        )

        value = None
        value_source = None
        manual_required = False

        # BUGFIX: constraints may be missing or a non-dict — .get() crashed
        constraints = field.get("constraints")
        if not isinstance(constraints, dict):
            constraints = {}

        # ======================================
        # 8. READONLY FIELDS
        # ======================================

        if constraints.get("readonly"):

            value = field.get("value")

            if not is_empty(value):
                value_source = "website_readonly"

            else:
                value = None

        # ======================================
        # 9. PERSONAL / LEGAL DECLARATIONS
        # ======================================

        elif requires_manual_answer(field):

            value = get_application_answer(field)

            if value is not None:

                value_source = "candidate_application_answers"

            else:

                manual_required = True

                print("MANUAL REQUIRED:", label)

        # ======================================
        # 10. RADIO / CHECKBOX
        # ======================================

        elif field_type in ["radio", "radiogroup", "checkbox"]:

            # BUGFIX: an explicitly recorded application answer must win
            # over forcing a manual answer — the answer lookup was only
            # reachable through the declarative-question branch, so radio/
            # checkbox fields with a known field id were ALWAYS manual.
            value = get_application_answer(field)

            if value is not None:

                value_source = "candidate_application_answers"

            else:

                value = None
                manual_required = True

                print("MANUAL REQUIRED:", label)

        # ======================================
        # 11. PYTHON-BASED EXACT MATCHING
        # ======================================

        elif "first name" in label_lower:

            value = first_name
            value_source = "personal_information"

        elif "last name" in label_lower:

            value = last_name
            value_source = "personal_information"

        elif "email" in label_lower:

            value = email
            value_source = "personal_information"

        elif (
            "country code" in label_lower
            and (
                field_type in ["select", "combobox", "dropdown", "selectbox"]
                or "country" in (
                    str(field.get("name") or "")
                    + " "
                    + str(field.get("id") or "")
                ).lower()
                or bool(field.get("options"))
            )
        ):
            # BUGFIX: dedicated phone country-code selector. The FULL phone
            # number used to land in this field, because "phone" in
            # "phone country code" matched the generic phone branch below.
            # Only the leading +NN prefix belongs here. (Labels like
            # Lever's "Phone (include country code)" are plain text inputs
            # without country in name/id and without options, so they
            # still fall through to the full-phone branch.)
            prefix_match = re.match(r"^\s*(\+\d{1,4})", phone or "")

            if prefix_match:

                value = prefix_match.group(1)
                value_source = "personal_information"

        elif "phone" in label_lower or "mobile" in label_lower:

            value = phone
            value_source = "personal_information"

        # ======================================
        # 12. LLM (OLLAMA) MATCHING
        # ======================================

        else:

            current_field = {

                "label": label,
                "type": field_type,
                "options": field.get("options", []),
                "required": field.get("required"),
                "constraints": constraints

            }

            prompt = f"""
You are a website application form field matching assistant.

TASK:
Find information that directly matches the given field.

FIELD:
{json.dumps(current_field, ensure_ascii=False)}

RESUME:
{json.dumps(resume_data, ensure_ascii=False)}

CANDIDATE PROFILE:
{json.dumps(candidate_profile, ensure_ascii=False)}

STRICT RULES:

1. Use only explicitly available information.
2. Never invent, assume, calculate or guess information.
3. Missing information must return null.
4. Never guess personal, legal, citizenship, government employment,
   eligibility or declaration questions.
5. For city or country, use only explicitly available information.
6. For dropdown fields, return an exact available option value or label.
7. Never select an unavailable dropdown option.
8. Do not confuse different concepts.
9. Respect field constraints.
10. Return only JSON.

OUTPUT:
{{"value": null}}
"""

            try:

                response = ollama.chat(

                    model="phi4-mini:3.8b-q4_K_M",

                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    format="json",

                    options={
                        "temperature": 0,
                        "num_ctx": 16384,
                        "num_predict": 256
                    }

                )

                content = response["message"]["content"]

                result = json.loads(content)

                value = result.get("value")

                if not is_empty(value):
                    # BUGFIX: the source tag said "qwen" but the configured
                    # model is phi4-mini — renamed to the neutral "llm".
                    value_source = "llm"

                else:
                    value = None

            except Exception as e:

                print("Model error:", e)

                value = None

        # ======================================
        # 13. DROPDOWN VALIDATION
        # ======================================

        options = field.get("options", [])

        if value is not None:

            # BUGFIX: combobox/dropdown/selectbox types were not validated,
            # so an unvalidated LLM value could reach filler for custom
            # dropdowns and fail there.
            if field_type in [
                "select", "select-one", "combobox",
                "dropdown", "selectbox",
            ]:

                value = validate_dropdown(
                    value,
                    options
                )

                if value is None:
                    value_source = None

            elif field_type == "select-multiple":

                value = validate_multiple_dropdown(
                    value,
                    options
                )

                if value is None:
                    value_source = None

        # ======================================
        # 14. TEXT CONSTRAINT VALIDATION
        # ======================================

        if value is not None and isinstance(value, str):

            max_length = constraints.get("max_length")
            min_length = constraints.get("min_length")

            if max_length is not None and len(value) > max_length:

                print("Warning: Maximum length exceeded.")

                value = None
                value_source = None

            elif min_length is not None and len(value) < min_length:

                print("Warning: Minimum length not satisfied.")

                value = None
                value_source = None

        print("Matched value:", value)
        print("Value source:", value_source)

        # ======================================
        # 15. MANUAL REQUIRED TRACKING
        # ======================================

        required = field.get("required")

        is_required = (
            required is True
            or required == 1
            or str(required).lower() == "true"
        )

        if is_required and is_empty(value):

            manual_required = True

        if manual_required:

            manual_required_fields.append({

                "id": field.get("id"),
                "label": label,
                # BUGFIX: filler decides mandatory_status (0/1/2) from the
                # `required` flag on manual entries — it was missing, so
                # every required manual question was treated as optional
                # and the flow auto-clicked Next past unanswered questions.
                "required": bool(is_required),
                "reason": "Candidate input required.",

            })

        # ======================================
        # 16. SAVE MAPPED OUTPUT
        # ======================================

        mapped_fields.append({

            "selector": field.get("selector"),
            "widget_selector": field.get("widget_selector"),
            "is_custom_select": field.get("is_custom_select", False),
            "container_selector": field.get("container_selector"),

            "options": options,
            "constraints": constraints,

            # BUGFIX: pass the contenteditable flag through so filler can
            # route rich-text fields to the correct branch.
            "contenteditable": bool(field.get("contenteditable")),

            "name": field.get("name"),
            "id": field.get("id"),

            # BUGFIX: bool() — a None `required` leaked into mapped fields
            # and made filler treat required fields as optional.
            "required": bool(field.get("required", False)),
            "control_visible": field.get("control_visible", True),

            "label": label,
            "value": value,
            "type": field_type,

            "value_source": value_source,
            "manual_required": manual_required

        })

    # ==========================================
    # 17. FINAL OUTPUT
    # ==========================================

    return {

        "fields": mapped_fields,

        "manual_required_fields": manual_required_fields

    }