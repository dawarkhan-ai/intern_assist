# intern_assist — Auto-Fill Job Application Tool

This tool opens a job/internship page, checks if you are eligible, and then
**fills the application form for you** using your saved profile and resume.

One important rule: **it never submits the application by itself.**
It fills the form, stops at the final Submit button, and lets you review
and click submit yourself.

---

## What it does (step by step)

1. You give it a job URL.
2. It reads the job page (title, description, Apply button).
3. It asks a local AI model (Ollama) to check: are you eligible for this job?
4. It clicks Apply and goes through each application page.
5. On every page, it fills the fields it can (name, email, phone, etc.)
   using your profile and resume data.
6. Fields it cannot fill safely (like "Are you legally authorized to work?")
   are listed for you to answer by hand.
7. It stops when it sees the Submit button. You do the final review.

**Works with:** Internshala, Lever, Greenhouse, Workday-style dropdowns,
Ashby, and most simple ATS forms.

---

## How the code is organized

```
main.py                  → starts everything, takes the URL
project_utility.py       → loads your config, profile, resume, logging

job_details/             → reads and understands the job post
  jd_scraper.py          → captures the page (HTML, buttons, links)
  jd_parser.py           → cleans the text, finds the real Apply button
  eligibility_checker.py → AI check: should you apply?

application/             → fills the form
  app_scraper.py         → finds all form fields on the page
  app_parser.py          → works out each field's type, options, rules
  rule_maper.py          → matches fields to your data (no AI needed)
  ai_mapper.py           → AI backup for fields the rules missed
  app_utility.py         → shared helpers (aliases, matching, buttons)
  filler.py              → types the values, verifies them, uploads resume
  applyer.py             → runs the page-by-page loop, pauses for you
```

---

## How to set it up

```bash
pip install -r requirements.txt        # playwright + ollama
playwright install chrome              # needs real Google Chrome
ollama pull phi4-mini:3.8b-q4_K_M      # the local AI model
```

Then edit the three files in `user_config/` (templates are already there):

| File | What to put in it |
|------|-------------------|
| `candidate_profile.json` | Your details: name, email, phone, education, answers to common questions |
| `temp_resume.json` | Your resume as JSON |
| `temp_resume.pdf` | Your real resume PDF (used for upload) |

Run it:

```bash
python main.py
# paste the job URL when it asks
```

When it pauses, it is asking you to fill something by hand. When it says
"Submit button detected", the form is ready for your final review.

---

## Things it cannot do (on purpose or by site limits)

- **Logins**: Internshala, Naukri, LinkedIn ask you to sign in to apply.
  The tool does not store your passwords.
- **Naukri anti-bot**: Naukri blocks automated browsers at the connection level.
- **Needs the AI model**: without Ollama running, the eligibility and AI-mapping
  steps will fail.
- **Hidden file boxes**: some sites hide the file-picker in a way browsers
  do not allow automation to use.
- **Some sites redraw the page**: a site like Lever may visually reset a
  filled field right after it is filled. That is the site's own behavior.

---

## Files in this pack

```
fixed_files/
├── main.py
├── project_utility.py
├── README.md        ← setup guide
├── requirements.txt ← playwright, ollama
├── FIXES.md         ← every fix in detail, with test proof
├── application/     ← 8 files for form filling
├── job_details/     ← 4 files for reading the job post
└── user_config/     ← your profile + resume templates
```

