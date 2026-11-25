# # ==========================================
# # 1. IMPORTS
# # ==========================================
# import re


# # ==========================================
# # 2. PUBLIC EXPORTS
# # ==========================================
# __all__ = [
#     "PORTAL_CONFIG",
#     "match_option",
#     "is_required",
#     "requires_manual_answer",
#     "is_empty",
#     "canonical",
#     "clean_value",
#     "flatten_data",
#     "get_source_value",
#     "click_apply_button",
#     "pick_visible_button",
#     "click_next_button",
#     "merge",
# ]


# # ==========================================
# # 3. PORTAL CONFIGURATION
# # ==========================================
# PORTAL_CONFIG = {
#     "resume_file_input": ".resume-upload-wrapper input[type='file']",
#     "uploaded_file_name": ".has-resume .uploadedFileName",
#     "download_file_link": ".has-resume a.downloadFile[href]",
#     "email_edit_button": "button.communication-channel__value-email-edit",
#     "resume_max_mb": 1,
#     "resume_allowed_extensions": (".doc", ".docx", ".html", ".pdf", ".txt"),
#     "dropdown_timeout_ms": 5000,
#     "upload_verify_timeout_ms": 15000,
# }


# # ==========================================
# # 4. FIELD TYPE CONSTANTS
# # ==========================================

# # Choice-like field types handled by the option-matching branch
# _RADIO_TYPES = {"radio", "radiogroup", "radiobutton", "radio_group"}

# _CHECK_TYPES = {
#     "checkbox", "checkboxes", "checkbox_group",
#     "multiselect", "multi_select", "multiplechoice",
#     "select_multiple", "multi_selectbox",
# }

# _CHOICE_TYPES = _RADIO_TYPES | _CHECK_TYPES

# # Dropdown types that must be validated against options
# _SELECT_TYPES = {"select", "combobox", "selectbox", "dropdown"}


# # ==========================================
# # 5. NORMALIZATION & UTILITY HELPERS
# # ==========================================

# def _norm(value):
#     """Lowercase and collapse whitespace."""
#     return re.sub(r"\s+", " ", str(value or "").strip().lower())


# def _alnum(value):
#     """Sirf a-z0-9 — punctuation-insensitive fallback compare."""
#     return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


# def _alias_norm(text):
#     """Field-name/label <-> alias matching normalizer (non-alnum -> space)."""
#     return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


# def _norm_option_text(value):
#     if value is None:
#         return ""
#     s = str(value).strip().lower()
#     s = re.sub(r"[\s_-]+", " ", s)
#     return s


# def _is_checkbox_type(field_type):
#     return (
#         field_type in _CHECK_TYPES
#         or field_type.startswith("checkbox")
#         or field_type.startswith("multi")
#     )


# def _as_choice_list(raw):
#     """Normalize any raw profile value into a list of wanted items."""
#     if raw is None:
#         return []
#     if isinstance(raw, str):
#         return [item.strip() for item in raw.split(",") if item.strip()]
#     if isinstance(raw, (list, tuple, set)):
#         return [str(item).strip() for item in raw if str(item).strip()]
#     return [str(raw).strip()]


# def is_empty(value):
#     return (
#         value is None
#         or (isinstance(value, str) and not value.strip())
#     )


# # ==========================================
# # 6. OPTION MATCHING HELPERS
# # ==========================================

# def _option_fields(opt):
#     if isinstance(opt, dict):
#         return opt
#     return {"value": opt, "label": opt}


# def match_option(options, value):
#     """Fuzzy-match `value` against an options list.

#     Accepts dict options ({value, label, text}) or plain strings.
#     Returns the matched option dict, or None.
#     """
#     if not options or value is None:
#         return None

#     if isinstance(value, bool):
#         target = _norm_option_text("yes" if value else "no")
#         target_raw = value
#     else:
#         target = _norm_option_text(value)
#         target_raw = value

#     opts = [_option_fields(o) for o in options]

#     # 1. exact value / label / text
#     for opt in opts:
#         for k in ("value", "label", "text"):
#             if opt.get(k) is None:
#                 continue
#             if str(opt.get(k)).strip() == str(target_raw).strip():
#                 return opt

#     # 2. normalized comparison
#     for opt in opts:
#         for k in ("value", "label", "text"):
#             if opt.get(k) is not None and _norm_option_text(opt.get(k)) == target:
#                 return opt

#     # 3. containment (option text contains the value or vice versa)
#     for opt in opts:
#         for k in ("value", "label", "text"):
#             ov = opt.get(k)
#             if ov is None:
#                 continue
#             on = _norm_option_text(ov)
#             if on and (on in target or target in on):
#                 return opt
#     return None

# # ==========================================
# # 7. FIELD VALIDATION & DETECTION
# # ==========================================

# def is_required(field):
#     if not isinstance(field, dict):
#         return False
#     if bool(field.get("required")):
#         return True
#     constraints = field.get("constraints")
#     if isinstance(constraints, dict):
#         if bool(constraints.get("required")) or bool(constraints.get("mandatory")):
#             return True
#     if field.get("isRequired") is True:          # Ashby style
#         return True
#     return False


# _DECLARATIVE_PATTERNS = [
#     r"are you (legally )?authorized",
#     r"legally (authorized|allowed) to work",
#     r"sponsor(ship)?",
#     r"visa",
#     r"work permit",
#     r"(minimum|acceptable) (salary|compensation|pay)",
#     r"salary expectation",
#     r"notice period",
#     r"willing to (relocate|travel|undergo|submit)",
#     r"background check",
#     r"drug test",
#     r"self[- ]identif",
#     r"gender",
#     r"race",
#     r"ethnic",
#     r"veteran",
#     r"disability",
#     r"sexual orientation",
#     r"i (hereby )?(agree|consent|accept|certify|confirm|acknowledge)",
#     r"(agree|consent) to (the|our)",
#     r"terms and conditions",
#     r"privacy (policy|notice)",
#     r"over the age",
#     r"18 years",
#     r"how did you hear",
#     r"referral source",
#     r"do you (have|own|possess)",
#     r"are you (a|an) ",
#     r"can you ",
#     r"have you (ever|been)",
#     r"why do you",
#     r"describe ",
#     r"tell us ",
# ]

# _DECLARATIVE_RE = re.compile("|".join(_DECLARATIVE_PATTERNS))


# def requires_manual_answer(field):
#     """True for declarative/eligibility/consent questions."""
#     if not isinstance(field, dict):
#         return False
#     label = _norm(field.get("label"))
#     name = _norm(field.get("name"))
#     text = f"{label} {name}"
#     return bool(_DECLARATIVE_RE.search(text))


# # ==========================================
# # 8. FIELD ALIASES + GUARDS
# # ==========================================

# FIELD_ALIASES = {
#     "name": ["name", "full_name", "fullname", "candidate_name"],
#     "first_name": ["first_name", "firstname", "given_name", "fname"],
#     "last_name": ["last_name", "lastname", "family_name", "surname", "lname"],
#     "email": ["email", "email_address", "primary_email"],
#     "phone": ["phone", "phone_number", "mobile", "mobile_number", "telephone"],
#     "phone_country_code": ["phone_country_code", "country_code"],
#     "location": ["location", "current_location", "city", "address"],
#     "linkedin": ["linkedin", "linkedin_url", "linkedin_profile"],
#     "portfolio": ["portfolio", "website", "personal_website", "url"],
#     "github": ["github", "github_url", "github_profile"],
#     "current_company": ["current_company", "company", "employer"],
#     "current_title": ["current_title", "title", "job_title", "designation"],
#     "years_of_experience": ["years_of_experience", "total_experience", "experience_years"],
#     "salary_expectation": ["salary_expectation", "expected_salary", "salary"],
#     "relocate": ["relocate", "willing_to_relocate", "open_to_relocation"],
#     "education": ["education", "university", "school", "degree"],
#     "cover_letter": ["cover_letter", "coverletter"],
#     "notice_period": ["notice_period", "available_from", "availability"],
#     "gender": ["gender"],
#     "veteran_status": ["veteran_status", "veteran"],
#     "disability_status": ["disability_status", "disability"],
#     "race_ethnicity": ["race_ethnicity", "race", "ethnicity"],
#     "work_authorization": ["work_authorization", "legally_authorized"],
#     "sponsorship": ["sponsorship", "require_sponsorship"],
#     "preferred_name": ["preferred_name", "nickname"],
#     "dob": ["dob", "date_of_birth", "birthday"],
#     "nationality": ["nationality", "citizenship"],
# }


# GENERIC_GUARDS = {
#     "name": [
#         "company", "manager", "reference", "referrer", "referral", "referred",
#         "emergency", "father", "mother", "guardian", "spouse", "relative",
#         "friend", "agency", "recruiter", "supervisor", "school", "college",
#         "university", "institute", "employee", "contact", "alternate", "job",
#         "requisition", "user", "account", "firm", "vendor", "clinic",
#         "hospital", "doctor", "physician", "veteran", "previous", "past",
#         "maiden",
#     ],
#     "email": [
#         "company", "work", "alternate", "reference", "emergency",
#         "school", "college",
#     ],
#     "phone": [
#         "company", "work", "alternate", "reference", "emergency", "fax",
#         "school", "college",
#     ],
#     "location": ["job", "work", "preferred", "office", "relocation"],
#     "address": [
#         "company", "work", "school", "billing", "previous", "past",
#         "employer", "permanent",
#     ],
#     "skills": [],
# }


# MANUAL_KEYWORDS = [
#     "government employment",
#     "government organization",
#     "government organisation",
#     "government employee",

#     "citizenship",
#     "citizen",
#     "passport",
#     "dual citizenship",
#     "permanent resident",

#     "conflict of interest",
#     "family member",
#     "personal relationship",

#     "non compete",
#     "noncompete",
#     "nda",

#     "work permit",
#     "residency permit",
#     "residence permit",

#     "sponsorship",
#     "visa sponsorship",
#     "require sponsorship",

#     "authorized to work",
#     "legally authorized",
#     "eligible to work",
#     "right to work",
#     "visa status",
#     "employment eligibility",

#     "regulatory authority",
#     "criminal conviction",
#     "background check",
#     "export control",

#     # sensitive self-identification — candidate ko khud answer karna chahiye
#     "veteran",
#     "disability",
#     "ethnic",
#     "race",
#     "gender",
#     "religion",
#     "pregnan",
#     "sexual orientation",
# ]


# def canonical(value):
#     """Normalize a label/name/id into a canonical snake_case key."""
#     if value is None:
#         return None
#     s = str(value).strip().lower()
#     if not s:
#         return None
#     s = re.sub(r"[^a-z0-9]+", "_", s)
#     s = re.sub(r"_+", "_", s).strip("_")

#     # synonym collapse
#     synonyms = {
#         "first_name": "first_name",
#         "firstname": "first_name",
#         "last_name": "last_name",
#         "lastname": "last_name",
#         "surname": "last_name",
#         "full_name": "name",
#         "fullname": "name",
#         "candidate_name": "name",
#         "your_name": "name",
#         "email": "email",
#         "email_address": "email",
#         "e_mail": "email",
#         "phone": "phone",
#         "phone_number": "phone",
#         "mobile": "phone",
#         "mobile_number": "phone",
#         "telephone": "phone",
#         "contact_number": "phone",
#         "phone_country_code": "phone_country_code",
#         "country_code": "phone_country_code",
#         "country": "country",
#         "city": "location",
#         "current_city": "location",
#         "location": "location",
#         "address": "location",
#         "linkedin_profile": "linkedin",
#         "linkedin_url": "linkedin",
#         "linkedin": "linkedin",
#         "github_profile": "github",
#         "github_url": "github",
#         "website": "portfolio",
#         "portfolio": "portfolio",
#         "personal_website": "portfolio",
#         "current_company": "current_company",
#         "employer": "current_company",
#         "company": "current_company",
#         "current_job_title": "current_title",
#         "job_title": "current_title",
#         "current_title": "current_title",
#         "designation": "current_title",
#         "expected_salary": "salary_expectation",
#         "salary_expectation": "salary_expectation",
#         "minimum_salary": "salary_expectation",
#         "salary_expectations": "salary_expectation",
#         "notice_period": "notice_period",
#         "willing_to_relocate": "relocate",
#         "relocation": "relocate",
#         "years_of_experience": "years_of_experience",
#         "total_years_of_experience": "years_of_experience",
#     }
#     return synonyms.get(s, s)

# # ==========================================
# # 9. PROFILE / RESUME DATA HELPERS
# # ==========================================

# def clean_value(value):
#     """Normalize a raw source value; None when empty."""
#     if value is None:
#         return None
#     if isinstance(value, str):
#         s = value.strip()
#         return s if s else None
#     if isinstance(value, bool):
#         return value
#     if isinstance(value, (int, float)):
#         return value
#     if isinstance(value, list):
#         cleaned = [clean_value(v) for v in value]
#         cleaned = [v for v in cleaned if v is not None]
#         return cleaned if cleaned else None
#     if isinstance(value, dict):
#         return value if value else None
#     return value


# def flatten_data(data):
#     """Flatten nested dicts (and lists of dicts) into a single-level map.

#     Produces both bare leaf keys ("email") and dotted paths
#     ("personal.email"), so get_source_value can match aliases either way.
#     """
#     flat = {}

#     if not isinstance(data, dict):
#         return flat

#     def _walk(prefix, obj):
#         if isinstance(obj, dict):
#             for key, val in obj.items():
#                 path = f"{prefix}.{key}" if prefix else str(key)
#                 _walk(path, val)
#         elif isinstance(obj, list):
#             scalars = [
#                 v for v in obj
#                 if isinstance(v, (str, int, float, bool))
#             ]
#             if scalars:
#                 flat.setdefault(prefix, scalars)
#             for i, item in enumerate(obj):
#                 if isinstance(item, (dict, list)):
#                     _walk(f"{prefix}[{i}]", item)
#         else:
#             if obj is not None:
#                 flat.setdefault(prefix, obj)
#                 # also expose the bare leaf key for alias matching
#                 bare = prefix.rsplit(".", 1)[-1]
#                 bare = re.sub(r"\[\d+\]$", "", bare)
#                 flat.setdefault(bare, obj)

#     _walk("", data)
#     return flat


# def get_source_value(flat, aliases):
#     """Return the first non-empty value matching any alias key/path."""
#     if not isinstance(flat, dict) or not aliases:
#         return None

#     for alias in aliases:
#         # exact key
#         if alias in flat:
#             val = clean_value(flat[alias])
#             if val is not None:
#                 return val
#         # dotted-path suffix match (e.g. "personal.email" for alias "email")
#         for key, val in flat.items():
#             if "." in key or "[" in key:
#                 tail = key.rsplit(".", 1)[-1]
#                 tail = re.sub(r"\[\d+\]$", "", tail)
#                 if tail == alias:
#                     cleaned = clean_value(val)
#                     if cleaned is not None:
#                         return cleaned
#     return None


# # ==========================================
# # 10. APPLY BUTTON HANDLING
# # ==========================================

# def click_apply_button(page, apply_actions):

#     if not apply_actions:
#         return False

#     # Find the first enabled Apply action
#     apply_button = next(
#         (
#             action for action in apply_actions
#             if action.get("enabled", False)
#         ),
#         None
#     )

#     if not apply_button:
#         return False

#     # 1. Try scraped CSS selector
#     selector = apply_button.get("selector")

#     if selector:
#         locator = page.locator(selector)

#     # 2. Fallback: ID
#     elif apply_button.get("id"):
#         locator = page.locator(
#             f"#{apply_button['id']}"
#         )

#     # 3. Fallback: href
#     elif apply_button.get("url"):
#         locator = page.locator(
#             f'{apply_button["tag"]}[href]'
#         ).filter(
#             has_text=apply_button.get("text", "")
#         )

#     # 4. Fallback: text
#     else:
#         locator = page.locator(
#             apply_button["tag"]
#         ).filter(
#             has_text=apply_button.get("text", "")
#         )

#     # Check locator
#     if locator.count() == 0:
#         return False

#     locator = locator.first

#     if not locator.is_visible():
#         return False

#     if not locator.is_enabled():
#         return False

#     # Click
#     locator.click(timeout=10000)

#     return True


# # ==========================================
# # 11. VISIBLE BUTTON SELECTION
# # ==========================================

# def pick_visible_button(page, buttons):
#     """P0-3: buttons LIST me se pehla visible+enabled button pick karo.

#     Sticky header/footer me 2 next buttons ho sakte hain — hidden wala
#     nahi, chalu wala chahiye. Koi visible na mile to None.
#     """
#     for button in buttons or []:
#         if not isinstance(button, dict):
#             continue
#         selector = button.get("selector")
#         if not selector:
#             continue
#         try:
#             locator = page.locator(selector).first
#             if locator.is_visible() and locator.is_enabled():
#                 return button
#         except Exception:
#             continue
#     return None


# # ==========================================
# # 12. NEXT BUTTON CLICK (NAVIGATION DETECTION)
# # ==========================================

# def click_next_button(page, button_data,logger):
#     if not isinstance(button_data, dict):
#         logger.error("Next button data invalid (dict expected, got %s).",
#                      type(button_data).__name__)
#         return False

#     if not button_data:
#         logger.warning("Next button not found.")
#         return False

#     try:
#         selector = button_data.get("selector")

#         if not selector:
#             logger.warning("Button selector missing.")
#             return False

#         button = page.locator(selector).first

#         if not button.is_visible():
#             logger.warning("Next button is not visible.")
#             return False

#         if not button.is_enabled():
#             logger.warning("Next button is disabled.")
#             return False

#         # Capture current page state
#         old_url = page.url
#         old_fields = page.locator("input, select, textarea").count()

#         # Click button
#         button.click(timeout=10000)
#         logger.info("Next button click attempted.")

#         # Wait for possible SPA or normal navigation
#         try:
#             page.wait_for_function(
#                 "(oldUrl) => window.location.href !== oldUrl",
#                 arg=old_url,
#                 timeout=5000,
#             )
#         except Exception:
#             pass

#         # Allow DOM updates
#         page.wait_for_timeout(2000)

#         # Check current page state
#         new_url = page.url
#         new_fields = page.locator("input, select, textarea").count()

#         # Check HTML validation
#         invalid_fields = page.locator(
#             "input:invalid, select:invalid, textarea:invalid"
#         )
#         invalid_count = invalid_fields.count()

#         logger.info(
#             "URL: %s -> %s | fields: %d -> %d | invalid: %d",
#             old_url, new_url, old_fields, new_fields, invalid_count,
#         )

#         # Navigation detection
#         if new_url != old_url or new_fields != old_fields:
#             logger.info("Page transition detected.")
#             return True

#         if invalid_count > 0:
#             logger.warning("Form validation failed.")
#             for i in range(invalid_count):
#                 field = invalid_fields.nth(i)
#                 logger.warning(
#                     "  %s -> %s",
#                     field.get_attribute("name"),
#                     field.evaluate("(el) => el.validationMessage"),
#                 )
#             return False

#         logger.warning("No page transition detected.")
#         return False

#     except Exception as exc:
#         logger.error("Next button error: %s", exc)
#         return False


# def merge(ruled_output, ai_output=None):

#     ruled_output = ruled_output or {}
#     ai_output = ai_output or {}

#     merged_fields = []
#     seen_field_keys = set()

#     def get_field_key(field):
#         return (
#             field.get("selector")
#             or field.get("id")
#             or field.get("name")
#             or (field.get("label"), field.get("type"))
#         )

#     # 1. Merge mapped fields (ruled_output gets priority)
#     for field in ruled_output.get("fields", []):
#         key = get_field_key(field)
#         seen_field_keys.add(key)
#         merged_fields.append(field)

#     for field in ai_output.get("fields", []):
#         key = get_field_key(field)
#         if key not in seen_field_keys:
#             seen_field_keys.add(key)
#             merged_fields.append(field)

#     # 2. Merge manual_required_fields without duplicates
#     merged_manual_fields = []
#     seen_manual_keys = set()

#     def get_manual_key(item):
#         return (item.get("id"), item.get("label"))

#     for item in ruled_output.get("manual_required_fields", []):
#         key = get_manual_key(item)
#         if key not in seen_manual_keys:
#             seen_manual_keys.add(key)
#             merged_manual_fields.append(item)

#     for item in ai_output.get("manual_required_fields", []):
#         key = get_manual_key(item)
#         if key not in seen_manual_keys:
#             seen_manual_keys.add(key)
#             merged_manual_fields.append(item)

#     return {
#         "fields": merged_fields,
#         "manual_required_fields": merged_manual_fields
#     }




import re


# ==========================================
# 2. PUBLIC EXPORTS
# ==========================================
__all__ = [
    "PORTAL_CONFIG",
    "match_option",
    "is_required",
    "requires_manual_answer",
    "is_empty",
    "canonical",
    "clean_value",
    "flatten_data",
    "get_source_value",
    "click_apply_button",
    "pick_visible_button",
    "click_next_button",
    "merge",
]


# ==========================================
# 3. PORTAL CONFIGURATION
# ==========================================
PORTAL_CONFIG = {
    "resume_file_input": ".resume-upload-wrapper input[type='file']",
    "uploaded_file_name": ".has-resume .uploadedFileName",
    "download_file_link": ".has-resume a.downloadFile[href]",
    "email_edit_button": "button.communication-channel__value-email-edit",
    "resume_max_mb": 1,
    "resume_allowed_extensions": (".doc", ".docx", ".html", ".pdf", ".txt"),
    "dropdown_timeout_ms": 5000,
    "upload_verify_timeout_ms": 15000,
}


# ==========================================
# 4. FIELD TYPE CONSTANTS
# ==========================================

# Choice-like field types handled by the option-matching branch
_RADIO_TYPES = {"radio", "radiogroup", "radiobutton", "radio_group"}

_CHECK_TYPES = {
    "checkbox", "checkboxes", "checkbox_group",
    "multiselect", "multi_select", "multiplechoice",
    "select_multiple", "multi_selectbox",
}

_CHOICE_TYPES = _RADIO_TYPES | _CHECK_TYPES

# Dropdown types that must be validated against options
_SELECT_TYPES = {"select", "combobox", "selectbox", "dropdown"}


# ==========================================
# 5. NORMALIZATION & UTILITY HELPERS
# ==========================================

def _norm(value):
    """Lowercase and collapse whitespace."""
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _alnum(value):
    """Sirf a-z0-9 — punctuation-insensitive fallback compare."""
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _alias_norm(text):
    """Field-name/label <-> alias matching normalizer (non-alnum -> space)."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _norm_option_text(value):
    if value is None:
        return ""
    s = str(value).strip().lower()
    s = re.sub(r"[\s_-]+", " ", s)
    return s


def _is_checkbox_type(field_type):
    # BUGFIX: guard against None/empty — .startswith() crashed on it.
    if not field_type:
        return False
    return (
        field_type in _CHECK_TYPES
        or field_type.startswith("checkbox")
        or field_type.startswith("multi")
    )


def _containment_allowed(option_text, target):
    """BUGFIX: guards for the fuzzy containment pass in match_option.

    - pure-number prefix ("12" vs "1200000") must not match;
    - tiny yes/no answers must hit Yes/No options exactly ("no" must
      never match "Norway").
    """
    option_digits = re.sub(r"\D", "", option_text)
    target_digits = re.sub(r"\D", "", target)
    if (
        option_digits
        and target_digits
        and option_digits != target_digits
        and (
            option_digits.startswith(target_digits)
            or target_digits.startswith(option_digits)
        )
    ):
        return False
    if (
        option_text in ("yes", "no") or target in ("yes", "no")
    ) and option_text != target:
        return False
    return True


def _as_choice_list(raw):
    """Normalize any raw profile value into a list of wanted items."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [item.strip() for item in raw.split(",") if item.strip()]
    if isinstance(raw, (list, tuple, set)):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [str(raw).strip()]


def is_empty(value):
    return (
        value is None
        or (isinstance(value, str) and not value.strip())
    )


# ==========================================
# 6. OPTION MATCHING HELPERS
# ==========================================

def _option_fields(opt):
    if isinstance(opt, dict):
        return opt
    return {"value": opt, "label": opt}


def match_option(options, value):
    """Fuzzy-match `value` against an options list.

    Accepts dict options ({value, label, text}) or plain strings.
    Returns the matched option dict, or None.
    """
    if not options or value is None:
        return None

    if isinstance(value, bool):
        target = _norm_option_text("yes" if value else "no")
        target_raw = value
    else:
        target = _norm_option_text(value)
        target_raw = value

    opts = [_option_fields(o) for o in options]

    # 1. exact value / label / text
    for opt in opts:
        for k in ("value", "label", "text"):
            if opt.get(k) is None:
                continue
            if str(opt.get(k)).strip() == str(target_raw).strip():
                return opt

    # 2. normalized comparison
    for opt in opts:
        for k in ("value", "label", "text"):
            if opt.get(k) is not None and _norm_option_text(opt.get(k)) == target:
                return opt

    # 3. containment (option text contains the value or vice versa)
    for opt in opts:
        for k in ("value", "label", "text"):
            ov = opt.get(k)
            if ov is None:
                continue
            on = _norm_option_text(ov)
            if not on:
                continue
            if not _containment_allowed(on, target):
                continue
            if on in target or target in on:
                return opt
    return None

# ==========================================
# 7. FIELD VALIDATION & DETECTION
# ==========================================

def is_required(field):
    if not isinstance(field, dict):
        return False
    if bool(field.get("required")):
        return True
    constraints = field.get("constraints")
    if isinstance(constraints, dict):
        if bool(constraints.get("required")) or bool(constraints.get("mandatory")):
            return True
    if field.get("isRequired") is True:          # Ashby style
        return True
    return False


_DECLARATIVE_PATTERNS = [
    r"are you (legally )?authorized",
    r"legally (authorized|allowed) to work",
    r"sponsor(ship)?",
    r"visa",
    r"work permit",
    r"(minimum|acceptable) (salary|compensation|pay)",
    r"salary expectation",
    r"notice period",
    r"willing to (relocate|travel|undergo|submit)",
    r"background check",
    r"drug test",
    r"self[- ]identif",
    r"gender",
    r"race",
    r"ethnic",
    r"veteran",
    r"disability",
    r"sexual orientation",
    r"i (hereby )?(agree|consent|accept|certify|confirm|acknowledge)",
    r"(agree|consent) to (the|our)",
    r"terms and conditions",
    r"privacy (policy|notice)",
    r"over the age",
    r"18 years",
    r"how did you hear",
    r"referral source",
    r"do you (have|own|possess)",
    r"are you (a|an) ",
    r"can you ",
    r"have you (ever|been)",
    r"why do you",
    r"describe ",
    r"tell us ",
]

_DECLARATIVE_RE = re.compile("|".join(_DECLARATIVE_PATTERNS))


def requires_manual_answer(field):
    """True for declarative/eligibility/consent questions."""
    if not isinstance(field, dict):
        return False
    label = _norm(field.get("label"))
    name = _norm(field.get("name"))
    text = f"{label} {name}"
    return bool(_DECLARATIVE_RE.search(text))


# ==========================================
# 8. FIELD ALIASES + GUARDS
# ==========================================

FIELD_ALIASES = {
    "name": ["name", "full_name", "fullname", "candidate_name"],
    "first_name": ["first_name", "firstname", "given_name", "fname"],
    "last_name": ["last_name", "lastname", "family_name", "surname", "lname"],
    "email": ["email", "email_address", "primary_email"],
    "phone": ["phone", "phone_number", "mobile", "mobile_number", "telephone"],
    "phone_country_code": ["phone_country_code", "country_code"],
    "location": ["location", "current_location", "city", "address"],
    "linkedin": ["linkedin", "linkedin_url", "linkedin_profile"],
    "portfolio": ["portfolio", "website", "personal_website", "url"],
    "github": ["github", "github_url", "github_profile"],
    "current_company": ["current_company", "company", "employer"],
    "current_title": ["current_title", "title", "job_title", "designation"],
    "years_of_experience": ["years_of_experience", "total_experience", "experience_years"],
    "salary_expectation": ["salary_expectation", "expected_salary", "salary"],
    "relocate": ["relocate", "willing_to_relocate", "open_to_relocation"],
    "education": ["education", "university", "school", "degree"],
    "cover_letter": ["cover_letter", "coverletter"],
    "notice_period": ["notice_period", "available_from", "availability"],
    "gender": ["gender"],
    "veteran_status": ["veteran_status", "veteran"],
    "disability_status": ["disability_status", "disability"],
    "race_ethnicity": ["race_ethnicity", "race", "ethnicity"],
    "work_authorization": ["work_authorization", "legally_authorized"],
    "sponsorship": ["sponsorship", "require_sponsorship"],
    "preferred_name": ["preferred_name", "nickname"],
    "dob": ["dob", "date_of_birth", "birthday"],
    "nationality": ["nationality", "citizenship"],
}


GENERIC_GUARDS = {
    "name": [
        "company", "manager", "reference", "referrer", "referral", "referred",
        "emergency", "father", "mother", "guardian", "spouse", "relative",
        "friend", "agency", "recruiter", "supervisor", "school", "college",
        "university", "institute", "employee", "contact", "alternate", "job",
        "requisition", "user", "account", "firm", "vendor", "clinic",
        "hospital", "doctor", "physician", "veteran", "previous", "past",
        "maiden",
    ],
    "email": [
        "company", "work", "alternate", "reference", "emergency",
        "school", "college",
    ],
    "phone": [
        "company", "work", "alternate", "reference", "emergency", "fax",
        "school", "college",
    ],
    "location": ["job", "work", "preferred", "office", "relocation"],
    "address": [
        "company", "work", "school", "billing", "previous", "past",
        "employer", "permanent",
    ],
    "skills": [],
}


MANUAL_KEYWORDS = [
    "government employment",
    "government organization",
    "government organisation",
    "government employee",

    "citizenship",
    "citizen",
    "passport",
    "dual citizenship",
    "permanent resident",

    "conflict of interest",
    "family member",
    "personal relationship",

    "non compete",
    "noncompete",
    "nda",

    "work permit",
    "residency permit",
    "residence permit",

    "sponsorship",
    "visa sponsorship",
    "require sponsorship",

    "authorized to work",
    "legally authorized",
    "eligible to work",
    "right to work",
    "visa status",
    "employment eligibility",

    "regulatory authority",
    "criminal conviction",
    "background check",
    "export control",

    # sensitive self-identification — candidate ko khud answer karna chahiye
    "veteran",
    "disability",
    "ethnic",
    "race",
    "gender",
    "religion",
    "pregnan",
    "sexual orientation",
]


def canonical(value):
    """Normalize a label/name/id into a canonical snake_case key."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")

    # synonym collapse
    synonyms = {
        "first_name": "first_name",
        "firstname": "first_name",
        "last_name": "last_name",
        "lastname": "last_name",
        "surname": "last_name",
        "full_name": "name",
        "fullname": "name",
        "candidate_name": "name",
        "your_name": "name",
        "email": "email",
        "email_address": "email",
        "e_mail": "email",
        "phone": "phone",
        "phone_number": "phone",
        "mobile": "phone",
        "mobile_number": "phone",
        "telephone": "phone",
        "contact_number": "phone",
        "phone_country_code": "phone_country_code",
        "country_code": "phone_country_code",
        "country": "country",
        "city": "location",
        "current_city": "location",
        "location": "location",
        "address": "location",
        "linkedin_profile": "linkedin",
        "linkedin_url": "linkedin",
        "linkedin": "linkedin",
        "github_profile": "github",
        "github_url": "github",
        "website": "portfolio",
        "portfolio": "portfolio",
        "personal_website": "portfolio",
        "current_company": "current_company",
        "employer": "current_company",
        "company": "current_company",
        "current_job_title": "current_title",
        "job_title": "current_title",
        "current_title": "current_title",
        "designation": "current_title",
        "expected_salary": "salary_expectation",
        "salary_expectation": "salary_expectation",
        "minimum_salary": "salary_expectation",
        "salary_expectations": "salary_expectation",
        "notice_period": "notice_period",
        "willing_to_relocate": "relocate",
        "relocation": "relocate",
        "years_of_experience": "years_of_experience",
        "total_years_of_experience": "years_of_experience",
    }
    return synonyms.get(s, s)


# FIX-6: declarative-looking labels that are actually backed by real
# profile data may be auto-mapped when the profile provides a value.
# Sensitive declarations (gender, race, veteran, sponsorship, consent...)
# are deliberately NOT in this set.
PROFILE_BACKED_KEYS = {
    "notice_period",
    "salary_expectation",
    "relocate",
    "years_of_experience",
}


# FIX-7: exact canonical keys miss prefixed labels like "Please indicate
# your nationality". Whole-word token-subsequence matching recovers the
# alias key conservatively: multi-token keys are always allowed,
# single-token keys only from a safe set (generic words like "name" or
# "title" would over-match into the GENERIC_GUARDS territory).
_SAFE_SINGLE_TOKEN_ALIASES = {
    "location", "portfolio", "github", "linkedin", "email",
    "phone", "dob", "nationality", "education", "gender",
}


def find_embedded_alias_keys(label, name=None, field_id=None):
    """FIELD_ALIASES keys that appear as whole-word token subsequences
    inside a longer label/name/id."""
    text = _alias_norm(" ".join(
        str(x) for x in (label, name, field_id) if x
    ))
    tokens = text.split()
    if not tokens:
        return []
    out = []
    for key in FIELD_ALIASES:
        ktokens = key.split("_")
        if len(ktokens) >= 2:
            allowed = True
        else:
            allowed = ktokens[0] in _SAFE_SINGLE_TOKEN_ALIASES
        if not allowed:
            continue
        n = len(ktokens)
        for i in range(len(tokens) - n + 1):
            if tokens[i:i + n] == ktokens:
                out.append(key)
                break
    return out

# ==========================================
# 9. PROFILE / RESUME DATA HELPERS
# ==========================================

def clean_value(value):
    """Normalize a raw source value; None when empty."""
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        cleaned = [clean_value(v) for v in value]
        cleaned = [v for v in cleaned if v is not None]
        return cleaned if cleaned else None
    if isinstance(value, dict):
        return value if value else None
    return value


def flatten_data(data):
    """Flatten nested dicts (and lists of dicts) into a single-level map.

    Produces both bare leaf keys ("email") and dotted paths
    ("personal.email"), so get_source_value can match aliases either way.
    """
    flat = {}

    if not isinstance(data, dict):
        return flat

    def _walk(prefix, obj):
        if isinstance(obj, dict):
            for key, val in obj.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                _walk(path, val)
        elif isinstance(obj, list):
            scalars = [
                v for v in obj
                if isinstance(v, (str, int, float, bool))
            ]
            if scalars:
                flat.setdefault(prefix, scalars)
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    _walk(f"{prefix}[{i}]", item)
        else:
            if obj is not None:
                flat.setdefault(prefix, obj)
                # also expose the bare leaf key for alias matching
                bare = prefix.rsplit(".", 1)[-1]
                bare = re.sub(r"\[\d+\]$", "", bare)
                flat.setdefault(bare, obj)

    _walk("", data)
    return flat


def get_source_value(flat, aliases):
    """Return the first non-empty value matching any alias key/path."""
    if not isinstance(flat, dict) or not aliases:
        return None

    for alias in aliases:
        # exact key
        if alias in flat:
            val = clean_value(flat[alias])
            if val is not None:
                return val
        # dotted-path suffix match (e.g. "personal.email" for alias "email")
        for key, val in flat.items():
            if "." in key or "[" in key:
                tail = key.rsplit(".", 1)[-1]
                tail = re.sub(r"\[\d+\]$", "", tail)
                if tail == alias:
                    cleaned = clean_value(val)
                    if cleaned is not None:
                        return cleaned
    return None


# ==========================================
# 10. APPLY BUTTON HANDLING
# ==========================================

# FIX-4: overlay modals (Internshala's subscription_alert, cookie walls,
# job-alert popups) intercept pointer events and make the Apply click
# time out. Best-effort dismissal + retry + DOM-level click fallback.
_MODAL_CLOSE_SELECTORS = [
    "[class*='modal'] [class*='close']",
    "[class*='modal'] button[aria-label='Close']",
    "button[aria-label='Close']",
    "[data-dismiss='modal']",
    "[class*='modal'] .cross",
    "[class*='popup'] [class*='close']",
    "[aria-label='Close dialog']",
]


def dismiss_blocking_popups(page):
    """Try Escape + common close controls. True if anything was closed."""
    dismissed = False

    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
    except Exception:
        pass

    for sel in _MODAL_CLOSE_SELECTORS:
        try:
            loc = page.locator(sel)
            for i in range(min(loc.count(), 3)):
                cand = loc.nth(i)
                if cand.is_visible():
                    try:
                        cand.click(timeout=1500)
                        page.wait_for_timeout(300)
                        dismissed = True
                    except Exception:
                        continue
        except Exception:
            continue

    return dismissed


def click_apply_button(page, apply_actions):

    if not apply_actions:
        return False

    # Find the first enabled Apply action
    apply_button = next(
        (
            action for action in apply_actions
            if action.get("enabled", False)
        ),
        None
    )

    if not apply_button:
        return False

    # 1. Try scraped CSS selector
    selector = apply_button.get("selector")

    if selector:
        locator = page.locator(selector)

    # 2. Fallback: ID
    elif apply_button.get("id"):
        locator = page.locator(
            f"#{apply_button['id']}"
        )

    # 3. Fallback: href
    elif apply_button.get("url"):
        locator = page.locator(
            f'{apply_button.get("tag", "*")}[href]'
        ).filter(
            has_text=apply_button.get("text", "")
        )

    # 4. Fallback: text
    else:
        locator = page.locator(
            apply_button.get("tag", "*")
        ).filter(
            has_text=apply_button.get("text", "")
        )

    # Check locator
    if locator.count() == 0:
        return False

    locator = locator.first

    if not locator.is_visible():
        return False

    if not locator.is_enabled():
        return False

    # FIX-4: dismiss overlay popups first; if the click still fails
    # because something intercepts pointer events, retry once after
    # another dismissal, and finally fall back to a DOM-level click
    # (a synthetic el.click() is not blocked by overlays).
    dismiss_blocking_popups(page)

    try:
        locator.click(timeout=10000)
        return True
    except Exception:
        dismiss_blocking_popups(page)
        try:
            locator.click(timeout=5000)
            return True
        except Exception:
            locator.evaluate("el => el.click()")
            return True


# ==========================================
# 11. VISIBLE BUTTON SELECTION
# ==========================================

def pick_visible_button(page, buttons):
    """P0-3: buttons LIST me se pehla visible+enabled button pick karo.

    Sticky header/footer me 2 next buttons ho sakte hain — hidden wala
    nahi, chalu wala chahiye. Koi visible na mile to None.
    """
    for button in buttons or []:
        if not isinstance(button, dict):
            continue
        selector = button.get("selector")
        if not selector:
            continue
        try:
            locator = page.locator(selector)
            # BUGFIX: only .first was checked — when the first DOM match is
            # hidden but a later match is visible, the button was skipped
            # entirely. Check every match before giving up.
            for i in range(locator.count()):
                candidate = locator.nth(i)
                if candidate.is_visible() and candidate.is_enabled():
                    return button
        except Exception:
            continue
    return None


# ==========================================
# 12. NEXT BUTTON CLICK (NAVIGATION DETECTION)
# ==========================================

def click_next_button(page, button_data,logger):
    if not isinstance(button_data, dict):
        logger.error("Next button data invalid (dict expected, got %s).",
                     type(button_data).__name__)
        return False

    if not button_data:
        logger.warning("Next button not found.")
        return False

    try:
        selector = button_data.get("selector")

        if not selector:
            logger.warning("Button selector missing.")
            return False

        button = page.locator(selector).first

        if not button.is_visible():
            logger.warning("Next button is not visible.")
            return False

        if not button.is_enabled():
            logger.warning("Next button is disabled.")
            return False

        # Capture current page state
        # FIX-9: count only VISIBLE fields — multi-step same-page forms
        # keep every step's fields in the DOM (hidden), so a total DOM
        # count never changes and the transition was never detected.
        old_url = page.url
        old_fields = page.locator(
            "input:visible, select:visible, textarea:visible"
        ).count()

        # Click button
        button.click(timeout=10000)
        logger.info("Next button click attempted.")

        # Wait for possible SPA or normal navigation
        try:
            page.wait_for_function(
                "(oldUrl) => window.location.href !== oldUrl",
                arg=old_url,
                timeout=5000,
            )
        except Exception:
            pass

        # Allow DOM updates
        page.wait_for_timeout(2000)

        # Check current page state
        new_url = page.url
        new_fields = page.locator(
            "input:visible, select:visible, textarea:visible"
        ).count()

        # Check HTML validation (visible fields only — hidden required
        # inputs of inactive form steps must not block the transition)
        invalid_fields = page.locator(
            "input:invalid:visible, select:invalid:visible, "
            "textarea:invalid:visible"
        )
        invalid_count = invalid_fields.count()

        logger.info(
            "URL: %s -> %s | fields: %d -> %d | invalid: %d",
            old_url, new_url, old_fields, new_fields, invalid_count,
        )

        # Navigation detection
        if new_url != old_url or new_fields != old_fields:
            logger.info("Page transition detected.")
            return True

        if invalid_count > 0:
            logger.warning("Form validation failed.")
            for i in range(invalid_count):
                field = invalid_fields.nth(i)
                logger.warning(
                    "  %s -> %s",
                    field.get_attribute("name"),
                    field.evaluate("(el) => el.validationMessage"),
                )
            return False

        logger.warning("No page transition detected.")
        return False

    except Exception as exc:
        logger.error("Next button error: %s", exc)
        return False


def merge(ruled_output, ai_output=None):

    ruled_output = ruled_output or {}
    ai_output = ai_output or {}

    merged_fields = []
    seen_field_keys = set()

    def get_field_key(field):
        return (
            field.get("selector")
            or field.get("id")
            or field.get("name")
            or (field.get("label"), field.get("type"))
        )

    # 1. Merge mapped fields (ruled_output gets priority)
    for field in ruled_output.get("fields", []):
        key = get_field_key(field)
        seen_field_keys.add(key)
        merged_fields.append(field)

    for field in ai_output.get("fields", []):
        key = get_field_key(field)
        if key not in seen_field_keys:
            seen_field_keys.add(key)
            merged_fields.append(field)

    # 2. Merge manual_required_fields without duplicates
    merged_manual_fields = []
    seen_manual_keys = set()

    def get_manual_key(item):
        return (item.get("id"), item.get("label"))

    for item in ruled_output.get("manual_required_fields", []):
        key = get_manual_key(item)
        if key not in seen_manual_keys:
            seen_manual_keys.add(key)
            merged_manual_fields.append(item)

    for item in ai_output.get("manual_required_fields", []):
        key = get_manual_key(item)
        if key not in seen_manual_keys:
            seen_manual_keys.add(key)
            merged_manual_fields.append(item)

    # 3. BUGFIX: carry rule_map's unmatched fields through as
    # remaining_web_data — filler's "unmatched required field" safety net
    # reads this key and it was silently DROPPED here, so the check was
    # dead code. Fields already covered by the AI mapper (mapped fields or
    # manual entries) are excluded, otherwise filler would double-report
    # them as failed.
    unmatched_fields = []

    for field in ((ruled_output.get("remaining_web_data") or {}).get("fields") or []):
        if not isinstance(field, dict):
            continue
        if get_field_key(field) in seen_field_keys:
            continue
        if (field.get("id"), field.get("label")) in seen_manual_keys:
            continue
        unmatched_fields.append(field)

    return {
        "fields": merged_fields,
        "manual_required_fields": merged_manual_fields,
        "remaining_web_data": (
            {"fields": unmatched_fields} if unmatched_fields else None
        ),
    }