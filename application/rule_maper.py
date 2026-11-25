# # ==========================================
# # 4. RULE MAP (field <-> profile/resume matching) — FIXED
# # ==========================================

# import json
# import application.app_utility as app_ut
# import re


# def rule_map(fields, resume, candidate_profile):

#     if isinstance(fields, str):
#         fields = json.loads(fields)

#     if isinstance(resume, str):
#         resume = json.loads(resume)

#     if isinstance(candidate_profile, str):
#         candidate_profile = json.loads(candidate_profile)

#     if not isinstance(fields, list):
#         raise TypeError("fields must be a list")

#     candidate_data = app_ut.flatten_data(candidate_profile)
#     resume_data_flat = app_ut.flatten_data(resume)

#     # ==========================================
#     # SYNTHESIZE FULL NAME
#     # ==========================================

#     first_name = (
#         app_ut.get_source_value(
#             candidate_data, app_ut.FIELD_ALIASES["first_name"]
#         )
#         or app_ut.get_source_value(
#             resume_data_flat, app_ut.FIELD_ALIASES["first_name"]
#         )
#     )

#     last_name = (
#         app_ut.get_source_value(
#             candidate_data, app_ut.FIELD_ALIASES["last_name"]
#         )
#         or app_ut.get_source_value(
#             resume_data_flat, app_ut.FIELD_ALIASES["last_name"]
#         )
#     )

#     if first_name and last_name:

#         full_name = f"{first_name} {last_name}"

#         if app_ut.get_source_value(
#             candidate_data, app_ut.FIELD_ALIASES["name"]
#         ) is None:
#             candidate_data["full_name"] = full_name

#         if app_ut.get_source_value(
#             resume_data_flat, app_ut.FIELD_ALIASES["name"]
#         ) is None:
#             resume_data_flat["full_name"] = full_name

#     mapped_fields = []
#     unmatched_fields = []
#     manual_required_fields = []

#     # ==========================================
#     # FIELD MAPPING
#     # ==========================================

#     for field in fields:

#         if not isinstance(field, dict):
#             unmatched_fields.append(field)
#             continue

#         label = str(field.get("label") or "")
#         field_name = str(field.get("name") or "")
#         field_id = str(field.get("id") or "")
#         field_type = (field.get("type") or "").lower()

#         # F2: constraints must be a dict, anything else ignored
#         constraints = field.get("constraints")
#         if not isinstance(constraints, dict):
#             constraints = {}

#         value = None
#         value_source = None
#         manual_required = False
#         manual_reason = None

#         required = app_ut.is_required(field)

#         canonical_key = (
#             app_ut.canonical(field_name)
#             or app_ut.canonical(field_id)
#             or app_ut.canonical(label)
#         )

#         # F1: never KeyError on unknown canonical keys — fall back to the
#         # canonical key itself as a direct source lookup
#         aliases = None
#         if canonical_key:
#             aliases = app_ut.FIELD_ALIASES.get(canonical_key) or [canonical_key]

#         # ==========================================
#         # READONLY FIELDS
#         # ==========================================

#         if constraints.get("readonly"):

#             value = app_ut.clean_value(field.get("value"))

#             if value is not None:
#                 value_source = "website_readonly"

#             else:
#                 manual_required = True
#                 manual_reason = "Readonly field with no prefilled value."

#         # ==========================================
#         # MANUAL DECLARATIONS
#         # ==========================================

#         elif app_ut.requires_manual_answer(field):

#             manual_required = True
#             manual_reason = (
#                 "Declarative/eligibility question — candidate must answer."
#             )

#         else:

#             handled = False

#             # ======================================
#             # PHONE COUNTRY CODE
#             # ======================================

#             # Only treat this as a dedicated CC selector — NOT a phone
#             # input whose label merely mentions "country code" (e.g.
#             # Lever's "Phone (include country code)")
#             _label_norm = app_ut._norm(label)
#             _name_or_id = (field_name or field_id).lower()
#             _is_cc_selector = (
#                 "country code" in _label_norm
#                 and (
#                     field_type in app_ut._SELECT_TYPES
#                     or canonical_key in ("phone_country_code", "country_code")
#                     or "country" in _name_or_id
#                 )
#             )

#             if _is_cc_selector:

#                 phone_val = app_ut.get_source_value(
#                     candidate_data,
#                     app_ut.FIELD_ALIASES["phone"]
#                 )

#                 cc_source = "candidate_profile"

#                 if phone_val is None:

#                     phone_val = app_ut.get_source_value(
#                         resume_data_flat,
#                         app_ut.FIELD_ALIASES["phone"]
#                     )

#                     if phone_val is not None:
#                         cc_source = "resume"

#                 prefix_match = re.match(
#                     r"^\s*(\+\d{1,4})",
#                     str(phone_val or "")
#                 )

#                 if prefix_match:

#                     options = field.get("options") or []

#                     opt = app_ut.match_option(
#                         options,
#                         prefix_match.group(1)
#                     )

#                     if opt is not None:

#                         value = (
#                             opt.get("value")
#                             if opt.get("value") not in (None, "")
#                             else prefix_match.group(1)
#                         )

#                         value_source = cc_source
#                         handled = True

#                     elif not options:
#                         # F6: no options -> plain text input; the prefix
#                         # itself is the correct value
#                         value = prefix_match.group(1)
#                         value_source = cc_source
#                         handled = True

#             # ======================================
#             # RADIO / CHECKBOX / MULTISELECT
#             # ======================================

#             if not handled and field_type in app_ut._CHOICE_TYPES:

#                 options = field.get("options") or []

#                 raw = None
#                 raw_source = None

#                 if aliases:

#                     raw = app_ut.get_source_value(candidate_data, aliases)
#                     raw_source = "candidate_profile"

#                     if raw is None:
#                         raw = app_ut.get_source_value(resume_data_flat, aliases)
#                         raw_source = "resume"

#                 if (
#                     options
#                     and raw is not None
#                     and app_ut._is_checkbox_type(field_type)
#                 ):

#                     wanted_items = app_ut._as_choice_list(raw)

#                     matched_options = []
#                     all_matched = bool(wanted_items)

#                     for item in wanted_items:

#                         opt = app_ut.match_option(options, item)

#                         if opt is None:
#                             all_matched = False
#                             break

#                         matched_options.append(opt)

#                     if all_matched and matched_options:

#                         value = [
#                             str(
#                                 opt.get("label")
#                                 or opt.get("text")
#                                 or opt.get("value")
#                             )
#                             for opt in matched_options
#                         ]

#                         value_source = raw_source

#                     else:

#                         manual_required = True
#                         manual_reason = (
#                             "Selected value(s) not present in checkbox options."
#                         )

#                 elif options and raw is not None:

#                     opt = app_ut.match_option(options, raw)

#                     if opt is not None:

#                         value = (
#                             opt.get("value")
#                             if opt.get("value") not in (None, "")
#                             else (opt.get("label") or opt.get("text"))
#                         )

#                         value_source = raw_source

#                     else:

#                         manual_required = True
#                         manual_reason = (
#                             "Profile value not found in radio options."
#                         )

#                 else:

#                     manual_required = True

#                     manual_reason = (
#                         "Single choice/consent field — manual answer safest."
#                         if not options
#                         else "No matching profile value for choice field."
#                     )

#             # ======================================
#             # RULE-BASED MATCHING
#             # ======================================

#             elif not handled and aliases:

#                 value = app_ut.get_source_value(candidate_data, aliases)
#                 value_source = "candidate_profile"

#                 if value is None:

#                     value = app_ut.get_source_value(resume_data_flat, aliases)
#                     value_source = "resume"

#                 if value is not None and (
#                     field_type in app_ut._SELECT_TYPES
#                     or app_ut._is_checkbox_type(field_type)
#                 ):

#                     options = field.get("options") or []

#                     if options:

#                         if app_ut._is_checkbox_type(field_type):
#                             # F4: multiselect reaching rule-based matching —
#                             # every wanted item must exist in options
#                             wanted_items = app_ut._as_choice_list(value)
#                             matched = all(
#                                 app_ut.match_option(options, item) is not None
#                                 for item in wanted_items
#                             )

#                             if matched and wanted_items:
#                                 value = [
#                                     str(
#                                         o.get("label")
#                                         or o.get("text")
#                                         or o.get("value")
#                                     )
#                                     for o in (
#                                         app_ut.match_option(options, item)
#                                         for item in wanted_items
#                                     )
#                                 ]
#                             else:
#                                 manual_required = True
#                                 manual_reason = (
#                                     "Selected value(s) not present in "
#                                     "multiselect options."
#                                 )
#                                 value = None
#                                 value_source = None

#                         elif app_ut.match_option(options, value) is None:
#                             manual_required = True
#                             manual_reason = (
#                                 "Profile value not present in dropdown options."
#                             )
#                             value = None
#                             value_source = None

#                         else:
#                             # F5: use the canonical option value so custom
#                             # selects (Workday/Greenhouse) fill correctly
#                             opt = app_ut.match_option(options, value)
#                             canonical_value = opt.get("value")
#                             if canonical_value not in (None, ""):
#                                 value = canonical_value

#                 # F9: scalar values for text-ish inputs become strings
#                 if (
#                     value is not None
#                     and field_type not in app_ut._CHOICE_TYPES
#                     and isinstance(value, (int, float))
#                     and not isinstance(value, bool)
#                 ):
#                     value = str(value)

#         # ==========================================
#         # MANUAL REQUIRED FIELDS
#         # ==========================================

#         if manual_required:

#             manual_required_fields.append({

#                 "id": field.get("id"),
#                 "label": label,
#                 "reason": manual_reason,
#                 "required": required,

#             })

#         # ==========================================
#         # SAVE MATCHED / UNMATCHED
#         # ==========================================

#         if value is not None:

#             mapped_fields.append({

#                 "selector": field.get("selector"),
#                 "widget_selector": field.get("widget_selector"),
#                 "is_custom_select": field.get(
#                     "is_custom_select", False
#                 ),
#                 "container_selector": field.get(
#                     "container_selector"
#                 ),

#                 "options": field.get("options") or [],   # F7
#                 "constraints": constraints,

#                 "name": field.get("name"),
#                 "id": field.get("id"),

#                 "required": required,
#                 "control_visible": field.get(
#                     "control_visible", True
#                 ),

#                 "label": label,
#                 "value": value,
#                 "type": field_type,

#                 "value_source": value_source,
#                 "manual_required": manual_required,

#             })

#         else:

#             unmatched_fields.append(field)

#     # ==========================================
#     # REMAINING WEB DATA
#     # ==========================================

#     remaining_web_data = (
#         {"fields": unmatched_fields}
#         if unmatched_fields
#         else None
#     )

#     ruled_output={
#         "fields": mapped_fields,
#         "manual_required_fields": manual_required_fields
#     }
        
#     return ruled_output,  remaining_web_data



import json
import application.app_utility as app_ut
import re


def rule_map(fields, resume, candidate_profile):

    if isinstance(fields, str):
        fields = json.loads(fields)

    if isinstance(resume, str):
        resume = json.loads(resume)

    if isinstance(candidate_profile, str):
        candidate_profile = json.loads(candidate_profile)

    if not isinstance(fields, list):
        raise TypeError("fields must be a list")

    candidate_data = app_ut.flatten_data(candidate_profile)
    resume_data_flat = app_ut.flatten_data(resume)

    # ==========================================
    # SYNTHESIZE FULL NAME
    # ==========================================

    first_name = (
        app_ut.get_source_value(
            candidate_data, app_ut.FIELD_ALIASES["first_name"]
        )
        or app_ut.get_source_value(
            resume_data_flat, app_ut.FIELD_ALIASES["first_name"]
        )
    )

    last_name = (
        app_ut.get_source_value(
            candidate_data, app_ut.FIELD_ALIASES["last_name"]
        )
        or app_ut.get_source_value(
            resume_data_flat, app_ut.FIELD_ALIASES["last_name"]
        )
    )

    if first_name and last_name:

        full_name = f"{first_name} {last_name}"

        if app_ut.get_source_value(
            candidate_data, app_ut.FIELD_ALIASES["name"]
        ) is None:
            candidate_data["full_name"] = full_name

        if app_ut.get_source_value(
            resume_data_flat, app_ut.FIELD_ALIASES["name"]
        ) is None:
            resume_data_flat["full_name"] = full_name

    mapped_fields = []
    unmatched_fields = []
    manual_required_fields = []

    # ==========================================
    # FIELD MAPPING
    # ==========================================

    for field in fields:

        if not isinstance(field, dict):
            # BUGFIX: non-dict garbage must NOT be appended to
            # unmatched_fields — ai_map and filler call .get() on every
            # remaining field and would crash on it. Drop it here.
            continue

        label = str(field.get("label") or "")
        field_name = str(field.get("name") or "")
        field_id = str(field.get("id") or "")
        field_type = (field.get("type") or "").lower()

        # F2: constraints must be a dict, anything else ignored
        constraints = field.get("constraints")
        if not isinstance(constraints, dict):
            constraints = {}

        value = None
        value_source = None
        manual_required = False
        manual_reason = None

        required = app_ut.is_required(field)

        # BUGFIX: canonical_key was built with `or` short-circuiting, so a
        # meaningless id ("cl", "f1", "txt1") shadowed the label entirely
        # and the field never matched via its label alias (e.g. a
        # contenteditable "Cover Letter" with id="cl" stayed unmatched).
        # Collect ALL candidate keys and try them in priority order.
        candidate_keys = []
        for source in (field_name, field_id, label):
            key = app_ut.canonical(source) if source else None
            if key and key not in candidate_keys:
                candidate_keys.append(key)

        # F1: never KeyError on unknown canonical keys — fall back to the
        # canonical key itself as a direct source lookup
        alias_lists = []
        for key in candidate_keys:
            aliases = app_ut.FIELD_ALIASES.get(key) or [key]
            if aliases not in alias_lists:
                alias_lists.append(aliases)

        def lookup_value(flat_data):
            """First non-empty value across alias lists (priority order)."""
            for aliases in alias_lists:
                found = app_ut.get_source_value(flat_data, aliases)
                if found is not None:
                    return found
            return None

        # ==========================================
        # READONLY FIELDS
        # ==========================================

        if constraints.get("readonly"):

            value = app_ut.clean_value(field.get("value"))

            if value is not None:
                value_source = "website_readonly"

            else:
                manual_required = True
                manual_reason = "Readonly field with no prefilled value."

        # ==========================================
        # MANUAL DECLARATIONS
        # ==========================================

        elif app_ut.requires_manual_answer(field):

            manual_required = True
            manual_reason = (
                "Declarative/eligibility question — candidate must answer."
            )

        else:

            handled = False

            # ======================================
            # PHONE COUNTRY CODE
            # ======================================

            # Only treat this as a dedicated CC selector — NOT a phone
            # input whose label merely mentions "country code" (e.g.
            # Lever's "Phone (include country code)")
            _label_norm = app_ut._norm(label)
            _name_or_id = (field_name or field_id).lower()
            _is_cc_selector = (
                "country code" in _label_norm
                and (
                    field_type in app_ut._SELECT_TYPES
                    or app_ut.canonical_key in ("phone_country_code", "country_code")
                    or "country" in _name_or_id
                )
            )

            if _is_cc_selector:

                phone_val = app_ut.get_source_value(
                    candidate_data,
                    app_ut.FIELD_ALIASES["phone"]
                )

                cc_source = "candidate_profile"

                if phone_val is None:

                    phone_val = app_ut.get_source_value(
                        resume_data_flat,
                        app_ut.FIELD_ALIASES["phone"]
                    )

                    if phone_val is not None:
                        cc_source = "resume"

                prefix_match = re.match(
                    r"^\s*(\+\d{1,4})",
                    str(phone_val or "")
                )

                if prefix_match:

                    options = field.get("options") or []

                    opt = app_ut.match_option(
                        options,
                        prefix_match.group(1)
                    )

                    if opt is not None:

                        value = (
                            opt.get("value")
                            if opt.get("value") not in (None, "")
                            else prefix_match.group(1)
                        )

                        value_source = cc_source
                        handled = True

                    elif not options:
                        # F6: no options -> plain text input; the prefix
                        # itself is the correct value
                        value = prefix_match.group(1)
                        value_source = cc_source
                        handled = True

            # ======================================
            # RADIO / CHECKBOX / MULTISELECT
            # ======================================

            if not handled and field_type in app_ut._CHOICE_TYPES:

                options = field.get("options") or []

                raw = None
                raw_source = None

                if alias_lists:

                    raw = lookup_value(candidate_data)
                    raw_source = "candidate_profile"

                    if raw is None:
                        raw = lookup_value(resume_data_flat)
                        raw_source = "resume"

                if (
                    options
                    and raw is not None
                    and app_ut._is_checkbox_type(field_type)
                ):

                    wanted_items = app_ut._as_choice_list(raw)

                    matched_options = []
                    all_matched = bool(wanted_items)

                    for item in wanted_items:

                        opt = app_ut.match_option(options, item)

                        if opt is None:
                            all_matched = False
                            break

                        matched_options.append(opt)

                    if all_matched and matched_options:

                        value = [
                            str(
                                opt.get("label")
                                or opt.get("text")
                                or opt.get("value")
                            )
                            for opt in matched_options
                        ]

                        value_source = raw_source

                    else:

                        manual_required = True
                        manual_reason = (
                            "Selected value(s) not present in checkbox options."
                        )

                elif options and raw is not None:

                    opt = app_ut.match_option(options, raw)

                    if opt is not None:

                        value = (
                            opt.get("value")
                            if opt.get("value") not in (None, "")
                            else (opt.get("label") or opt.get("text"))
                        )

                        value_source = raw_source

                    else:

                        manual_required = True
                        manual_reason = (
                            "Profile value not found in radio options."
                        )

                else:

                    manual_required = True

                    manual_reason = (
                        "Single choice/consent field — manual answer safest."
                        if not options
                        else "No matching profile value for choice field."
                    )

            # ======================================
            # RULE-BASED MATCHING
            # ======================================

            elif not handled and alias_lists:

                value = lookup_value(candidate_data)
                value_source = "candidate_profile"

                if value is None:

                    value = lookup_value(resume_data_flat)
                    value_source = "resume"

                if value is not None and (
                    field_type in app_ut._SELECT_TYPES
                    or app_ut._is_checkbox_type(field_type)
                ):

                    options = field.get("options") or []

                    if options:

                        if app_ut._is_checkbox_type(field_type):
                            # F4: multiselect reaching rule-based matching —
                            # every wanted item must exist in options
                            wanted_items = app_ut._as_choice_list(value)
                            matched = all(
                                app_ut.match_option(options, item) is not None
                                for item in wanted_items
                            )

                            if matched and wanted_items:
                                value = [
                                    str(
                                        o.get("label")
                                        or o.get("text")
                                        or o.get("value")
                                    )
                                    for o in (
                                        app_ut.match_option(options, item)
                                        for item in wanted_items
                                    )
                                ]
                            else:
                                manual_required = True
                                manual_reason = (
                                    "Selected value(s) not present in "
                                    "multiselect options."
                                )
                                value = None
                                value_source = None

                        elif app_ut.match_option(options, value) is None:
                            manual_required = True
                            manual_reason = (
                                "Profile value not present in dropdown options."
                            )
                            value = None
                            value_source = None

                        else:
                            # F5: use the canonical option value so custom
                            # selects (Workday/Greenhouse) fill correctly
                            opt = app_ut.match_option(options, value)
                            canonical_value = opt.get("value")
                            if canonical_value not in (None, ""):
                                value = canonical_value

                # F9: scalar values for text-ish inputs become strings
                if (
                    value is not None
                    and field_type not in app_ut._CHOICE_TYPES
                    and isinstance(value, (int, float))
                    and not isinstance(value, bool)
                ):
                    value = str(value)

        # ==========================================
        # MANUAL REQUIRED FIELDS
        # ==========================================

        if manual_required:

            manual_required_fields.append({

                "id": field.get("id"),
                "label": label,
                "reason": manual_reason,
                "required": required,

            })

        # ==========================================
        # SAVE MATCHED / UNMATCHED
        # ==========================================

        if value is not None:

            mapped_fields.append({

                "selector": field.get("selector"),
                "widget_selector": field.get("widget_selector"),
                "is_custom_select": field.get(
                    "is_custom_select", False
                ),
                "container_selector": field.get(
                    "container_selector"
                ),

                "options": field.get("options") or [],   # F7
                "constraints": constraints,

                # BUGFIX: pass the contenteditable flag through — the
                # scraper sets it, filler needs it to pick the right fill
                # branch (rich-text fields have no input value).
                "contenteditable": bool(
                    field.get("contenteditable")
                ),

                "name": field.get("name"),
                "id": field.get("id"),

                "required": required,
                "control_visible": field.get(
                    "control_visible", True
                ),

                "label": label,
                "value": value,
                "type": field_type,

                "value_source": value_source,
                "manual_required": manual_required,

            })

        else:

            unmatched_fields.append(field)

    # ==========================================
    # REMAINING WEB DATA
    # ==========================================

    remaining_web_data = (
        {"fields": unmatched_fields}
        if unmatched_fields
        else None
    )

    ruled_output={
        "fields": mapped_fields,
        "manual_required_fields": manual_required_fields
    }
        
    return ruled_output,  remaining_web_data
