import requests
import urllib.parse
import logging
import json
from api_client.security import Session

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s\t%(asctime)s\t%(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)


class ProjectServiceClient(object):
    def __init__(self, session: Session, service_base_url):
        self.session = session
        self.service_base_url = service_base_url

    def run_analysis(self, analysis_id, with_attr = None):
        if with_attr:
            url_path = f'/project/v1/analyses/{analysis_id}/jobs?withAttribution=true'
        else:
            url_path = f'/project/v1/analyses/{analysis_id}/jobs'
        url = urllib.parse.urljoin(self.service_base_url, url_path)
        logging.info(f'now making run analysis call with url: {url}')
        response = requests.post(url, headers=self.session.get_auth_header(), proxies=self.session.proxies)
        response.raise_for_status()

        job_info = response.json()
        result = job_info['jobId']
        return result
    
    def duplicate_analysis(self, analysis_id, payload):
        url_path = f'/project/v1/analysis/{analysis_id}/duplicate'
        url = urllib.parse.urljoin(self.service_base_url, url_path)

        headers = self.session.get_auth_header()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        response = requests.post(url, headers=headers, proxies=self.session.proxies, data=json.dumps(payload))
        response.raise_for_status() 
        return response.json()

    def get_analysis_scenarios(self, analysis_id: int) -> list:
        url_path = f'/project/1.0/analyses/{analysis_id}/scenarios'
        url = urllib.parse.urljoin(self.service_base_url, url_path)
        response = requests.get(url, headers=self.session.get_auth_header(), proxies=self.session.proxies)
        response.raise_for_status() 
        return response.json()

    def ping(self):
        url_path = "/project/docs/"
        url = urllib.parse.urljoin(self.service_base_url, url_path)
        response = requests.get(
            url,
            proxies=self.session.proxies)

        if response.ok:
            logging.info(f"Project service connectivity test to '{self.service_base_url}' - PASSED")
            return True
        else:
            logging.error(
                f"Project service connectivity test to '{self.service_base_url}' - FAILED. "
                f"Status code: {response.status_code}; Reason: {response.reason}")
            return False
