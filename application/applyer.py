
# # ==========================================
# # 7. MAIN APPLICATION FLOW (P0-1..P0-5 fixed loop)
# # ==========================================
# from application.app_scraper import app_scrap
# from application.app_parser import app_parse
# from application.rule_maper import rule_map
# from application.ai_mapper import ai_map
# from application.filler import fill
# from application.app_utility import pick_visible_button,click_next_button,merge

# def run_application_flow(page, resume_data, candidate_profile,logger,resume_path=None, max_pages=15):
#     for page_no in range(1, max_pages + 1):
#         logger.info("=========== PAGE %d/%d ===========", page_no, max_pages)
#         try:
#             # ------------------------------------
#             # 1. SCRAPE + PARSE
#             # ------------------------------------
#             scraped_output = app_scrap(page)
#             parsed_output = app_parse(scraped_output)
#             logger.info("Page %d scraped+parsed.", page_no)

#             if not parsed_output.get("form_found") and not (
#                 parsed_output["buttons"]["next"]
#                 or parsed_output["buttons"]["submit"]
#             ):
#                 input(
#                     "Is page par form ya Next/Submit button nahi mila. "
#                     "Manually check karke Enter dabao (abort: Ctrl+C)..."
#                 )
#                 continue

#             # ------------------------------------
#             # 2. FIELD MATCHING  (P0-1: ruled_output use hota hai)
#             # ------------------------------------
#             ruled_output,remaining_parsed_output = rule_map(
#                 parsed_output["fields"],
#                 resume_data,
#                 candidate_profile
#             )

#             ai_output=None
#             if remaining_parsed_output is not None:
#                 # P0-1: jo fields rule_map se match nahi hue, unhe
#                 # ai_map (Qwen) se match karne ke liye bhejo. Pehle yahan
#                 # galti se rule_map dobara call ho raha tha — uska return
#                 # tuple hota hai, aur merge() uspe .get() karke crash karta tha.
#                 ai_output = ai_map(
#                     remaining_parsed_output,
#                     resume_data,
#                     candidate_profile
#                 )
#             mapped_output=merge(ruled_output,ai_output)
#             logger.info("Matching completed.")

#             # ------------------------------------
#             # 3. AUTOFILL (P1-7: resume sirf tab jab widget available ho)
#             # ------------------------------------
#             resume_available = bool(
#                 (parsed_output.get("resume_upload") or {}).get("available")
#             )
#             status=fill(
#                 page,
#                 mapped_output,
#                 resume_path if resume_available else None
#             )
#             logger.info("Auto filling done.")

#             # ------------------------------------
#             # 4. FINAL APPLICATION PAGE
#             # (P0-2: parsed["buttons"]["submit"] — purani
#             #  "submit_button" key exist hi nahi karti thi)
#             # ------------------------------------
#             if parsed_output["buttons"]["submit"]:
#                 input(
#                     "Final application page detected. "
#                     "Review everything and submit manually. "
#                     "Press Enter after completion..."
#                 )
#                 logger.info(
#                     "Application workflow finished (final review by user)."
#                 )
#                 return True

#             # ------------------------------------
#             # 5. MANDATORY FIELD STATUS
#             # (P0-2: status ruled_output se; P0-5: 0/1/2 sab live hain)
#             # ------------------------------------
#             # STATUS 0: required data-fields missing
#             if status == 0:
#                 input(
#                     "Some mandatory fields are missing values. "
#                     "Complete remaining fields and click Next manually. "
#                     "Press Enter after navigation..."
#                 )
#                 continue

#             # STATUS 2: manual/declarative questions bache hain
#             if status == 2:
#                 input(
#                     "Kuch questions aapke manual answers chahte hain "
#                     "(declarations/eligibility/radio). Answer karke "
#                     "Next dabao. Press Enter after navigation..."
#                 )
#                 continue

#             if status != 1:
#                 logger.error(
#                     "Unknown mandatory status: %r — stopping workflow.",
#                     status,
#                 )
#                 return False

#             # STATUS 1: sab theek -> auto Next
#             # (P0-3: list se visible+enabled button pick hota hai;
#             #  P2-16 ke baad bhi koi redundant double-verification nahi —
#             #  click_next_button khud transition confirm karta hai)
#             next_button = pick_visible_button(
#                 page, parsed_output["buttons"]["next"]
#             )

#             if not next_button:
#                 input(
#                     "Next button not found/visible. "
#                     "Handle manually and press Enter..."
#                 )
#                 continue

#             if not click_next_button(page, next_button,logger):
#                 input(
#                     "Navigation could not be confirmed. "
#                     "Handle manually and press Enter..."
#                 )
#                 continue

#             # Transition confirm ho chuka hai; thoda settle time
#             page.wait_for_timeout(1500)

#         except KeyboardInterrupt:
#             raise
#         except Exception as exc:
#             logger.exception("Page %d pe error: %s", page_no, exc)
#             input(
#                 "Error aa gaya. Manually handle karke Enter dabao "
#                 "(continue) ya Ctrl+C (abort)..."
#             )
#             continue

#     logger.warning(
#         "MAX_PAGES (%d) reach ho gaya — safety ke liye flow rok diya.",
#         max_pages,
#     )



#==========================================
# 7. MAIN APPLICATION FLOW (P0-1..P0-5 fixed loop)
# ==========================================
from application.app_scraper import app_scrap
from application.app_parser import app_parse
from application.rule_maper import rule_map
from application.ai_mapper import ai_map
from application.filler import fill
from application.app_utility import pick_visible_button,click_next_button,merge

def run_application_flow(page, resume_data, candidate_profile,logger,resume_path=None, max_pages=15):
    for page_no in range(1, max_pages + 1):
        logger.info("=========== PAGE %d/%d ===========", page_no, max_pages)
        try:
            # ------------------------------------
            # 1. SCRAPE + PARSE
            # ------------------------------------
            scraped_output = app_scrap(page)
            parsed_output = app_parse(scraped_output)
            logger.info("Page %d scraped+parsed.", page_no)

            if not parsed_output.get("form_found") and not (
                parsed_output["buttons"]["next"]
                or parsed_output["buttons"]["submit"]
            ):
                input(
                    "Is page par form ya Next/Submit button nahi mila. "
                    "Manually check karke Enter dabao (abort: Ctrl+C)..."
                )
                continue

            # ------------------------------------
            # 2. FIELD MATCHING  (P0-1: ruled_output use hota hai)
            # ------------------------------------
            ruled_output,remaining_parsed_output = rule_map(
                parsed_output["fields"],
                resume_data,
                candidate_profile
            )

            ai_output=None
            if remaining_parsed_output is not None:
                # P0-1: jo fields rule_map se match nahi hue, unhe
                # ai_map (Qwen) se match karne ke liye bhejo. Pehle yahan
                # galti se rule_map dobara call ho raha tha — uska return
                # tuple hota hai, aur merge() uspe .get() karke crash karta tha.
                ai_output = ai_map(
                    remaining_parsed_output,
                    resume_data,
                    candidate_profile
                )
            mapped_output=merge(ruled_output,ai_output)
            logger.info("Matching completed.")

            # ------------------------------------
            # 3. AUTOFILL (P1-7: resume sirf tab jab widget available ho)
            # ------------------------------------
            resume_available = bool(
                (parsed_output.get("resume_upload") or {}).get("available")
            )
            status=fill(
                page,
                mapped_output,
                resume_path if resume_available else None
            )
            logger.info("Auto filling done.")

            # ------------------------------------
            # 4. FINAL APPLICATION PAGE
            # (P0-2: parsed["buttons"]["submit"] — purani
            #  "submit_button" key exist hi nahi karti thi)
            # ------------------------------------
            if parsed_output["buttons"]["submit"]:
                input(
                    "Final application page detected. "
                    "Review everything and submit manually. "
                    "Press Enter after completion..."
                )
                logger.info(
                    "Application workflow finished (final review by user)."
                )
                return True

            # ------------------------------------
            # 5. MANDATORY FIELD STATUS
            # (P0-2: status ruled_output se; P0-5: 0/1/2 sab live hain)
            # ------------------------------------
            # STATUS 0: required data-fields missing
            if status == 0:
                input(
                    "Some mandatory fields are missing values. "
                    "Complete remaining fields and click Next manually. "
                    "Press Enter after navigation..."
                )
                continue

            # STATUS 2: manual/declarative questions bache hain
            if status == 2:
                input(
                    "Kuch questions aapke manual answers chahte hain "
                    "(declarations/eligibility/radio). Answer karke "
                    "Next dabao. Press Enter after navigation..."
                )
                continue

            if status != 1:
                logger.error(
                    "Unknown mandatory status: %r — stopping workflow.",
                    status,
                )
                return False

            # STATUS 1: sab theek -> auto Next
            # (P0-3: list se visible+enabled button pick hota hai;
            #  P2-16 ke baad bhi koi redundant double-verification nahi —
            #  click_next_button khud transition confirm karta hai)
            next_button = pick_visible_button(
                page, parsed_output["buttons"]["next"]
            )

            if not next_button:
                input(
                    "Next button not found/visible. "
                    "Handle manually and press Enter..."
                )
                continue

            if not click_next_button(page, next_button,logger):
                input(
                    "Navigation could not be confirmed. "
                    "Handle manually and press Enter..."
                )
                continue

            # Transition confirm ho chuka hai; thoda settle time
            page.wait_for_timeout(1500)

        except KeyboardInterrupt:
            raise
        except Exception as exc:
            logger.exception("Page %d pe error: %s", page_no, exc)
            input(
                "Error aa gaya. Manually handle karke Enter dabao "
                "(continue) ya Ctrl+C (abort)..."
            )
            continue

    logger.warning(
        "MAX_PAGES (%d) reach ho gaya — safety ke liye flow rok diya.",
        max_pages,
    )

    # BUGFIX: explicit False — pehle implicit None return hota tha,
    # jo truthiness me False jaisa hai par debug me confusing hai.
    return False




