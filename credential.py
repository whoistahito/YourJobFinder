import os

class JobMatcherCredential:
    @staticmethod
    def get_url():
        return os.environ.get("job_matcher_url")

    @staticmethod
    def get_token():
        return os.environ.get("job_matcher_token")

    @staticmethod
    def get_extractor_model():
        return os.environ.get("extractor_model")

    @staticmethod
    def get_judge_model():
        return os.environ.get("judge_model")


class GoogleScraperCredential:
    @staticmethod
    def get_google_scraper_url():
        return os.environ.get("google_scraper_url")
    @staticmethod
    def get_google_scraper_token():
        return os.environ.get("google_scraper_token")

class EmailCredential:
    @staticmethod
    def get_email_address():
        return os.environ.get("email_address")

    @staticmethod
    def get_email_password():
        return os.environ.get("email_password")


class DatabaseCredential:
    @staticmethod
    def get_db_name():
        return os.environ.get("db_name")

    @staticmethod
    def get_db_password():
        return os.environ.get("db_password")

    @staticmethod
    def get_db_username():
        return os.environ.get("db_username")

    @staticmethod
    def get_db_host():
        return os.environ.get("db_host")

    @staticmethod
    def get_db_port():
        return os.environ.get("db_port")

    @staticmethod
    def get_db_uri():
        return os.environ.get(
            "db_url",
            "postgresql://%s:%s@%s:%s/%s" % (
                DatabaseCredential.get_db_username(),
                DatabaseCredential.get_db_password(),
                DatabaseCredential.get_db_host(),
                DatabaseCredential.get_db_port(),
                DatabaseCredential.get_db_name(),
            ),
        )