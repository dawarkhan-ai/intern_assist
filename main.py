from playwright.sync_api import sync_playwright
import json

import project_utility as pr_ut
from job_details import jd_scrap,jd_parse,check_eligibility
from application import click_apply_button
from application import run_application_flow

import logging
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
logger = logging.getLogger("autofill")

def main():
    try:      
        ##1. Setup
        print("=================Setup=================")
        #taking inputs
        url=input("Enter Application URL: ")
        logger.info(f"Url: {url}")
            
        with sync_playwright() as p:
            #opening site
            browser = p.chromium.launch(
                channel="chrome",
                headless=False
            )
            context = browser.new_context()
            page = context.new_page()
            page.goto(url)

            #scrap site
            raw_web_data=jd_scrap(page)
            logger.info("Raw web data is scrapped.")
            
            #parse site
            web_data=jd_parse(page,raw_web_data)
            logger.info("web data is parsed.")

            #fetching resume
            resume_path="user_config/temp_resume.json"
            resume_data=pr_ut.fetch_resume(resume_path)
            logger.info("Fetching resume is successfull.")

            #fetching candidate profile
            profile_path="user_config/candidate_profile.json"
            candidate_profile=pr_ut.fetch_candidate_profile(profile_path)
            logger.info("Fetching candidate profile is successfull.")

            ##2. Check eligibility
            print("===================Checking Eligibility===================")
            check_eligibility(
                json.dumps(web_data, indent=4),
                json.dumps(resume_data, indent=4),
                json.dumps(candidate_profile, indent=4),
                logger     
            )
            logger.info("Eligibility checking is done successfully.")


            print("===============Applying application form=====================")
            ##3. Applying
            #clicking apply button
            click_apply_button(page,web_data["apply_actions"])
            logger.info("apply button clicked.")

            resume_path="user_config/temp_resume.pdf"
            run_application_flow(page, resume_data, candidate_profile,logger, resume_path=None, max_pages=15)
            logger.info("Application submission is successfully done.")

            ##4. Resources cleanup
            context.close()

    except Exception as e:
        print("Exception caught:",e)
        return


main()
print("InternPilot AI completed 1 task.")



