
SCRAPE_JS = r"""
() => {

    // 1. Visibility
    const isVisible = el => {
        const style = getComputedStyle(el);
        return (
            style.display !== "none" &&
            style.visibility !== "hidden" &&
            Number(style.opacity) > 0 &&
            el.getClientRects().length > 0 &&
            !el.closest('[hidden], [aria-hidden="true"]')
        );
    };

    // 2. Clean text
    const getText = el =>
        el?.innerText?.replace(/\s+/g, ' ').trim() || null;

    // 2b. Strip HTML tags (used for JSON-LD descriptions, which are HTML strings)
    const stripHtml = html =>
        html
            .replace(/<style[\s\S]*?<\/style>/gi, ' ')
            .replace(/<script[\s\S]*?<\/script>/gi, ' ')
            .replace(/<[^>]+>/g, ' ')
            .replace(/&nbsp;/g, ' ')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/\s+/g, ' ')
            .trim();

    // 3. Identify main content
    const candidates = Array.from(
        document.querySelectorAll(
            'main, article, [role="main"], [role="article"], [itemtype*="JobPosting"]'
        )
    ).filter(isVisible);

    const main = candidates.sort(
        (a, b) =>
            (getText(b)?.length || 0) -
            (getText(a)?.length || 0)
    )[0] || document.body;

    // 8. Selector generation
    const getSelector = el => {
        if (el.id)
            return `#${CSS.escape(el.id)}`;

        for (const attr of [
            'data-testid',
            'data-test',
            'data-automation-id',
            'data-qa'
        ]) {
            const value = el.getAttribute(attr);
            if (value)
                return `[${attr}="${CSS.escape(value)}"]`;
        }

        const parts = [];
        while (el && el.nodeType === 1) {
            let part = el.tagName.toLowerCase();

            if (el.id) {
                parts.unshift('#' + CSS.escape(el.id));
                break;
            }

            const parent = el.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(
                    child => child.tagName === el.tagName
                );
                if (siblings.length > 1) {
                    part += `:nth-of-type(${siblings.indexOf(el) + 1})`;
                }
            }

            parts.unshift(part);
            el = parent;
        }
        return parts.join(' > ');
    };

    // 9. Visible clickable elements extraction
    //    FIX-5: also capture input[type="button"], not just submit.
    const raw_actions = Array.from(
        document.querySelectorAll(
            'a[href], button, input[type="submit"], input[type="button"], [role="button"]'
        )
    )
    .filter(isVisible)
    .map(el => {
        const text = [
            getText(el),
            el.getAttribute('aria-label'),
            el.getAttribute('title'),
            el.value
        ]
        .filter(Boolean)
        .join(' ')
        .trim();

        const rect = el.getBoundingClientRect();

        return {
            text,
            tag: el.tagName.toLowerCase(),
            selector: getSelector(el),
            url: el.tagName === 'A' ? el.href : null,
            id: el.id || null,
            aria_label: el.getAttribute('aria-label'),
            // FIX-5: respect aria-disabled as well as the disabled property
            enabled: !el.disabled && el.getAttribute('aria-disabled') !== 'true',
            location: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        };
    });
    // NOTE: no text-length filter here — FIX-8 relies on seeing icon-only
    // anchors (empty text, apply href); text matching happens in parse().

    // 11. FIX-4: JSON-LD JobPosting extraction (structured, most reliable source)
    const jsonld_postings = [];
    document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
        let parsed;
        try {
            parsed = JSON.parse(s.textContent);
        } catch (e) {
            return; // malformed JSON-LD — skip silently
        }

        const nodes = Array.isArray(parsed)
            ? parsed
            : (parsed && parsed['@graph']) || [parsed];

        nodes.forEach(n => {
            const t = n && n['@type'];
            const isJob =
                t === 'JobPosting' ||
                (Array.isArray(t) && t.includes('JobPosting'));
            if (!isJob) return;

            let location = null;
            const jl = Array.isArray(n.jobLocation) ? n.jobLocation[0] : n.jobLocation;
            if (jl && jl.address) {
                const a = jl.address;
                location = [a.addressLocality, a.addressRegion, a.addressCountry]
                    .filter(Boolean).join(', ') || null;
            }

            const org = n.hiringOrganization || {};

            jsonld_postings.push({
                title: n.title || null,
                organization: org.name || null,
                date_posted: n.datePosted || null,
                valid_through: n.validThrough || null,
                employment_type: Array.isArray(n.employmentType)
                    ? n.employmentType.join(', ')
                    : (n.employmentType || null),
                location,
                apply_url: n.url || org.sameAs || null,
                description: n.description ? stripHtml(String(n.description)).slice(0, 8000) : null
            });
        });
    });

    // 10. Output
    return {
        page_title: document.title,
        page_url: location.href,
        captured_at: new Date().toISOString(),   // FIX-3
        main_html: main.innerHTML,
        raw_actions,
        jsonld_postings                          // FIX-4
    };
}
"""




def jd_scrap(page):
    """Raw capture: main-content HTML, visible actions, JSON-LD JobPostings.

    Raises PlaywrightError if the page is unavailable (navigated away,
    crashed, CSP-locked evaluate, etc.).
    """
    raw_data = page.evaluate(SCRAPE_JS)

    # FIX-7: basic sanity guard on the capture itself
    if not raw_data or not raw_data.get("main_html"):
        raise ValueError(
            f"scrape(): empty capture from {page.url!r} "
            "(page may still be loading or is a shell document)"
        )
    return raw_data