import ollama
import json


def check_eligibility(web_data, resume_data, candidate_profile,logger):

    prompt = f"""
You are an intelligent Job Eligibility Checker.

Your task is to determine whether a candidate is eligible
for a given job based on the provided information.

INPUT DATA:
1. Website Data: Contains job details and eligibility criteria.
2. Resume Data: Contains candidate's qualifications, skills and experience.
3. Candidate Profile: Contains additional candidate information.

RULES:

1. Identify all mandatory and preferred criteria separately
   from website data.

2. Compare those criteria with the resume and candidate profile.

3. Consider educational qualifications, experience,
   required skills and other job requirements.

4. Never invent, assume or fabricate candidate information.

5. STRICT ELIGIBILITY RULE:
   Return eligible = false ONLY when the candidate
   violates an explicitly mandatory requirement.

6. Educational qualification:
   If the job explicitly requires a specific degree,
   such as MA, and the candidate has B.Tech instead,
   return eligible = false only if MA is mandatory
   and equivalent qualifications are not accepted.

7. If a requirement is preferred, desirable,
   or good-to-have, its absence must NOT cause rejection.

8. Missing preferred skills must not affect eligibility.

9. If a mandatory requirement cannot be verified
   because information is missing, mention it in reason.
   Do not automatically reject unless the job explicitly
   requires that information to be provided.

10. Calculate matching_score (0-100) based on overall
    alignment between candidate qualifications, skills,
    experience and job requirements.

11. The matching_score must consider both mandatory
    and preferred requirements.

12. Return a concise and accurate reason.

OUTPUT FORMAT:
Return ONLY a valid JSON object:

{{
    "eligible": true,
    "reason": "Candidate satisfies all mandatory eligibility criteria.",
    "matching_score": 85
}}

WEBSITE DATA:
{web_data}

RESUME DATA:
{resume_data}

CANDIDATE PROFILE:
{candidate_profile}
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

        local_result = response["message"]["content"]

        if not local_result:
            raise Exception("Empty Ollama response")

        # ==========================================
        # 1. PARSE JSON RESPONSE
        # ==========================================

        result = json.loads(local_result)

        # ==========================================
        # 2. VALIDATE RESPONSE
        # ==========================================

        if not isinstance(result.get("eligible"), bool):
            raise ValueError("Invalid eligibility value")

        if not isinstance(result.get("reason"), str):
            raise ValueError("Invalid eligibility reason")

        if not isinstance(result.get("matching_score"), (int, float)):
            raise ValueError("Invalid matching score")

        print("Successful local model: phi4-mini:3.8b-q4_K_M")

        # ==========================================
        # 3. ELIGIBILITY DECISION
        # ==========================================
        if result["eligible"] == False:

            logger.info("\nYou are not eligible.")
            logger.info(f"Due to: {result['reason']}")
            logger.info(f"Matching Score: {result['matching_score']}")

            logger.info("Eligibility checking is done successfully.")
            logger.info("Application submission decision is dropping out.")

            return None

        # ==========================================
        # 4. ELIGIBLE CANDIDATE
        # ==========================================
        logger.info("\nYou are eligible.")
        logger.info(f"Due to: {result['reason']}")
        logger.info(f"Matching Score: {result['matching_score']}")        

    except Exception as e:

        raise Exception(
            f"Local AI eligibility checking failed: {e}"
        )