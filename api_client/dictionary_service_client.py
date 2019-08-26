import requests
import urllib.parse
import logging
from api_client.security import Session

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s\t%(asctime)s\t%(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)


class DictionaryServiceClient(object):
    def __init__(self, session: Session, service_base_url):
        self.session = session
        self.service_base_url = service_base_url

    def import_file(self, file_management_file_id, job_name, overwrite=False):
        url_path = f'/dictionary/v1/import/{file_management_file_id}/jobs'
        url = urllib.parse.urljoin(self.service_base_url, url_path)

        params = {
            'jobname': job_name,
            'overwrite': str(overwrite).lower()
        }

        response = requests.post(
            url,
            params=params,
            headers=self.session.get_auth_header(),
            proxies=self.session.proxies)
        response.raise_for_status()

        job_info = response.json()
        result = job_info['jobId']
        return result

    def ping(self):
        url_path = "/dictionary/docs/"
        url = urllib.parse.urljoin(self.service_base_url, url_path)
        response = requests.get(
            url,
            proxies=self.session.proxies)

        if response.ok:
            logging.info(f"Dictionary service connectivity test to '{self.service_base_url}' - PASSED")
            return True
        else:
            logging.error(
                f"Dictionary service connectivity test to '{self.service_base_url}' - FAILED. "
                f"Status code: {response.status_code}; Reason: {response.reason}")
            return False
