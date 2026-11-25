# def parse_web(page):
#     web_data = page.evaluate("""

#     () => {

#         // 1. Visibility
#         const isVisible = el => {

#             const style = getComputedStyle(el);

#             return (
#                 style.display !== "none" &&
#                 style.visibility !== "hidden" &&
#                 Number(style.opacity) > 0 &&
#                 el.getClientRects().length > 0 &&
#                 !el.closest('[hidden], [aria-hidden="true"]')
#             );
#         };


#         // 2. Clean text
#         const getText = el =>
#             el?.innerText?.replace(/\\s+/g, ' ').trim() || null;


#         // 3. Identify main content
#         const candidates = Array.from(
#             document.querySelectorAll(
#                 'main, article, [role="main"], [role="article"], [itemtype*="JobPosting"]'
#             )
#         ).filter(isVisible);


#         const main = candidates.sort(
#             (a, b) =>
#                 (getText(b)?.length || 0) -
#                 (getText(a)?.length || 0)
#         )[0] || document.body;


#         // 4. Content extraction
#         const clone = main.cloneNode(true);


#         // Remove non-content elements
#         clone.querySelectorAll([
#             'script',
#             'style',
#             'noscript',
#             'svg',
#             'iframe',
#             'canvas',
#             'nav',
#             'footer',
#             'form',
#             'input',
#             'select',
#             'textarea',
#             'button',
#             '[role="navigation"]',
#             '[role="dialog"]',
#             '[aria-hidden="true"]',
#             '[hidden]'
#         ].join(',')).forEach(el => el.remove());


#         // 5. Semantic content filtering

#         const irrelevantPatterns = [
#             /^skip to (main )?content$/i,
#             /^back to top$/i,
#             /^home$/i,
#             /^search jobs$/i,
#             /^sign in$/i,
#             /^log in$/i,
#             /^register$/i,
#             /^subscribe$/i,
#             /^download our app$/i,
#             /^follow us$/i,
#             /^join us on/i,
#             /^privacy policy$/i,
#             /^terms (of use|and conditions)$/i,
#             /^cookie policy$/i
#         ];


#         // Remove irrelevant standalone elements
#         clone.querySelectorAll(
#             'p, li, h1, h2, h3, h4, h5, h6, a'
#         ).forEach(el => {

#             const text = getText(el);

#             if (!text) return;

#             if (
#                 irrelevantPatterns.some(pattern =>
#                     pattern.test(text)
#                 )
#             ) {
#                 el.remove();
#             }

#         });


#         // 6. Remove duplicate text blocks

#         const seen = new Set();

#         clone.querySelectorAll(
#             'h1,h2,h3,h4,h5,h6,p,li'
#         ).forEach(el => {

#             const text = getText(el);

#             if (!text) return;

#             const normalized = text.toLowerCase();

#             if (seen.has(normalized)) {
#                 el.remove();
#             } else {
#                 seen.add(normalized);
#             }

#         });


#         // 7. Final job content
#         const job_content = clone.innerText
#             .replace(/[ \\t]+/g, ' ')
#             .replace(/\\n{3,}/g, '\\n\\n')
#             .trim();


#         // 8. Selector generation
#         const getSelector = el => {

#             if (el.id)
#                 return `#${CSS.escape(el.id)}`;

#             for (const attr of [
#                 'data-testid',
#                 'data-test',
#                 'data-automation-id',
#                 'data-qa'
#             ]) {

#                 const value = el.getAttribute(attr);

#                 if (value)
#                     return `[${attr}="${CSS.escape(value)}"]`;
#             }

#             const parts = [];

#             while (el && el.nodeType === 1) {

#                 let part = el.tagName.toLowerCase();

#                 if (el.id) {
#                     parts.unshift('#' + CSS.escape(el.id));
#                     break;
#                 }

#                 const parent = el.parentElement;

#                 if (parent) {

#                     const siblings = Array.from(
#                         parent.children
#                     ).filter(
#                         child => child.tagName === el.tagName
#                     );

#                     if (siblings.length > 1) {
#                         part += `:nth-of-type(${siblings.indexOf(el) + 1})`;
#                     }
#                 }

#                 parts.unshift(part);

#                 el = parent;
#             }

#             return parts.join(' > ');
#         };


#         // 9. Apply button detection

#         const apply_actions = Array.from(
#             document.querySelectorAll(
#                 'a[href], button, input[type="submit"], [role="button"]'
#             )
#         )
#         .filter(isVisible)
#         .map(el => {

#             const text = [
#                 getText(el),
#                 el.getAttribute('aria-label'),
#                 el.getAttribute('title'),
#                 el.value
#             ]
#             .filter(Boolean)
#             .join(' ')
#             .trim();

#             return {el, text};

#         })
#         .filter(({text}) => {

#             return /\\bapply\\b|\\beasy apply\\b|\\bapply now\\b|\\bstart application\\b/i
#                 .test(text);

#         })
#         .map(({el, text}) => {

#             const rect = el.getBoundingClientRect();

#             return {

#                 text,

#                 tag: el.tagName.toLowerCase(),

#                 selector: getSelector(el),

#                 url: el.tagName === 'A'
#                     ? el.href
#                     : null,

#                 id: el.id || null,

#                 aria_label: el.getAttribute('aria-label'),

#                 enabled: !el.disabled,

#                 location: {
#                     x: Math.round(rect.x),
#                     y: Math.round(rect.y),
#                     width: Math.round(rect.width),
#                     height: Math.round(rect.height)
#                 }

#             };

#         });


#         // 10. Output

#         return {

#             page_title: document.title,

#             page_url: location.href,

#             job_content,

#             apply_actions

#         };

#     }

#     """)

#     return web_data






PARSE_JS = r"""
(data) => {

    // Clean text helper.
    // FIX-1: helpers now run on ATTACHED clones (see staging below), so
    // innerText is layout-aware again (newlines + hidden-text filtering).
    const getText = el =>
        el?.innerText?.replace(/\s+/g, ' ').trim() || null;

    const MIN_CONTENT_CHARS = 150;

    // FIX-2: cleaning is parameterised so we can retry with <form> kept.
    const buildClone = (removeForms) => {
        const c = document.createElement('div');
        c.innerHTML = data.main_html;

        const removals = [
            'script',
            'style',
            'noscript',
            'svg',
            'iframe',
            'canvas',
            'nav',
            'footer',
            'input',
            'select',
            'textarea',
            'button',
            '[role="navigation"]',
            '[role="dialog"]',
            '[aria-hidden="true"]',
            '[hidden]'
        ];
        if (removeForms) removals.push('form');

        c.querySelectorAll(removals.join(',')).forEach(el => el.remove());
        return c;
    };

    const irrelevantPatterns = [
        /^skip to (main )?content$/i,
        /^back to top$/i,
        /^home$/i,
        /^search jobs$/i,
        /^sign in$/i,
        /^log in$/i,
        /^register$/i,
        /^subscribe$/i,
        /^download our app$/i,
        /^follow us$/i,
        /^join us on/i,
        /^privacy policy$/i,
        /^terms (of use|and conditions)$/i,
        /^cookie policy$/i
    ];

    // 5. Semantic content filtering
    const filterIrrelevant = clone => {
        clone.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6, a').forEach(el => {
            const text = getText(el);
            if (!text) return;
            if (irrelevantPatterns.some(pattern => pattern.test(text))) {
                el.remove();
            }
        });
    };

    // 6. Remove duplicate text blocks
    const dedupBlocks = clone => {
        const seen = new Set();
        clone.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li').forEach(el => {
            const text = getText(el);
            if (!text) return;
            const normalized = text.toLowerCase();
            if (seen.has(normalized)) {
                el.remove();
            } else {
                seen.add(normalized);
            }
        });
    };

    // FIX-1: off-screen staging container. Children keep their classes, so
    // CSS rules (display:none etc.) still apply to them — innerText is now
    // computed by a real layout pass instead of falling back to textContent.
    const stage = document.createElement('div');
    stage.style.cssText =
        'position:absolute; left:-99999px; top:0; width:900px; margin:0; padding:0;';
    document.body.appendChild(stage);

    const extractText = clone => {
        stage.appendChild(clone);
        const text = clone.innerText
            .replace(/[ \t]+/g, ' ')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
        clone.remove();
        return text;
    };

    let job_content;

    // FIX-2: pass 1 — remove forms (previous behaviour).
    const cloneA = buildClone(true);
    filterIrrelevant(cloneA);
    dedupBlocks(cloneA);
    const textA = extractText(cloneA);

    if (textA.length >= MIN_CONTENT_CHARS) {
        job_content = textA;
    } else {
        // FIX-2: pass 2 — job description probably lives inside/next to a
        // <form>; retry keeping it (interactive controls are still stripped).
        const cloneB = buildClone(false);
        filterIrrelevant(cloneB);
        dedupBlocks(cloneB);
        const textB = extractText(cloneB);

        job_content = textB.length > textA.length ? textB : textA;
        if (textB.length > textA.length) {
            var used_form_fallback = true;
        }
    }

    stage.remove(); // FIX-1: always clean up the staging container

    // 9. FIX-6: Apply button filtering, with false-positive guard.
    const APPLY_RE =
        /\bapply\b|\bapply now\b|\beasy apply\b|\bstart application\b/i;

    // "How to apply", "Ways to apply" etc. are informational links, not CTAs.
    const FALSE_POS_RE =
        /^(how\s+to\s+apply|ways\s+to\s+apply|learn\s+how\s+to\s+apply)/i;

    // FIX-8 (found during live testing): some ATS buttons are icon-only
    // anchors with EMPTY text but an unambiguous apply href
    // (e.g. Lever: <a class="postings-btn" href=".../apply"></a>).
    // Match those by URL so they are not lost.
    const APPLY_HREF_RE = /\/apply([\/?#]|$)/i;

    const apply_actions = (data.raw_actions || []).filter(({ text, url }) => {
        const t = (text || '').trim();
        if (APPLY_RE.test(t) && !FALSE_POS_RE.test(t)) return true;
        return !!url && APPLY_HREF_RE.test(url);
    });

    // 10. Output
    return {
        page_title: data.page_title,
        page_url: data.page_url,
        captured_at: data.captured_at,
        // FIX-3: caller can detect that the page changed between scrape & parse
        page_moved: data.page_url !== location.href,
        used_form_fallback: !!used_form_fallback,
        job_content,
        jsonld_postings: data.jsonld_postings || [],
        apply_actions
    };
}
"""





def jd_parse(page, raw_data):
    """Clean + structure the raw capture into job content and apply actions.

    Raises ValueError on invalid input, PlaywrightError if evaluate fails.
    """
    # FIX-7: validate input before touching the browser
    if not raw_data or not raw_data.get("main_html"):
        raise ValueError("parse(): raw_data is missing or has no main_html")

    web_data = page.evaluate(PARSE_JS, raw_data)
    return web_data


