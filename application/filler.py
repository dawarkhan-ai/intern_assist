# import application.app_utility as app_ut
# import re
# from pathlib import Path


# def fill(page, mapped_output, resume_path=None, config=None):

#     cfg = {**app_ut.PORTAL_CONFIG, **(config or {})}

#     report = {
#         "success": [],
#         "failed": [],
#         "skipped": [],
#         "manual_required": [],
#         "resume_upload": None,
#     }

#     current_required = False

#     def add_status(status, label, value=None, reason=None, required=None):

#         if required is None:
#             required = current_required

#         report[status].append({
#             "label": label,
#             "value": value,
#             "reason": reason,
#             "required": required,
#         })

#     def field_value(field):
#         value = field.get("value")
#         return value.strip() if isinstance(value, str) else value

#     def get_phone_parts(fields):

#         for item in fields:

#             label = app_ut._norm(item.get("label"))
#             value = field_value(item)

#             if value and "phone" in label and "country code" not in label:

#                 match = re.match(
#                     r"^\s*(\+\d{1,4})[\s().-]+(.*)$",
#                     str(value)
#                 )

#                 if match:
#                     return (
#                         match.group(1),
#                         re.sub(r"\D", "", match.group(2))
#                     )

#         return None, None

#     def verify_input(locator, expected):

#         actual = locator.input_value()

#         expected = str(expected).strip()
#         actual = str(actual).strip()

#         if (locator.get_attribute("type") or "").lower() == "tel":

#             expected = re.sub(r"\D", "", expected)
#             actual = re.sub(r"\D", "", actual)

#         if app_ut._norm(actual) != app_ut._norm(expected):

#             raise RuntimeError(
#                 f"Verification mismatch: expected={expected!r}, actual={actual!r}"
#             )

#     def resolve_option(field, value):
#         return app_ut.match_option(field.get("options"), value)

#     def select_custom(locator, option_label):

#         locator.click()

#         controls = locator.get_attribute("aria-controls")

#         if not controls:
#             raise RuntimeError("Custom dropdown has no aria-controls")

#         popup = page.locator(f'[id="{controls}"]').first

#         if not popup.is_visible():

#             toggle = page.locator(
#                 f'button[aria-controls="{controls}"]'
#             )

#             if toggle.count():
#                 toggle.first.click()

#         popup.wait_for(
#             state="visible",
#             timeout=cfg["dropdown_timeout_ms"]
#         )

#         desired = app_ut._norm(option_label)

#         candidates = popup.locator(
#             '[role="option"], [role="gridcell"], [role="row"], li, button'
#         )

#         chosen = None

#         for i in range(candidates.count()):

#             candidate = candidates.nth(i)

#             if (
#                 candidate.is_visible()
#                 and app_ut._norm(candidate.inner_text()) == desired
#             ):
#                 chosen = candidate
#                 break

#         if chosen is None:

#             exact = popup.get_by_text(
#                 str(option_label).strip(),
#                 exact=True
#             )

#             for i in range(exact.count()):

#                 if exact.nth(i).is_visible():
#                     chosen = exact.nth(i)
#                     break

#         if chosen is None:
#             raise RuntimeError(
#                 f"Dropdown option not found: {option_label}"
#             )

#         chosen.click()

#         page.wait_for_timeout(250)

#         actual = (
#             locator.get_attribute("aria-valuetext")
#             or locator.get_attribute("value")
#             or ""
#         )

#         if app_ut._norm(actual) != desired:

#             raise RuntimeError(
#                 f"Dropdown selection not verified: {actual!r}"
#             )

#     # ==========================================
#     # RESUME UPLOAD
#     # ==========================================

#     def upload_resume_file(file_path):

#         result = {
#             "status": "not_attempted",
#             "success": False,
#             "filename": None,
#             "size_kb": None,
#             "file_selected": False,
#             "upload_verified": False,
#             "reason": None,
#         }

#         try:

#             existing = page.locator(cfg["uploaded_file_name"])

#             existing_names = [
#                 name.strip()
#                 for name in existing.all_text_contents()
#                 if name.strip()
#             ]

#             download = page.locator(cfg["download_file_link"])

#             if existing_names and download.count() > 0:

#                 result.update({
#                     "status": "already_uploaded",
#                     "success": True,
#                     "filename": existing_names[0],
#                     "file_selected": True,
#                     "upload_verified": True,
#                     "reason": "Existing uploaded resume detected.",
#                 })

#                 return result

#             file_input = page.locator(cfg["resume_file_input"])

#             if file_input.count() == 0:

#                 result.update({
#                     "status": "not_present",
#                     "reason": "Resume upload widget not present.",
#                 })

#                 return result

#             if file_input.count() != 1:

#                 raise RuntimeError(
#                     f"Expected one resume input; found {file_input.count()}"
#                 )

#             path = Path(file_path).expanduser()

#             if not path.exists() or not path.is_file():

#                 raise FileNotFoundError(
#                     f"Resume file not found: {path}"
#                 )

#             if path.suffix.lower() not in tuple(
#                 cfg["resume_allowed_extensions"]
#             ):

#                 raise ValueError(
#                     f"Unsupported resume format: {path.suffix}"
#                 )

#             size_bytes = path.stat().st_size

#             if size_bytes > cfg["resume_max_mb"] * 1024 * 1024:

#                 raise ValueError(
#                     f"Resume exceeds {cfg['resume_max_mb']} MB limit."
#                 )

#             result["filename"] = path.name
#             result["size_kb"] = round(size_bytes / 1024, 2)

#             file_input.set_input_files(str(path))

#             selected_name = file_input.evaluate(
#                 "el => el.files?.length ? el.files[0].name : null"
#             )

#             if selected_name != path.name:

#                 raise RuntimeError(
#                     "Browser did not retain selected resume."
#                 )

#             result.update({
#                 "file_selected": True,
#                 "status": "selected_unverified",
#             })

#             page.wait_for_function(
#                 """(sel) => {
#                     const name = document.querySelector(sel.nameSel);
#                     const link = document.querySelector(sel.linkSel);

#                     return name?.textContent.trim() && link?.getAttribute('href');
#                 }""",
#                 arg={
#                     "nameSel": cfg["uploaded_file_name"],
#                     "linkSel": cfg["download_file_link"],
#                 },
#                 timeout=cfg["upload_verify_timeout_ms"],
#             )

#             uploaded_name = page.locator(
#                 cfg["uploaded_file_name"]
#             ).first.inner_text().strip()

#             if (
#                 app_ut._norm(uploaded_name) != app_ut._norm(path.name)
#                 and path.name not in uploaded_name
#             ):

#                 raise RuntimeError(
#                     f"Uploaded filename mismatch: {uploaded_name}"
#                 )

#             result.update({
#                 "status": "uploaded",
#                 "success": True,
#                 "upload_verified": True,
#                 "filename": uploaded_name,
#                 "reason": "Website upload verified.",
#             })

#         except Exception as exc:

#             result["status"] = (
#                 "selected_unverified"
#                 if result["file_selected"]
#                 else "failed"
#             )

#             result["reason"] = str(exc)

#         return result

#     # ==========================================
#     # GET RULE MAP OUTPUT
#     # ==========================================

#     if not isinstance(mapped_output, dict):
#         raise TypeError("ruled_output must be a dictionary")

#     fields = mapped_output.get("fields", [])

#     manual_fields = mapped_output.get(
#         "manual_required_fields", []
#     )

#     remaining_fields = (
#         mapped_output.get("remaining_web_data") or {}
#     ).get("fields", [])

#     # ==========================================
#     # INITIALIZE MANUAL REQUIRED FIELDS
#     # ==========================================

#     mapped_ids = {
#         str(field.get("id"))
#         for field in fields
#         if field.get("id") is not None
#     }

#     for field in manual_fields:

#         # Already handled through mapped fields
#         if (
#             field.get("id") is not None
#             and str(field.get("id")) in mapped_ids
#         ):
#             continue

#         add_status(
#             "manual_required",
#             field.get("label") or "Unknown field",
#             None,
#             field.get("reason") or "Candidate input required.",
#             required=field.get("required", False),
#         )

#     # ==========================================
#     # CHECK UNMATCHED REQUIRED FIELDS
#     # ==========================================

#     manual_ids = {
#         str(field.get("id"))
#         for field in manual_fields
#         if field.get("id") is not None
#     }

#     for field in remaining_fields:

#         field_id = field.get("id")

#         # Already included in manual fields
#         if (
#             field_id is not None
#             and str(field_id) in manual_ids
#         ):
#             continue

#         required = app_ut.is_required(field)

#         if required:

#             add_status(
#                 "failed",
#                 field.get("label") or "Unknown field",
#                 None,
#                 "Required field has no mapped value.",
#                 required=True,
#             )

#     # ==========================================
#     # RESUME UPLOAD
#     # ==========================================

#     if resume_path:

#         report["resume_upload"] = upload_resume_file(resume_path)

#         if report["resume_upload"]["status"] == "failed":

#             add_status(
#                 "failed",
#                 "Resume upload",
#                 resume_path,
#                 report["resume_upload"]["reason"],
#                 required=False,
#             )

#     # ==========================================
#     # PHONE DETAILS
#     # ==========================================

#     country_code, phone_number = get_phone_parts(fields)

#     has_country_field = any(
#         "country code" in app_ut._norm(field.get("label"))
#         for field in fields
#     )

#     # ==========================================
#     # FILL FIELDS
#     # ==========================================

#     for index, field in enumerate(fields, start=1):

#         label = field.get("label") or f"Field {index}"
#         label_n = app_ut._norm(label)

#         selector = field.get("selector")
#         value = field_value(field)

#         field_type = app_ut._norm(field.get("type"))

#         required = field.get(
#             "required",
#             app_ut.is_required(field)
#         )

#         current_required = required

#         manual_required = field.get("manual_required", False)

#         if manual_required and value is None:

#             add_status(
#                 "manual_required",
#                 label,
#                 value,
#                 "Candidate input required."
#             )

#             continue

#         if value is None and "country code" in label_n and country_code:

#             value = country_code

#         if value is None or (
#             isinstance(value, str) and not value.strip()
#         ):

#             add_status(
#                 "manual_required" if required else "skipped",
#                 label,
#                 value,
#                 "No reliable matched value; not guessed."
#             )

#             continue

#         # ======================================
#         # POSTAL CODE VALIDATION
#         # ======================================

#         if any(
#             term in label_n
#             for term in (
#                 "postal code", "pin code", "zip code",
#                 "pincode", "zipcode"
#             )
#         ):

#             compact = re.sub(r"[\s\-]", "", str(value))
#             digits = re.sub(r"\D", "", compact)

#             if (
#                 not re.fullmatch(r"\d{4,10}", digits)
#                 or compact != digits
#             ):

#                 add_status(
#                     "manual_required" if required else "skipped",
#                     label,
#                     value,
#                     "Invalid postal code."
#                 )

#                 continue

#         # ======================================
#         # DATE VALIDATION
#         # ======================================

#         if field_type == "date" and not re.fullmatch(
#             r"\d{4}-\d{2}-\d{2}",
#             str(value).strip()
#         ):

#             add_status(
#                 "manual_required" if required else "skipped",
#                 label,
#                 value,
#                 "Date must be in yyyy-mm-dd format."
#             )

#             continue

#         # ======================================
#         # ACTUAL FILLING
#         # ======================================

#         try:

#             # ----------------------------------
#             # RADIO
#             # ----------------------------------

#             if field_type in ("radio", "radiogroup"):

#                 option = resolve_option(field, value)

#                 if not option or not option.get("selector"):

#                     raise RuntimeError(
#                         "Matching radio option not found."
#                     )

#                 locator = page.locator(option["selector"])

#                 locator.check()

#                 if not locator.is_checked():

#                     raise RuntimeError(
#                         "Radio selection verification failed."
#                     )

#             # ----------------------------------
#             # CHECKBOX
#             # ----------------------------------

#             elif field_type in ("checkbox", "checkboxes"):

#                 options = field.get("options") or []

#                 if options:

#                     selected = (
#                         value if isinstance(value, list) else [value]
#                     )

#                     selected_n = {
#                         app_ut._norm(x) for x in selected
#                     }

#                     for option in options:

#                         opt_selector = option.get("selector")

#                         if not opt_selector:
#                             continue

#                         should_check = any(
#                             app_ut._norm(option.get(k)) in selected_n
#                             for k in ("value", "label", "text")
#                             if option.get(k) is not None
#                         )

#                         if should_check:

#                             checkbox = page.locator(opt_selector)

#                             if not checkbox.is_checked():
#                                 checkbox.check()

#                             if not checkbox.is_checked():

#                                 raise RuntimeError(
#                                     f"Checkbox verification failed: {option.get('label')}"
#                                 )

#                 else:

#                     if not selector:

#                         raise RuntimeError(
#                             "Checkbox selector missing."
#                         )

#                     checkbox = page.locator(selector)

#                     if bool(value):

#                         if not checkbox.is_checked():
#                             checkbox.check()

#                         if not checkbox.is_checked():

#                             raise RuntimeError(
#                                 "Checkbox verification failed."
#                             )

#                     elif required:

#                         raise RuntimeError(
#                             "Required checkbox not selected."
#                         )

#             # ----------------------------------
#             # SELECT / COMBOBOX
#             # ----------------------------------

#             elif field_type in ("select", "combobox"):

#                 if not selector:

#                     raise RuntimeError(
#                         "Dropdown selector missing."
#                     )

#                 locator = page.locator(selector)

#                 if locator.count() != 1:

#                     raise RuntimeError(
#                         f"Selector matched {locator.count()} elements."
#                     )

#                 option = resolve_option(field, value)

#                 if locator.is_disabled():

#                     existing = locator.input_value()

#                     option_value = (
#                         str(option.get("value"))
#                         if option else None
#                     )

#                     if (
#                         option is not None
#                         and existing is not None
#                         and app_ut._norm(option_value or "")
#                         == app_ut._norm(existing)
#                     ):

#                         add_status(
#                             "success",
#                             label,
#                             existing,
#                             "Disabled dropdown already correctly prefilled."
#                         )

#                         continue

#                     raise RuntimeError(
#                         "Dropdown is disabled."
#                     )

#                 if option is None:

#                     raise RuntimeError(
#                         f"Exact dropdown option not found: {value}"
#                     )

#                 if (
#                     field.get("is_custom_select")
#                     or field_type == "combobox"
#                 ):

#                     target = locator

#                     widget_selector = field.get("widget_selector")

#                     if widget_selector:

#                         widget = page.locator(widget_selector)

#                         if widget.count() >= 1:
#                             target = widget.first

#                     option_label = (
#                         option.get("text")
#                         or option.get("label")
#                         or option.get("value")
#                     )

#                     select_custom(
#                         target,
#                         str(option_label)
#                     )

#                 else:

#                     option_value = option.get("value")

#                     if option_value is None:

#                         raise RuntimeError(
#                             "Dropdown option has no value."
#                         )

#                     locator.select_option(
#                         value=str(option_value)
#                     )

#                     verify_input(locator, option_value)

#             # ----------------------------------
#             # TEXT / INPUT
#             # ----------------------------------

#             elif field_type in (
#                 "input", "text", "email", "tel", "number",
#                 "url", "date", "textarea",
#             ):

#                 if not selector:

#                     raise RuntimeError(
#                         "Input selector missing."
#                     )

#                 locator = page.locator(selector)

#                 if locator.count() != 1:

#                     raise RuntimeError(
#                         f"Selector matched {locator.count()} elements."
#                     )

#                 if locator.is_disabled():

#                     raise RuntimeError(
#                         "Field is disabled."
#                     )

#                 final_value = value

#                 if (
#                     "phone number" in label_n
#                     and has_country_field
#                     and country_code
#                     and phone_number
#                 ):

#                     final_value = phone_number

#                 if locator.get_attribute("readonly") is not None:

#                     existing = (
#                         locator.input_value() or ""
#                     ).strip()

#                     if (
#                         existing
#                         and app_ut._norm(existing)
#                         == app_ut._norm(str(final_value))
#                     ):

#                         add_status(
#                             "success",
#                             label,
#                             existing,
#                             "Readonly field already correctly prefilled."
#                         )

#                         continue

#                     if "email" in label_n:

#                         edit_button = page.locator(
#                             cfg["email_edit_button"]
#                         )

#                         if edit_button.count() != 1:

#                             raise RuntimeError(
#                                 "Email edit button not found."
#                             )

#                         edit_button.click()

#                         page.wait_for_function(
#                             "el => el && !el.readOnly",
#                             arg=locator.element_handle(),
#                             timeout=cfg["dropdown_timeout_ms"],
#                         )

#                     else:

#                         raise RuntimeError(
#                             "Readonly field requires manual review."
#                         )

#                 locator.fill(str(final_value))

#                 verify_input(locator, final_value)

#             else:

#                 raise RuntimeError(
#                     f"Unsupported field type: {field_type or 'unknown'}"
#                 )

#             add_status(
#                 "success",
#                 label,
#                 value,
#                 "Filled and verified."
#             )

#         except Exception as exc:

#             add_status(
#                 "failed",
#                 label,
#                 value,
#                 str(exc)
#             )

#     # ==========================================
#     # FINAL MANDATORY STATUS
#     # ==========================================

#     required_failed = any(
#         item["required"]
#         for item in report["failed"]
#     )

#     required_manual = any(
#         item["required"]
#         for item in report["manual_required"]
#     )

#     if required_failed:

#         mandatory_status = 0

#     elif required_manual:

#         mandatory_status = 2

#     else:

#         mandatory_status = 1

#     # ==========================================
#     # FINAL REPORT
#     # ==========================================

#     print("\n========== FILL REPORT ==========")

#     for status in (
#         "success",
#         "failed",
#         "skipped",
#         "manual_required"
#     ):

#         items = report[status]

#         print(f"\n{status.upper()} ({len(items)})")

#         for item in items:

#             print(
#                 f"  - {item['label']}: {item['value']}"
#             )

#             if item["reason"]:

#                 print(
#                     f"    Reason: {item['reason']}"
#                 )

#     if report["resume_upload"]:

#         print(
#             f"\nRESUME UPLOAD: {report['resume_upload']}"
#         )


#     return mandatory_status

    



import application.app_utility as app_ut
import re
from pathlib import Path


def fill(page, mapped_output, resume_path=None, config=None):

    cfg = {**app_ut.PORTAL_CONFIG, **(config or {})}

    report = {
        "success": [],
        "failed": [],
        "skipped": [],
        "manual_required": [],
        "resume_upload": None,
    }

    current_required = False

    def add_status(status, label, value=None, reason=None, required=None):

        if required is None:
            required = current_required

        report[status].append({
            "label": label,
            "value": value,
            "reason": reason,
            "required": required,
        })

    def field_value(field):
        value = field.get("value")
        return value.strip() if isinstance(value, str) else value

    def get_phone_parts(fields):

        for item in fields:

            label = app_ut._norm(item.get("label"))
            value = field_value(item)

            if value and "phone" in label and "country code" not in label:

                match = re.match(
                    r"^\s*(\+\d{1,4})[\s().-]+(.*)$",
                    str(value)
                )

                if match:
                    return (
                        match.group(1),
                        re.sub(r"\D", "", match.group(2))
                    )

        return None, None

    def verify_input(locator, expected):

        actual = locator.input_value()

        expected = str(expected).strip()
        actual = str(actual).strip()

        if (locator.get_attribute("type") or "").lower() == "tel":

            expected = re.sub(r"\D", "", expected)
            actual = re.sub(r"\D", "", actual)

        if app_ut._norm(actual) != app_ut._norm(expected):

            raise RuntimeError(
                f"Verification mismatch: expected={expected!r}, actual={actual!r}"
            )

    def set_choice(locator):
        """BUGFIX-robust radio/checkbox selection.

        - native input: .check(); visually hidden inputs (opacity-0 inside
          a custom wrapper — the scraper keeps those via the wrapper) fall
          back to a DOM-level click, because .check() requires visibility.
        - custom div[role=radio]/div[role=checkbox]: .check() throws
          ("not an input"), .click() is the correct toggle.
        """

        tag = locator.evaluate(
            "el => el.tagName.toLowerCase()"
        )

        if tag == "input":

            try:

                locator.check(timeout=3000)

            except Exception:

                if not locator.is_checked():
                    locator.evaluate("el => el.click()")

        else:

            locator.click(timeout=3000)

    def clear_choice(locator):
        """Counterpart of set_choice for UNchecking an option."""

        tag = locator.evaluate(
            "el => el.tagName.toLowerCase()"
        )

        if tag == "input":

            try:

                locator.uncheck(timeout=3000)

            except Exception:

                if locator.is_checked():
                    locator.evaluate("el => el.click()")

        else:

            locator.click(timeout=3000)

    def is_selected(locator):
        """Verification that works for inputs AND aria-based widgets."""

        try:

            return locator.is_checked()

        except Exception:

            return locator.get_attribute("aria-checked") == "true"

    def resolve_option(field, value):
        return app_ut.match_option(field.get("options"), value)

    def select_custom(locator, option_label):

        locator.click()

        controls = locator.get_attribute("aria-controls")

        if controls:

            popup = page.locator(f'[id="{controls}"]').first

        else:
            # BUGFIX: Select2-style widgets expose no aria-controls; their
            # open dropdown lives in a body-level .select2-dropdown node.
            # Without this fallback every Select2 select failed filling.
            popup = page.locator(
                ".select2-dropdown--above, "
                ".select2-dropdown--below, "
                ".select2-dropdown"
            ).first

            if popup.count() == 0 or not popup.is_visible():
                raise RuntimeError("Custom dropdown has no aria-controls")

        if not popup.is_visible():

            toggle = page.locator(
                f'button[aria-controls="{controls}"]'
            )

            if toggle.count():
                toggle.first.click()

        popup.wait_for(
            state="visible",
            timeout=cfg["dropdown_timeout_ms"]
        )

        desired = app_ut._norm(option_label)

        candidates = popup.locator(
            '[role="option"], [role="gridcell"], [role="row"], li, button'
        )

        chosen = None

        for i in range(candidates.count()):

            candidate = candidates.nth(i)

            if (
                candidate.is_visible()
                and app_ut._norm(candidate.inner_text()) == desired
            ):
                chosen = candidate
                break

        if chosen is None:

            exact = popup.get_by_text(
                str(option_label).strip(),
                exact=True
            )

            for i in range(exact.count()):

                if exact.nth(i).is_visible():
                    chosen = exact.nth(i)
                    break

        if chosen is None:
            raise RuntimeError(
                f"Dropdown option not found: {option_label}"
            )

        chosen.click()

        page.wait_for_timeout(250)

        actual = (
            locator.get_attribute("aria-valuetext")
            or locator.get_attribute("value")
            or ""
        )

        if not app_ut._norm(actual):
            # BUGFIX: Select2 renders the chosen text in a child node — the
            # widget itself has no value/aria-valuetext, so verification
            # always failed even though the selection succeeded.
            rendered = locator.locator(
                ".select2-selection__rendered"
            )

            if rendered.count():
                actual = rendered.first.inner_text() or ""

        if app_ut._norm(actual) != desired:

            raise RuntimeError(
                f"Dropdown selection not verified: {actual!r}"
            )

    # ==========================================
    # RESUME UPLOAD
    # ==========================================

    def upload_resume_file(file_path):

        result = {
            "status": "not_attempted",
            "success": False,
            "filename": None,
            "size_kb": None,
            "file_selected": False,
            "upload_verified": False,
            "reason": None,
        }

        try:

            existing = page.locator(cfg["uploaded_file_name"])

            existing_names = [
                name.strip()
                for name in existing.all_text_contents()
                if name.strip()
            ]

            download = page.locator(cfg["download_file_link"])

            if existing_names and download.count() > 0:

                result.update({
                    "status": "already_uploaded",
                    "success": True,
                    "filename": existing_names[0],
                    "file_selected": True,
                    "upload_verified": True,
                    "reason": "Existing uploaded resume detected.",
                })

                return result

            file_input = page.locator(cfg["resume_file_input"])

            if file_input.count() == 0:

                result.update({
                    "status": "not_present",
                    "reason": "Resume upload widget not present.",
                })

                return result

            if file_input.count() != 1:

                raise RuntimeError(
                    f"Expected one resume input; found {file_input.count()}"
                )

            path = Path(file_path).expanduser()

            if not path.exists() or not path.is_file():

                raise FileNotFoundError(
                    f"Resume file not found: {path}"
                )

            if path.suffix.lower() not in tuple(
                cfg["resume_allowed_extensions"]
            ):

                raise ValueError(
                    f"Unsupported resume format: {path.suffix}"
                )

            size_bytes = path.stat().st_size

            if size_bytes > cfg["resume_max_mb"] * 1024 * 1024:

                raise ValueError(
                    f"Resume exceeds {cfg['resume_max_mb']} MB limit."
                )

            result["filename"] = path.name
            result["size_kb"] = round(size_bytes / 1024, 2)

            file_input.set_input_files(str(path))

            selected_name = file_input.evaluate(
                "el => el.files?.length ? el.files[0].name : null"
            )

            if selected_name != path.name:

                raise RuntimeError(
                    "Browser did not retain selected resume."
                )

            result.update({
                "file_selected": True,
                "status": "selected_unverified",
            })

            page.wait_for_function(
                """(sel) => {
                    const name = document.querySelector(sel.nameSel);
                    const link = document.querySelector(sel.linkSel);

                    return name?.textContent.trim() && link?.getAttribute('href');
                }""",
                arg={
                    "nameSel": cfg["uploaded_file_name"],
                    "linkSel": cfg["download_file_link"],
                },
                timeout=cfg["upload_verify_timeout_ms"],
            )

            uploaded_name = page.locator(
                cfg["uploaded_file_name"]
            ).first.inner_text().strip()

            if (
                app_ut._norm(uploaded_name) != app_ut._norm(path.name)
                and path.name not in uploaded_name
            ):

                raise RuntimeError(
                    f"Uploaded filename mismatch: {uploaded_name}"
                )

            result.update({
                "status": "uploaded",
                "success": True,
                "upload_verified": True,
                "filename": uploaded_name,
                "reason": "Website upload verified.",
            })

        except Exception as exc:

            result["status"] = (
                "selected_unverified"
                if result["file_selected"]
                else "failed"
            )

            result["reason"] = str(exc)

        return result

    # ==========================================
    # GET RULE MAP OUTPUT
    # ==========================================

    if not isinstance(mapped_output, dict):
        raise TypeError("ruled_output must be a dictionary")

    fields = mapped_output.get("fields", [])

    manual_fields = mapped_output.get(
        "manual_required_fields", []
    )

    remaining_fields = (
        mapped_output.get("remaining_web_data") or {}
    ).get("fields", [])

    # ==========================================
    # INITIALIZE MANUAL REQUIRED FIELDS
    # ==========================================

    mapped_ids = {
        str(field.get("id"))
        for field in fields
        if field.get("id") is not None
    }

    for field in manual_fields:

        # Already handled through mapped fields
        if (
            field.get("id") is not None
            and str(field.get("id")) in mapped_ids
        ):
            continue

        add_status(
            "manual_required",
            field.get("label") or "Unknown field",
            None,
            field.get("reason") or "Candidate input required.",
            required=field.get("required", False),
        )

    # ==========================================
    # CHECK UNMATCHED REQUIRED FIELDS
    # ==========================================

    manual_ids = {
        str(field.get("id"))
        for field in manual_fields
        if field.get("id") is not None
    }

    for field in remaining_fields:

        field_id = field.get("id")

        # Already included in manual fields
        if (
            field_id is not None
            and str(field_id) in manual_ids
        ):
            continue

        required = app_ut.is_required(field)

        if required:

            add_status(
                "failed",
                field.get("label") or "Unknown field",
                None,
                "Required field has no mapped value.",
                required=True,
            )

    # ==========================================
    # RESUME UPLOAD
    # ==========================================

    if resume_path:

        report["resume_upload"] = upload_resume_file(resume_path)

        if report["resume_upload"]["status"] == "failed":

            add_status(
                "failed",
                "Resume upload",
                resume_path,
                report["resume_upload"]["reason"],
                required=False,
            )

    # ==========================================
    # PHONE DETAILS
    # ==========================================

    country_code, phone_number = get_phone_parts(fields)

    has_country_field = any(
        "country code" in app_ut._norm(field.get("label"))
        for field in fields
    )

    # ==========================================
    # FILL FIELDS
    # ==========================================

    for index, field in enumerate(fields, start=1):

        label = field.get("label") or f"Field {index}"
        label_n = app_ut._norm(label)

        selector = field.get("selector")
        value = field_value(field)

        field_type = app_ut._norm(field.get("type"))

        required = field.get(
            "required",
            app_ut.is_required(field)
        )

        current_required = required

        manual_required = field.get("manual_required", False)

        if manual_required and value is None:

            add_status(
                "manual_required",
                label,
                value,
                "Candidate input required."
            )

            continue

        if value is None and "country code" in label_n and country_code:

            value = country_code

        if value is None or (
            isinstance(value, str) and not value.strip()
        ):

            add_status(
                "manual_required" if required else "skipped",
                label,
                value,
                "No reliable matched value; not guessed."
            )

            continue

        # ======================================
        # POSTAL CODE VALIDATION
        # ======================================

        if any(
            term in label_n
            for term in (
                "postal code", "pin code", "zip code",
                "pincode", "zipcode"
            )
        ):

            compact = re.sub(r"[\s\-]", "", str(value))
            digits = re.sub(r"\D", "", compact)

            if (
                not re.fullmatch(r"\d{4,10}", digits)
                or compact != digits
            ):

                add_status(
                    "manual_required" if required else "skipped",
                    label,
                    value,
                    "Invalid postal code."
                )

                continue

        # ======================================
        # DATE VALIDATION
        # ======================================

        if field_type == "date" and not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}",
            str(value).strip()
        ):

            add_status(
                "manual_required" if required else "skipped",
                label,
                value,
                "Date must be in yyyy-mm-dd format."
            )

            continue

        # ======================================
        # ACTUAL FILLING
        # ======================================

        try:

            # ----------------------------------
            # RADIO
            # ----------------------------------

            if field_type in ("radio", "radiogroup"):

                option = resolve_option(field, value)

                if not option or not option.get("selector"):

                    raise RuntimeError(
                        "Matching radio option not found."
                    )

                locator = page.locator(option["selector"])

                set_choice(locator)

                if not is_selected(locator):

                    raise RuntimeError(
                        "Radio selection verification failed."
                    )

            # ----------------------------------
            # CHECKBOX
            # ----------------------------------

            elif field_type in ("checkbox", "checkboxes"):

                options = field.get("options") or []

                if options:

                    selected = (
                        value if isinstance(value, list) else [value]
                    )

                    selected_n = {
                        app_ut._norm(x) for x in selected
                    }

                    for option in options:

                        opt_selector = option.get("selector")

                        if not opt_selector:
                            continue

                        should_check = any(
                            app_ut._norm(option.get(k)) in selected_n
                            for k in ("value", "label", "text")
                            if option.get(k) is not None
                        )

                        checkbox = page.locator(opt_selector)

                        if should_check:

                            set_choice(checkbox)

                            if not is_selected(checkbox):

                                raise RuntimeError(
                                    f"Checkbox verification failed: {option.get('label')}"
                                )

                        elif is_selected(checkbox):
                            # BUGFIX: a pre-checked option the candidate did
                            # NOT select was silently submitted (stale
                            # portal defaults). Uncheck it.
                            clear_choice(checkbox)

                else:

                    if not selector:

                        raise RuntimeError(
                            "Checkbox selector missing."
                        )

                    checkbox = page.locator(selector)

                    if bool(value):

                        set_choice(checkbox)

                        if not is_selected(checkbox):

                            raise RuntimeError(
                                "Checkbox verification failed."
                            )

                    elif required:

                        raise RuntimeError(
                            "Required checkbox not selected."
                        )

            # ----------------------------------
            # SELECT / COMBOBOX
            # ----------------------------------

            elif field_type in (
                "select", "combobox", "dropdown", "selectbox",
            ):

                if not selector:

                    raise RuntimeError(
                        "Dropdown selector missing."
                    )

                locator = page.locator(selector)

                if locator.count() != 1:

                    raise RuntimeError(
                        f"Selector matched {locator.count()} elements."
                    )

                option = resolve_option(field, value)

                if locator.is_disabled():

                    existing = locator.input_value()

                    option_value = (
                        str(option.get("value"))
                        if option else None
                    )

                    if (
                        option is not None
                        and existing is not None
                        and app_ut._norm(option_value or "")
                        == app_ut._norm(existing)
                    ):

                        add_status(
                            "success",
                            label,
                            existing,
                            "Disabled dropdown already correctly prefilled."
                        )

                        continue

                    raise RuntimeError(
                        "Dropdown is disabled."
                    )

                if option is None:

                    raise RuntimeError(
                        f"Exact dropdown option not found: {value}"
                    )

                if (
                    field.get("is_custom_select")
                    or field_type == "combobox"
                ):

                    target = locator

                    widget_selector = field.get("widget_selector")

                    if widget_selector:

                        widget = page.locator(widget_selector)

                        if widget.count() >= 1:
                            target = widget.first

                    option_label = (
                        option.get("text")
                        or option.get("label")
                        or option.get("value")
                    )

                    select_custom(
                        target,
                        str(option_label)
                    )

                else:

                    option_value = option.get("value")

                    if option_value is None:

                        raise RuntimeError(
                            "Dropdown option has no value."
                        )

                    locator.select_option(
                        value=str(option_value)
                    )

                    verify_input(locator, option_value)

            # ----------------------------------
            # CONTENTEDITABLE (rich text, e.g. cover letter)
            # BUGFIX: contenteditable fields were scraped but fill() had no
            # branch for them — they always failed as "Unsupported field
            # type" and required questions dragged the flow into manual.
            # ----------------------------------

            elif field.get("contenteditable") or field_type in (
                "contenteditable",
            ):

                if not selector:

                    raise RuntimeError(
                        "Contenteditable selector missing."
                    )

                locator = page.locator(selector)

                if locator.count() != 1:

                    raise RuntimeError(
                        f"Selector matched {locator.count()} elements."
                    )

                if locator.is_disabled():

                    raise RuntimeError(
                        "Field is disabled."
                    )

                locator.click()

                locator.fill(str(value))

                actual = locator.inner_text() or ""

                if app_ut._norm(actual) != app_ut._norm(str(value)):

                    raise RuntimeError(
                        f"Verification mismatch: expected={value!r}, actual={actual!r}"
                    )

            # ----------------------------------
            # TEXT / INPUT
            # ----------------------------------

            elif field_type in (
                "input", "text", "email", "tel", "number",
                "url", "date", "textarea",
            ):

                if not selector:

                    raise RuntimeError(
                        "Input selector missing."
                    )

                locator = page.locator(selector)

                if locator.count() != 1:

                    raise RuntimeError(
                        f"Selector matched {locator.count()} elements."
                    )

                if locator.is_disabled():

                    raise RuntimeError(
                        "Field is disabled."
                    )

                final_value = value

                if (
                    "phone" in label_n
                    and "country code" not in label_n
                    and has_country_field
                    and country_code
                    and phone_number
                ):

                    final_value = phone_number

                if locator.get_attribute("readonly") is not None:

                    existing = (
                        locator.input_value() or ""
                    ).strip()

                    if (
                        existing
                        and app_ut._norm(existing)
                        == app_ut._norm(str(final_value))
                    ):

                        add_status(
                            "success",
                            label,
                            existing,
                            "Readonly field already correctly prefilled."
                        )

                        continue

                    if "email" in label_n:

                        edit_button = page.locator(
                            cfg["email_edit_button"]
                        )

                        if edit_button.count() != 1:

                            raise RuntimeError(
                                "Email edit button not found."
                            )

                        edit_button.click()

                        page.wait_for_function(
                            "el => el && !el.readOnly",
                            arg=locator.element_handle(),
                            timeout=cfg["dropdown_timeout_ms"],
                        )

                    else:

                        raise RuntimeError(
                            "Readonly field requires manual review."
                        )

                locator.fill(str(final_value))

                verify_input(locator, final_value)

            else:

                raise RuntimeError(
                    f"Unsupported field type: {field_type or 'unknown'}"
                )

            add_status(
                "success",
                label,
                value,
                "Filled and verified."
            )

        except Exception as exc:

            add_status(
                "failed",
                label,
                value,
                str(exc)
            )

    # ==========================================
    # FINAL MANDATORY STATUS
    # ==========================================

    required_failed = any(
        item["required"]
        for item in report["failed"]
    )

    required_manual = any(
        item["required"]
        for item in report["manual_required"]
    )

    if required_failed:

        mandatory_status = 0

    elif required_manual:

        mandatory_status = 2

    else:

        mandatory_status = 1

    # ==========================================
    # FINAL REPORT
    # ==========================================

    print("\n========== FILL REPORT ==========")

    for status in (
        "success",
        "failed",
        "skipped",
        "manual_required"
    ):

        items = report[status]

        print(f"\n{status.upper()} ({len(items)})")

        for item in items:

            print(
                f"  - {item['label']}: {item['value']}"
            )

            if item["reason"]:

                print(
                    f"    Reason: {item['reason']}"
                )

    if report["resume_upload"]:

        print(
            f"\nRESUME UPLOAD: {report['resume_upload']}"
        )


    return mandatory_status
