import requests

from credential import JobMatcherCredential
from job_matching.job_matching_models import UserProfile, JobMatchingResponse
from logger_utils import create_logger

logger = create_logger("Job Matcher")


def match(job_description: str, user_profile: UserProfile) -> float:
    """
    Call the external job-matching service and return a similarity score (0.0–1.0).
    Raises on HTTP errors so the caller can handle failures gracefully.
    """
    token = JobMatcherCredential.get_token()
    url = JobMatcherCredential.get_url()
    payload = {
        "modelId": JobMatcherCredential.get_judge_model(),
        "extractionPipeline": {
            "extractorModelIds": JobMatcherCredential.get_extractor_model(),
            "judgeModelId": JobMatcherCredential.get_judge_model(),
        },
        "inputText": job_description,
        "userProfile": user_profile.model_dump(),
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    logger.info(f"Matching job description (first 15 chars): {job_description[:15]!r}")
    response = requests.post(url, json=payload, headers=headers, timeout=240)
    response.raise_for_status()
    data = JobMatchingResponse.model_validate(response.json())
    score = data.similarityScore.score
    logger.info(f"Received matching score: {score:.2f}")
    return score
