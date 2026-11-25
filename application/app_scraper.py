# def app_scrap(page):
#     page.wait_for_load_state(
#         "domcontentloaded",
#         timeout=15000
#     )

#     page.wait_for_timeout(1000)

#     scraped_data = page.evaluate("""
#     () => {

#         // ==========================================
#         // 1. HELPER FUNCTIONS
#         // ==========================================

#         const getText = el => {

#             return el?.innerText
#                 ?.trim()
#                 .replace(/\\s+/g, " ") || "";

#         };


#         const isVisible = el => {

#             if (!el) return false;

#             const style = getComputedStyle(el);
#             const rect = el.getBoundingClientRect();

#             return (
#                 style.display !== "none" &&
#                 style.visibility !== "hidden" &&
#                 style.opacity !== "0" &&
#                 rect.width > 0 &&
#                 rect.height > 0
#             );

#         };


#         const escapeCSS = value =>
#             CSS.escape(String(value));


#         const getSelector = el => {

#             if (!el) return null;

#             if (el.id) {
#                 return `#${escapeCSS(el.id)}`;
#             }

#             if (el.name) {

#                 return (
#                     `${el.tagName.toLowerCase()}` +
#                     `[name="${escapeCSS(el.name)}"]`
#                 );

#             }

#             // Oracle composite phone widget: the actual number input
#             // has no id/name, so give it a stable class selector.
#             if (el.matches("input.phone-row__input")) {
#                 return "input.phone-row__input";
#             }

#             for (const attr of [
#                 "data-field-id",
#                 "data-testid",
#                 "data-control-id"
#             ]) {
#                 const value = el.getAttribute(attr);
#                 if (value) {
#                     return `[${attr}="${escapeCSS(value)}"]`;
#                 }
#             }

#             return null;

#         };


#         const getAttribute = (el, attr) => {

#             return el?.getAttribute(attr) ?? null;

#         };


#         const getNumberAttribute = (el, attr) => {

#             const value = getAttribute(el, attr);

#             if (value === null || value === "") {
#                 return null;
#             }

#             const number = Number(value);

#             return Number.isNaN(number) ? null : number;

#         };


#         // ==========================================
#         // 2. QUESTION CONTAINER
#         // ==========================================

#         const getQuestionContainer = el => {

#             if (!el) return null;

#             return el.closest(`
#                 [data-questionid],
#                 [data-question-id],
#                 [data-field-id],
#                 [role="listitem"],
#                 fieldset,
#                 .question,
#                 .application-question
#             `);

#         };


#         const getContainer = el => {

#             return (
#                 getQuestionContainer(el) ||
#                 el?.closest(`
#                     .form-group,
#                     .form-field,
#                     .field-container,
#                     [role="group"],
#                     [role="radiogroup"]
#                 `) ||
#                 el?.parentElement ||
#                 null
#             );

#         };


#         // ==========================================
#         // 3. CONTAINER SELECTOR
#         // ==========================================

#         const getContainerSelector = container => {

#             if (!container) return null;

#             if (container.id) {

#                 return `#${escapeCSS(container.id)}`;

#             }

#             const attributes = [
#                 "data-questionid",
#                 "data-question-id",
#                 "data-field-id"
#             ];

#             for (const attr of attributes) {

#                 const value =
#                     container.getAttribute(attr);

#                 if (value) {

#                     return (
#                         `[${attr}="${escapeCSS(value)}"]`
#                     );

#                 }

#             }

#             return null;

#         };


#         // ==========================================
#         // 4. LABEL EXTRACTION
#         // ==========================================

#         const getLabel = (el, container) => {

#             if (!el) return "";

#             // Prefer the exact label associated with this field.
#             if (el.id) {
#                 const label = document.querySelector(
#                     `label[for="${escapeCSS(el.id)}"]`
#                 );
#                 if (label && getText(label)) return getText(label);
#             }

#             const labelledBy = el.getAttribute("aria-labelledby");
#             if (labelledBy) {
#                 const text = labelledBy
#                     .split(/\\s+/)
#                     .map(id => document.getElementById(id))
#                     .filter(Boolean)
#                     .map(getText)
#                     .filter(Boolean)
#                     .join(" ");
#                 if (text) return text;
#             }

#             const ariaLabel = el.getAttribute("aria-label");
#             if (ariaLabel?.trim()) return ariaLabel.trim();

#             const parentLabel = el.closest("label");
#             if (parentLabel && getText(parentLabel)) {
#                 return getText(parentLabel);
#             }

#             // Avoid taking the entire question/instruction container text.
#             if (container) {
#                 const questionLabel = container.querySelector(`
#                     .question-label label,
#                     .field-label,
#                     label:not(:has(input)),
#                     legend,
#                     [data-testid="field-label"]
#                 `);
#                 if (questionLabel && getText(questionLabel)) {
#                     return getText(questionLabel);
#                 }
#             }

#             return el.getAttribute("placeholder")?.trim() || "";
#         };


#         // ==========================================
#         // 5. SELECT2 DETECTION
#         // ==========================================

#         const getSelect2Widget = (select, container) => {

#             if (!select || !container) return null;

#             // First try to find the widget associated
#             // with this particular native select.

#             let widget = null;

#             if (select.id) {

#                 const generatedId =
#                     `select2-${select.id}-container`;

#                 const selection =
#                     document.getElementById(generatedId);

#                 if (selection) {

#                     widget = selection.closest(
#                         ".select2-selection"
#                     );

#                 }

#             }


#             // Fallback: search inside the container.

#             if (!widget) {

#                 const widgets = [
#                     ...container.querySelectorAll(`
#                         .select2-selection,
#                         [role="combobox"],
#                         [aria-haspopup="listbox"]
#                     `)
#                 ];

#                 widget = widgets.find(isVisible) || null;

#             }

#             return isVisible(widget) ? widget : null;

#         };


#         // ==========================================
#         // 6. FIELD SELECTOR
#         // ==========================================

#         const getFieldSelector = (el, container) => {

#             // The Oracle phone number input has no id or name.
#             if (el.matches("input.phone-row__input")) {
#                 return "input.phone-row__input";
#             }

#             const directSelector = getSelector(el);

#             if (directSelector) {
#                 return directSelector;
#             }

#             const containerSelector =
#                 getContainerSelector(container);

#             if (containerSelector) {

#                 const tag =
#                     el.tagName.toLowerCase();

#                 const type =
#                     el.getAttribute("type");

#                 if (tag === "input" && type) {

#                     return (
#                         `${containerSelector} ` +
#                         `input[type="${type}"]`
#                     );

#                 }

#                 return `${containerSelector} ${tag}`;

#             }

#             return null;

#         };


#         // ==========================================
#         // 7. REQUIRED CHECK
#         // ==========================================

#         const isRequired = (el, container) => {

#             return !!(
#                 el?.required ||
#                 el?.getAttribute("aria-required") === "true" ||
#                 container?.querySelector(`
#                     [aria-required="true"],
#                     .required
#                 `)
#             );

#         };


#         // ==========================================
#         // 8. FIND FORMS
#         // ==========================================

#         const forms = [...document.forms];

#         const form = forms.find(f =>
#             f.querySelector(`
#                 input:not([type="hidden"]),
#                 textarea,
#                 select
#             `)
#         ) || forms[0] || null;


#         // ==========================================
#         // 9. FIND NATIVE FIELDS
#         // ==========================================

#         const allElements = [
#             ...document.querySelectorAll(`
#                 input:not([type="hidden"]),
#                 textarea,
#                 select,
#                 [contenteditable="true"],
#                 [role="combobox"],
#                 [aria-haspopup="listbox"]
#             `)
#         ];


#         const elements = allElements.filter(el => {

#             if (el.disabled) return false;

#             // Native radio / checkbox with visible custom wrapper
#             if (
#                 el.type === "radio" ||
#                 el.type === "checkbox"
#             ) {

#                 const wrapper = el.closest(".custom-control");

#                 return wrapper
#                     ? isVisible(wrapper)
#                     : isVisible(el);

#             }

#             if (isVisible(el)) return true;

#             // Hidden native select with visible Select2

#             if (el.tagName === "SELECT") {

#                 const container = getContainer(el);

#                 return !!getSelect2Widget(
#                     el,
#                     container
#                 );

#             }

#             return false;

#         });


#         const fields = [];

#         const processed = new Set();


#         // ==========================================
#         // 10. NATIVE FIELD EXTRACTION
#         // ==========================================

#         elements.forEach(el => {

#             if (processed.has(el)) return;

#             const container = getContainer(el);

#             const tag = el.tagName.toLowerCase();

#             const nativeInputType =
#                 tag === "input"
#                     ? (el.getAttribute("type") || "text").toLowerCase()
#                     : null;

#             const type =
#                 el.getAttribute("role") === "combobox" ||
#                 el.getAttribute("aria-haspopup") === "listbox"
#                     ? "combobox"
#                     : (tag === "input" ? nativeInputType : tag);


#             // --------------------------------------
#             // RADIO / CHECKBOX GROUP
#             // --------------------------------------

#             if (
#                 type === "radio" ||
#                 type === "checkbox"
#             ) {

#                 const name = el.name;

#                 const questionContainer =
#                     getQuestionContainer(el) ||
#                     container;


#                 const group = elements.filter(other => {

#                     if (
#                         other.type !== type ||
#                         other.name !== name
#                     ) {
#                         return false;
#                     }

#                     return (
#                         (
#                             getQuestionContainer(other) ||
#                             getContainer(other)
#                         ) === questionContainer
#                     );

#                 });


#                 group.forEach(item =>
#                     processed.add(item)
#                 );


#                 const label =
#                     questionContainer?.querySelector(`
#                         .question-label label,
#                         .question-title,
#                         legend,
#                         .form-label
#                     `);


#                 const questionText =
#                     getText(label);


#                 const options = group.map(item => {

#                     const optionLabel = item.id
#                         ? document.querySelector(
#                             `label[for="${escapeCSS(item.id)}"]`
#                         )
#                         : null;

#                     return {

#                         label:
#                             getText(optionLabel) ||
#                             item.getAttribute("aria-label") ||
#                             getText(item.parentElement),

#                         value: item.value,

#                         selected: item.checked,

#                         selector: getSelector(item)

#                     };

#                 });


#                 fields.push({

#                     label:
#                         questionText ||
#                         getLabel(el, questionContainer),

#                     type: type,

#                     name: name || null,

#                     id: null,

#                     selector: name
#                         ? (
#                             questionContainer &&
#                             getContainerSelector(questionContainer)
#                             ? (
#                                 `${getContainerSelector(questionContainer)} ` +
#                                 `input[name="${escapeCSS(name)}"]`
#                             )
#                             : `input[name="${escapeCSS(name)}"]`
#                         )
#                         : getSelector(el),

#                     required: group.some(item =>
#                         isRequired(item, questionContainer)
#                     ),

#                     value: null,

#                     options: options

#                 });

#                 return;

#             }


#             // --------------------------------------
#             // NORMAL INPUT / SELECT / TEXTAREA
#             // --------------------------------------

#             processed.add(el);


#             let label = getLabel(
#                 el,
#                 container
#             );

#             // Oracle phone widgets expose the country-code picker as a
#             // separate combobox. Keep it distinct from the actual phone input.
#             const elementId = (el.id || "").toLowerCase();
#             const elementName = (el.name || "").toLowerCase();
#             if (
#                 elementId.includes("country-codes-dropdown") ||
#                 elementName.includes("countrycode")
#             ) {
#                 label = "Phone Country Code";
#             }


#             // --------------------------------------
#             // OPTIONS
#             // --------------------------------------

#             let options = [];

#             if (tag === "select") {

#                 options = [...el.options].map(option => ({

#                     text: option.text.trim(),

#                     value: option.value,

#                     selected: option.selected,

#                     disabled: option.disabled

#                 }));

#             }


#             // --------------------------------------
#             // SELECT2
#             // --------------------------------------

#             const select2Widget =
#                 tag === "select"
#                 ? getSelect2Widget(el, container)
#                 : null;


#             const containerSelector =
#                 getContainerSelector(container);


#             const widgetSelector = select2Widget
#                 ? getSelector(select2Widget) ||
#                     (
#                         containerSelector
#                         ? `${containerSelector} .select2-selection`
#                         : null
#                     )
#                 : null;


#             // --------------------------------------
#             // HTML VALIDATION CONSTRAINTS
#             // --------------------------------------

#             const constraints = {

#                 max_length:
#                     getNumberAttribute(el, "maxlength"),

#                 min_length:
#                     getNumberAttribute(el, "minlength"),

#                 max:
#                     getAttribute(el, "max"),

#                 min:
#                     getAttribute(el, "min"),

#                 pattern:
#                     getAttribute(el, "pattern"),

#                 step:
#                     getAttribute(el, "step"),

#                 required:
#                     isRequired(el, container),

#                 readonly:
#                     !!el.readOnly,

#                 disabled:
#                     !!el.disabled

#             };


#             // --------------------------------------
#             // FIELD DATA
#             // --------------------------------------

#             fields.push({

#                 label: label,

#                 type: type,

#                 input_type: nativeInputType,

#                 tag: tag,

#                 autocomplete:
#                     getAttribute(el, "autocomplete"),

#                 input_mode:
#                     getAttribute(el, "inputmode"),

#                 multiple:
#                     !!el.multiple,

#                 contenteditable:
#                     el.getAttribute("contenteditable") === "true",

#                 role: getAttribute(el, "role"),

#                 aria_haspopup:
#                     getAttribute(el, "aria-haspopup"),

#                 popup_selector: (() => {
#                     const controlledId = getAttribute(el, "aria-controls");
#                     return controlledId ? `#${escapeCSS(controlledId)}` : null;
#                 })(),

#                 name: el.name || null,

#                 id: el.id || null,

#                 placeholder:
#                     getAttribute(el, "placeholder"),

#                 aria_label:
#                     getAttribute(el, "aria-label"),

#                 required:
#                     constraints.required,

#                 value: el.value ?? null,

#                 options: options,

#                 selector: getFieldSelector(
#                     el,
#                     container
#                 ),

#                 container_selector:
#                     containerSelector,

#                 widget_selector:
#                     widgetSelector,

#                 is_custom_select:
#                     !!select2Widget ||
#                     type === "combobox" ||
#                     el.matches("[role='combobox'], [aria-haspopup='listbox']"),

#                 control_visible:
#                     isVisible(el) ||
#                     !!select2Widget,

#                 constraints:
#                     constraints

#             });

#         });


#         // ==========================================
#         // 11. CUSTOM RADIO / CHECKBOX
#         // ==========================================

#         const customControls = [
#             ...document.querySelectorAll(`
#                 [role="radio"],
#                 [role="checkbox"]
#             `)
#         ].filter(el => {

#             if (el.matches("input, button")) {
#                 return false;
#             }

#             return isVisible(el);

#         });


#         const customGroups = new Map();


#         customControls.forEach(el => {

#             const container = getContainer(el);

#             const role =
#                 el.getAttribute("role");

#             const containerSelector =
#                 getContainerSelector(container);


#             const key =
#                 role + "_" +
#                 (
#                     containerSelector ||
#                     container?.id ||
#                     customControls.indexOf(el)
#                 );


#             if (!customGroups.has(key)) {

#                 customGroups.set(key, {

#                     container: container,

#                     role: role,

#                     options: []

#                 });

#             }


#             customGroups.get(key).options.push({

#                 label:
#                     el.getAttribute("aria-label") ||
#                     getText(el),

#                 value:
#                     el.getAttribute("data-value") ||
#                     el.getAttribute("value"),

#                 selected:
#                     el.getAttribute("aria-checked") === "true",

#                 selector: getSelector(el)

#             });

#         });


#         customGroups.forEach(group => {

#             const container = group.container;

#             const labelledBy =
#                 container?.querySelector(
#                     "[aria-labelledby]"
#                 )?.getAttribute("aria-labelledby");


#             const questionLabel = labelledBy
#                 ? labelledBy
#                     .split(/\\s+/)
#                     .map(id => document.getElementById(id))
#                     .filter(Boolean)
#                     .map(getText)
#                     .join(" ")
#                 : getLabel(container, container);


#             fields.push({

#                 label: questionLabel,

#                 type: group.role,

#                 name: null,

#                 selector:
#                     getContainerSelector(container),

#                 required: !!container?.querySelector(
#                     '[aria-required="true"]'
#                 ),

#                 options: group.options

#             });

#         });


#         // ==========================================
#         // 12. BUTTON SELECTOR
#         // ==========================================

#         const getButtonSelector = el => {

#             if (!el) return null;

#             if (el.id) {
#                 return `#${escapeCSS(el.id)}`;
#             }

#             if (el.name) {
#                 return `${el.tagName.toLowerCase()}[name="${escapeCSS(el.name)}"]`;
#             }

#             const attributes = [
#                 "atm-id",
#                 "data-testid",
#                 "data-action",
#                 "data-id"
#             ];

#             for (const attr of attributes) {

#                 const value = el.getAttribute(attr);

#                 if (value) {
#                     return `[${attr}="${escapeCSS(value)}"]`;
#                 }

#             }

#             const classes = [...el.classList];

#             if (classes.length) {

#                 const selector =
#                     el.tagName.toLowerCase() +
#                     "." +
#                     classes.map(escapeCSS).join(".");

#                 if (document.querySelectorAll(selector).length === 1) {
#                     return selector;
#                 }

#             }

#             const text = getText(el) || el.value;

#             if (text) {

#                 const tag = el.tagName.toLowerCase();

#                 const matches = [...document.querySelectorAll(tag)]
#                     .filter(btn =>
#                         isVisible(btn) &&
#                         (getText(btn) || btn.value) === text
#                     );

#                 if (matches.length === 1) {
#                     return `${tag}:has-text("${text}")`;
#                 }

#             }

#             return null;

#         };


#         // ==========================================
#         // 13. BUTTON EXTRACTION
#         // ==========================================

#         const buttons = [
#             ...document.querySelectorAll(`
#                 button,
#                 input[type="submit"],
#                 input[type="button"],
#                 input[type="reset"],
#                 a[role="button"],
#                 [role="button"]
#             `)
#         ]
#         .filter(el => {

#             return (
#                 isVisible(el) &&
#                 !el.disabled &&
#                 el.getAttribute("aria-disabled") !== "true"
#             );

#         })
#         .map(el => {

#             return {

#                 text:
#                     getText(el) || el.value || "",

#                 type:
#                     el.getAttribute("type") ||
#                     el.getAttribute("role") ||
#                     el.tagName.toLowerCase(),

#                 name:
#                     el.name || null,

#                 id:
#                     el.id || null,

#                 selector:
#                     getButtonSelector(el),

#                 disabled:
#                     el.disabled || false,

#                 aria_label:
#                     el.getAttribute("aria-label")

#             };

#         });


#         // ==========================================
#         // 14. RESUME / CV UPLOAD EXTRACTION
#         // ==========================================

#         const resumeFileInput =
#             document.querySelector('.resume-upload-wrapper input[type="file"]') ||
#             document.querySelector('input[type="file"]');

#         const resumeUploadWrapper =
#             resumeFileInput?.closest(".resume-upload-wrapper") ||
#             resumeFileInput?.parentElement ||
#             document.querySelector(".resume-section");

#         const resumeUploadButton =
#             resumeUploadWrapper?.querySelector(
#                 'button[atm-id="resume-button"], button.upload-resume-btn'
#             ) ||
#             document.querySelector(
#                 'button[atm-id="resume-button"], button.upload-resume-btn'
#             );

#         const resumeSectionText =
#             getText(document.querySelector(".resume-section")) ||
#             getText(resumeUploadWrapper);

#         const acceptedFileTypes = ["DOC", "DOCX", "HTML", "PDF", "TXT"]
#             .filter(extension =>
#                 new RegExp("\\\\b" + extension + "\\\\b", "i")
#                     .test(resumeSectionText)
#             );

#         const maxSizeMatch =
#             resumeSectionText.match(/(\\d+(?:\\.\\d+)?)\\s*(MB|KB)/i);

#         const resumeMetadataIds = [
#             "resumePath",
#             "resumeName",
#             "resumeFileSize",
#             "resumeBucketId",
#             "resumeRelativePath",
#             "isResume"
#         ];

#         const resumeMetadata = {};
#         resumeMetadataIds.forEach(id => {
#             const input = document.getElementById(id);
#             if (input) {
#                 resumeMetadata[id] = {
#                     selector: `#${escapeCSS(id)}`,
#                     value: input.value || null
#                 };
#             }
#         });

#         const resumeUpload = {
#             available: !!resumeFileInput,
#             section_found: !!document.querySelector(".resume-section"),
#             label:
#                 getText(resumeUploadButton) ||
#                 (resumeFileInput ? "Resume / CV upload" : null),
#             required:
#                 !!document.querySelector(
#                     ".resume-header .resume-mandatory"
#                 ),
#             file_input: resumeFileInput ? {
#                 selector: resumeFileInput.id
#                     ? `#${escapeCSS(resumeFileInput.id)}`
#                     : 'input[type="file"]',
#                 type: resumeFileInput.type,
#                 visible: isVisible(resumeFileInput),
#                 accept_attribute: resumeFileInput.getAttribute("accept"),
#                 multiple: !!resumeFileInput.multiple,
#                 disabled: !!resumeFileInput.disabled
#             } : null,
#             upload_button: resumeUploadButton ? {
#                 selector: resumeUploadButton.id
#                     ? `#${escapeCSS(resumeUploadButton.id)}`
#                     : (
#                         resumeUploadButton.getAttribute("atm-id")
#                             ? `[atm-id="${escapeCSS(resumeUploadButton.getAttribute("atm-id"))}"]`
#                             : "button.upload-resume-btn"
#                     ),
#                 text: getText(resumeUploadButton),
#                 visible: isVisible(resumeUploadButton)
#             } : null,
#             accepted_file_types: acceptedFileTypes,
#             max_file_size: maxSizeMatch ? {
#                 value: Number(maxSizeMatch[1]),
#                 unit: maxSizeMatch[2].toUpperCase()
#             } : null,
#             instructions: resumeSectionText || null,
#             uploaded_file_metadata: resumeMetadata,
#             upload_state: (
#                 resumeMetadata.resumeName?.value ||
#                 resumeMetadata.resumePath?.value ||
#                 resumeMetadata.resumeRelativePath?.value
#             ) ? "metadata_present" : "not_detected"
#         };


#         // ==========================================
#         // 15. RETURN RAW SCRAPED SNAPSHOT
#         // ==========================================

#         return {
#             has_form: !!form,
#             form_action: form?.getAttribute("action") || null,
#             form_method: form?.getAttribute("method") || null,
#             page_title: document.title,
#             page_url: location.href,
#             resume_upload: resumeUpload,
#             raw_fields: fields,
#             buttons: buttons,
#             counts: {
#                 forms: forms.length,
#                 native_fields: elements.length,
#                 custom_controls: customControls.length,
#                 file_inputs: document.querySelectorAll('input[type="file"]').length
#             }
#         };

#     }
#     """)

#     return scraped_data


def app_scrap(page):
    page.wait_for_load_state(
        "domcontentloaded",
        timeout=15000
    )

    page.wait_for_timeout(1000)

    scraped_data = page.evaluate("""
    () => {

        // ==========================================
        // 1. HELPER FUNCTIONS
        // ==========================================

        const getText = el => {

            return el?.innerText
                ?.trim()
                .replace(/\\s+/g, " ") || "";

        };


        const isVisible = el => {

            if (!el) return false;

            const style = getComputedStyle(el);
            const rect = el.getBoundingClientRect();

            return (
                style.display !== "none" &&
                style.visibility !== "hidden" &&
                style.opacity !== "0" &&
                rect.width > 0 &&
                rect.height > 0
            );

        };


        const escapeCSS = value =>
            CSS.escape(String(value));


        const getSelector = el => {

            if (!el) return null;

            if (el.id) {
                return `#${escapeCSS(el.id)}`;
            }

            if (el.name) {

                return (
                    `${el.tagName.toLowerCase()}` +
                    `[name="${escapeCSS(el.name)}"]`
                );

            }

            // Oracle composite phone widget: the actual number input
            // has no id/name, so give it a stable class selector.
            if (el.matches("input.phone-row__input")) {
                return "input.phone-row__input";
            }

            for (const attr of [
                "data-field-id",
                "data-testid",
                "data-control-id"
            ]) {
                const value = el.getAttribute(attr);
                if (value) {
                    return `[${attr}="${escapeCSS(value)}"]`;
                }
            }

            return null;

        };


        const getAttribute = (el, attr) => {

            return el?.getAttribute(attr) ?? null;

        };


        const getNumberAttribute = (el, attr) => {

            const value = getAttribute(el, attr);

            if (value === null || value === "") {
                return null;
            }

            const number = Number(value);

            return Number.isNaN(number) ? null : number;

        };


        // ==========================================
        // 2. QUESTION CONTAINER
        // ==========================================

        const getQuestionContainer = el => {

            if (!el) return null;

            return el.closest(`
                [data-questionid],
                [data-question-id],
                [data-field-id],
                [role="listitem"],
                fieldset,
                .question,
                .application-question
            `);

        };


        const getContainer = el => {

            return (
                getQuestionContainer(el) ||
                el?.closest(`
                    .form-group,
                    .form-field,
                    .field-container,
                    [role="group"],
                    [role="radiogroup"]
                `) ||
                el?.parentElement ||
                null
            );

        };


        // ==========================================
        // 3. CONTAINER SELECTOR
        // ==========================================

        const getContainerSelector = container => {

            if (!container) return null;

            if (container.id) {

                return `#${escapeCSS(container.id)}`;

            }

            const attributes = [
                "data-questionid",
                "data-question-id",
                "data-field-id"
            ];

            for (const attr of attributes) {

                const value =
                    container.getAttribute(attr);

                if (value) {

                    return (
                        `[${attr}="${escapeCSS(value)}"]`
                    );

                }

            }

            return null;

        };


        // ==========================================
        // 4. LABEL EXTRACTION
        // ==========================================

        const getLabel = (el, container) => {

            if (!el) return "";

            // Prefer the exact label associated with this field.
            if (el.id) {
                const label = document.querySelector(
                    `label[for="${escapeCSS(el.id)}"]`
                );
                if (label && getText(label)) return getText(label);
            }

            const labelledBy = el.getAttribute("aria-labelledby");
            if (labelledBy) {
                const text = labelledBy
                    .split(/\\s+/)
                    .map(id => document.getElementById(id))
                    .filter(Boolean)
                    .map(getText)
                    .filter(Boolean)
                    .join(" ");
                if (text) return text;
            }

            const ariaLabel = el.getAttribute("aria-label");
            if (ariaLabel?.trim()) return ariaLabel.trim();

            const parentLabel = el.closest("label");
            if (parentLabel && getText(parentLabel)) {
                return getText(parentLabel);
            }

            // Avoid taking the entire question/instruction container text.
            if (container) {
                const questionLabel = container.querySelector(`
                    .question-label label,
                    .field-label,
                    label:not(:has(input)),
                    legend,
                    [data-testid="field-label"]
                `);
                if (questionLabel && getText(questionLabel)) {
                    return getText(questionLabel);
                }
            }

            return el.getAttribute("placeholder")?.trim() || "";
        };


        // ==========================================
        // 5. SELECT2 DETECTION
        // ==========================================

        const getSelect2Widget = (select, container) => {

            if (!select || !container) return null;

            // First try to find the widget associated
            // with this particular native select.

            let widget = null;

            if (select.id) {

                const generatedId =
                    `select2-${select.id}-container`;

                const selection =
                    document.getElementById(generatedId);

                if (selection) {

                    widget = selection.closest(
                        ".select2-selection"
                    );

                }

            }


            // Fallback: search inside the container.

            if (!widget) {

                const widgets = [
                    ...container.querySelectorAll(`
                        .select2-selection,
                        [role="combobox"],
                        [aria-haspopup="listbox"]
                    `)
                ];

                widget = widgets.find(isVisible) || null;

            }

            return isVisible(widget) ? widget : null;

        };


        // ==========================================
        // 6. FIELD SELECTOR
        // ==========================================

        const getFieldSelector = (el, container) => {

            // The Oracle phone number input has no id or name.
            if (el.matches("input.phone-row__input")) {
                return "input.phone-row__input";
            }

            const directSelector = getSelector(el);

            if (directSelector) {
                return directSelector;
            }

            const containerSelector =
                getContainerSelector(container);

            if (containerSelector) {

                const tag =
                    el.tagName.toLowerCase();

                const type =
                    el.getAttribute("type");

                let fallbackSelector;

                if (tag === "input" && type) {

                    fallbackSelector = (
                        `${containerSelector} ` +
                        `input[type="${type}"]`
                    );

                } else {

                    fallbackSelector =
                        `${containerSelector} ${tag}`;

                }

                // BUGFIX: the container-based fallback could match MULTIPLE
                // elements (e.g. two text inputs in one fieldset) — filler
                // then aborted with "Selector matched N elements".
                // Disambiguate with a Playwright nth index.
                const matches = [
                    ...document.querySelectorAll(fallbackSelector)
                ];

                if (matches.length > 1) {

                    const index = matches.indexOf(el);

                    if (index >= 0) {

                        fallbackSelector +=
                            ` >> nth=${index}`;

                    }

                }

                return fallbackSelector;

            }

            return null;

        };


        // ==========================================
        // 7. REQUIRED CHECK
        // ==========================================

        const isRequired = (el, container) => {

            return !!(
                el?.required ||
                el?.getAttribute("aria-required") === "true" ||
                container?.querySelector(`
                    [aria-required="true"],
                    .required
                `)
            );

        };


        // ==========================================
        // 8. FIND FORMS
        // ==========================================

        const forms = [...document.forms];

        const form = forms.find(f =>
            f.querySelector(`
                input:not([type="hidden"]),
                textarea,
                select
            `)
        ) || forms[0] || null;


        // ==========================================
        // 9. FIND NATIVE FIELDS
        // ==========================================

        const allElements = [
            ...document.querySelectorAll(`
                input:not([type="hidden"]),
                textarea,
                select,
                [contenteditable="true"],
                [role="combobox"],
                [aria-haspopup="listbox"]
            `)
        ];


        const elements = allElements.filter(el => {

            if (el.disabled) return false;

            // Native radio / checkbox with visible custom wrapper.
            // BUGFIX: also accept a visible parent <label> — very common
            // pattern (<label><input hidden>Text</label>) used to be
            // dropped entirely, losing whole radio/checkbox options.
            if (
                el.type === "radio" ||
                el.type === "checkbox"
            ) {

                const wrapper = el.closest(
                    ".custom-control, label"
                );

                return wrapper
                    ? isVisible(wrapper)
                    : isVisible(el);

            }

            if (isVisible(el)) return true;

            // Hidden native select with visible Select2

            if (el.tagName === "SELECT") {

                const container = getContainer(el);

                return !!getSelect2Widget(
                    el,
                    container
                );

            }

            return false;

        });


        const fields = [];

        const processed = new Set();


        // ==========================================
        // 10. NATIVE FIELD EXTRACTION
        // ==========================================

        elements.forEach(el => {

            if (processed.has(el)) return;

            const container = getContainer(el);

            const tag = el.tagName.toLowerCase();

            const nativeInputType =
                tag === "input"
                    ? (el.getAttribute("type") || "text").toLowerCase()
                    : null;

            const type =
                el.getAttribute("role") === "combobox" ||
                el.getAttribute("aria-haspopup") === "listbox"
                    ? "combobox"
                    : (tag === "input" ? nativeInputType : tag);


            // --------------------------------------
            // RADIO / CHECKBOX GROUP
            // --------------------------------------

            if (
                type === "radio" ||
                type === "checkbox"
            ) {

                const name = el.name;

                const questionContainer =
                    getQuestionContainer(el) ||
                    container;


                const group = elements.filter(other => {

                    if (
                        other.type !== type ||
                        other.name !== name
                    ) {
                        return false;
                    }

                    return (
                        (
                            getQuestionContainer(other) ||
                            getContainer(other)
                        ) === questionContainer
                    );

                });


                group.forEach(item =>
                    processed.add(item)
                );


                const label =
                    questionContainer?.querySelector(`
                        .question-label label,
                        .question-title,
                        legend,
                        .form-label
                    `);


                const questionText =
                    getText(label);


                const options = group.map(item => {

                    const optionLabel = item.id
                        ? document.querySelector(
                            `label[for="${escapeCSS(item.id)}"]`
                        )
                        : null;

                    return {

                        label:
                            getText(optionLabel) ||
                            item.getAttribute("aria-label") ||
                            getText(item.parentElement),

                        value: item.value,

                        selected: item.checked,

                        selector: getSelector(item)

                    };

                });


                fields.push({

                    label:
                        questionText ||
                        getLabel(el, questionContainer),

                    type: type,

                    name: name || null,

                    id: null,

                    selector: name
                        ? (
                            questionContainer &&
                            getContainerSelector(questionContainer)
                            ? (
                                `${getContainerSelector(questionContainer)} ` +
                                `input[name="${escapeCSS(name)}"]`
                            )
                            : `input[name="${escapeCSS(name)}"]`
                        )
                        : getSelector(el),

                    required: group.some(item =>
                        isRequired(item, questionContainer)
                    ),

                    value: null,

                    options: options

                });

                return;

            }


            // --------------------------------------
            // NORMAL INPUT / SELECT / TEXTAREA
            // --------------------------------------

            processed.add(el);


            let label = getLabel(
                el,
                container
            );

            // Oracle phone widgets expose the country-code picker as a
            // separate combobox. Keep it distinct from the actual phone input.
            const elementId = (el.id || "").toLowerCase();
            const elementName = (el.name || "").toLowerCase();
            if (
                elementId.includes("country-codes-dropdown") ||
                elementName.includes("countrycode")
            ) {
                label = "Phone Country Code";
            }


            // --------------------------------------
            // OPTIONS
            // --------------------------------------

            let options = [];

            if (tag === "select") {

                options = [...el.options].map(option => ({

                    text: option.text.trim(),

                    value: option.value,

                    selected: option.selected,

                    disabled: option.disabled

                }));

            }


            // --------------------------------------
            // SELECT2
            // --------------------------------------

            const select2Widget =
                tag === "select"
                ? getSelect2Widget(el, container)
                : null;


            const containerSelector =
                getContainerSelector(container);


            const widgetSelector = select2Widget
                ? getSelector(select2Widget) ||
                    (
                        containerSelector
                        ? `${containerSelector} .select2-selection`
                        : null
                    )
                : null;


            // --------------------------------------
            // HTML VALIDATION CONSTRAINTS
            // --------------------------------------

            const constraints = {

                max_length:
                    getNumberAttribute(el, "maxlength"),

                min_length:
                    getNumberAttribute(el, "minlength"),

                max:
                    getAttribute(el, "max"),

                min:
                    getAttribute(el, "min"),

                pattern:
                    getAttribute(el, "pattern"),

                step:
                    getAttribute(el, "step"),

                required:
                    isRequired(el, container),

                readonly:
                    !!el.readOnly,

                disabled:
                    !!el.disabled

            };


            // --------------------------------------
            // FIELD DATA
            // --------------------------------------

            fields.push({

                label: label,

                type: type,

                input_type: nativeInputType,

                tag: tag,

                autocomplete:
                    getAttribute(el, "autocomplete"),

                input_mode:
                    getAttribute(el, "inputmode"),

                multiple:
                    !!el.multiple,

                contenteditable:
                    el.getAttribute("contenteditable") === "true",

                role: getAttribute(el, "role"),

                aria_haspopup:
                    getAttribute(el, "aria-haspopup"),

                popup_selector: (() => {
                    const controlledId = getAttribute(el, "aria-controls");
                    return controlledId ? `#${escapeCSS(controlledId)}` : null;
                })(),

                name: el.name || null,

                id: el.id || null,

                placeholder:
                    getAttribute(el, "placeholder"),

                aria_label:
                    getAttribute(el, "aria-label"),

                required:
                    constraints.required,

                value: el.value ?? null,

                options: options,

                selector: getFieldSelector(
                    el,
                    container
                ),

                container_selector:
                    containerSelector,

                widget_selector:
                    widgetSelector,

                is_custom_select:
                    !!select2Widget ||
                    type === "combobox" ||
                    el.matches("[role='combobox'], [aria-haspopup='listbox']"),

                control_visible:
                    isVisible(el) ||
                    !!select2Widget,

                constraints:
                    constraints

            });

        });


        // ==========================================
        // 11. CUSTOM RADIO / CHECKBOX
        // ==========================================

        const customControls = [
            ...document.querySelectorAll(`
                [role="radio"],
                [role="checkbox"]
            `)
        ].filter(el => {

            if (el.matches("input, button")) {
                return false;
            }

            return isVisible(el);

        });


        const customGroups = new Map();


        customControls.forEach(el => {

            const container = getContainer(el);

            const role =
                el.getAttribute("role");

            const containerSelector =
                getContainerSelector(container);


            const key =
                role + "_" +
                (
                    containerSelector ||
                    container?.id ||
                    customControls.indexOf(el)
                );


            if (!customGroups.has(key)) {

                customGroups.set(key, {

                    container: container,

                    role: role,

                    options: []

                });

            }


            customGroups.get(key).options.push({

                label:
                    el.getAttribute("aria-label") ||
                    getText(el),

                value:
                    el.getAttribute("data-value") ||
                    el.getAttribute("value"),

                selected:
                    el.getAttribute("aria-checked") === "true",

                selector: getSelector(el)

            });

        });


        customGroups.forEach(group => {

            const container = group.container;

            const labelledBy =
                container?.querySelector(
                    "[aria-labelledby]"
                )?.getAttribute("aria-labelledby");


            const questionLabel = labelledBy
                ? labelledBy
                    .split(/\\s+/)
                    .map(id => document.getElementById(id))
                    .filter(Boolean)
                    .map(getText)
                    .join(" ")
                : getLabel(container, container);


            fields.push({

                label: questionLabel,

                type: group.role,

                name: null,

                selector:
                    getContainerSelector(container),

                required: !!container?.querySelector(
                    '[aria-required="true"]'
                ),

                options: group.options

            });

        });


        // ==========================================
        // 12. BUTTON SELECTOR
        // ==========================================

        const getButtonSelector = el => {

            if (!el) return null;

            if (el.id) {
                return `#${escapeCSS(el.id)}`;
            }

            if (el.name) {
                return `${el.tagName.toLowerCase()}[name="${escapeCSS(el.name)}"]`;
            }

            const attributes = [
                "atm-id",
                "data-testid",
                "data-action",
                "data-id"
            ];

            for (const attr of attributes) {

                const value = el.getAttribute(attr);

                if (value) {
                    return `[${attr}="${escapeCSS(value)}"]`;
                }

            }

            const classes = [...el.classList];

            if (classes.length) {

                const selector =
                    el.tagName.toLowerCase() +
                    "." +
                    classes.map(escapeCSS).join(".");

                if (document.querySelectorAll(selector).length === 1) {
                    return selector;
                }

            }

            const text = getText(el) || el.value;

            if (text) {

                const tag = el.tagName.toLowerCase();

                const matches = [...document.querySelectorAll(tag)]
                    .filter(btn =>
                        isVisible(btn) &&
                        (getText(btn) || btn.value) === text
                    );

                if (matches.length === 1) {
                    // BUGFIX: escape quotes/backslashes — a button text
                    // containing " broke the :has-text() selector.
                    const safeText = text.replace(
                        /[\\"]/g,
                        "\\$&"
                    );
                    return `${tag}:has-text("${safeText}")`;
                }

            }

            return null;

        };


        // ==========================================
        // 13. BUTTON EXTRACTION
        // ==========================================

        const buttons = [
            ...document.querySelectorAll(`
                button,
                input[type="submit"],
                input[type="button"],
                input[type="reset"],
                a[role="button"],
                [role="button"]
            `)
        ]
        .filter(el => {

            return (
                isVisible(el) &&
                !el.disabled &&
                el.getAttribute("aria-disabled") !== "true"
            );

        })
        .map(el => {

            return {

                text:
                    getText(el) || el.value || "",

                type:
                    el.getAttribute("type") ||
                    el.getAttribute("role") ||
                    el.tagName.toLowerCase(),

                name:
                    el.name || null,

                id:
                    el.id || null,

                selector:
                    getButtonSelector(el),

                disabled:
                    el.disabled || false,

                aria_label:
                    el.getAttribute("aria-label")

            };

        });


        // ==========================================
        // 14. RESUME / CV UPLOAD EXTRACTION
        // ==========================================

        const resumeFileInput =
            document.querySelector('.resume-upload-wrapper input[type="file"]') ||
            document.querySelector('input[type="file"]');

        const resumeUploadWrapper =
            resumeFileInput?.closest(".resume-upload-wrapper") ||
            resumeFileInput?.parentElement ||
            document.querySelector(".resume-section");

        const resumeUploadButton =
            resumeUploadWrapper?.querySelector(
                'button[atm-id="resume-button"], button.upload-resume-btn'
            ) ||
            document.querySelector(
                'button[atm-id="resume-button"], button.upload-resume-btn'
            );

        const resumeSectionText =
            getText(document.querySelector(".resume-section")) ||
            getText(resumeUploadWrapper);

        const acceptedFileTypes = ["DOC", "DOCX", "HTML", "PDF", "TXT"]
            .filter(extension =>
                new RegExp("\\\\b" + extension + "\\\\b", "i")
                    .test(resumeSectionText)
            );

        const maxSizeMatch =
            resumeSectionText.match(/(\\d+(?:\\.\\d+)?)\\s*(MB|KB)/i);

        const resumeMetadataIds = [
            "resumePath",
            "resumeName",
            "resumeFileSize",
            "resumeBucketId",
            "resumeRelativePath",
            "isResume"
        ];

        const resumeMetadata = {};
        resumeMetadataIds.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                resumeMetadata[id] = {
                    selector: `#${escapeCSS(id)}`,
                    value: input.value || null
                };
            }
        });

        const resumeUpload = {
            available: !!resumeFileInput,
            section_found: !!document.querySelector(".resume-section"),
            label:
                getText(resumeUploadButton) ||
                (resumeFileInput ? "Resume / CV upload" : null),
            required:
                !!document.querySelector(
                    ".resume-header .resume-mandatory"
                ),
            file_input: resumeFileInput ? {
                // BUGFIX: bare 'input[type="file"]' matched the FIRST file
                // input on the page — with several file inputs (e.g. a
                // portfolio upload) the resume went to the wrong widget.
                // Prefer the real id/attr selector of this exact element.
                selector: resumeFileInput.id
                    ? `#${escapeCSS(resumeFileInput.id)}`
                    : (
                        getSelector(resumeFileInput) ||
                        'input[type="file"]'
                    ),
                type: resumeFileInput.type,
                visible: isVisible(resumeFileInput),
                accept_attribute: resumeFileInput.getAttribute("accept"),
                multiple: !!resumeFileInput.multiple,
                disabled: !!resumeFileInput.disabled
            } : null,
            upload_button: resumeUploadButton ? {
                selector: resumeUploadButton.id
                    ? `#${escapeCSS(resumeUploadButton.id)}`
                    : (
                        resumeUploadButton.getAttribute("atm-id")
                            ? `[atm-id="${escapeCSS(resumeUploadButton.getAttribute("atm-id"))}"]`
                            : "button.upload-resume-btn"
                    ),
                text: getText(resumeUploadButton),
                visible: isVisible(resumeUploadButton)
            } : null,
            accepted_file_types: acceptedFileTypes,
            max_file_size: maxSizeMatch ? {
                value: Number(maxSizeMatch[1]),
                unit: maxSizeMatch[2].toUpperCase()
            } : null,
            instructions: resumeSectionText || null,
            uploaded_file_metadata: resumeMetadata,
            upload_state: (
                resumeMetadata.resumeName?.value ||
                resumeMetadata.resumePath?.value ||
                resumeMetadata.resumeRelativePath?.value
            ) ? "metadata_present" : "not_detected"
        };


        // ==========================================
        // 15. RETURN RAW SCRAPED SNAPSHOT
        // ==========================================

        return {
            has_form: !!form,
            form_action: form?.getAttribute("action") || null,
            form_method: form?.getAttribute("method") || null,
            page_title: document.title,
            page_url: location.href,
            resume_upload: resumeUpload,
            raw_fields: fields,
            buttons: buttons,
            counts: {
                forms: forms.length,
                native_fields: elements.length,
                custom_controls: customControls.length,
                file_inputs: document.querySelectorAll('input[type="file"]').length
            }
        };

    }
    """)

    return scraped_data