import requests
import json
import base64
from typing import Dict, Any, Optional, List


class HRVClient:
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get('base_url', 'http://localhost:8080')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.auth_mode = config.get('auth_mode', 'password')
        self.timeout = config.get('timeout', 30)
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def get_access_token(self) -> Optional[str]:
        try:
            url = f"{self.base_url}/api/public/access-token"
            if self.auth_mode == 'password':
                params = {
                    'username': self.username,
                    'password': self.password
                }
            else:
                params = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            self.token = response.text.strip()
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            return self.token
        except Exception as e:
            print(f"获取HRV access token失败: {e}")
            return None

    def ensure_token(self) -> bool:
        if not self.token:
            return self.get_access_token() is not None
        return True

    def create_patient(self, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/sync-patients"
            response = self.session.post(url, json=patient_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"创建/更新HRV患者失败: {e}")
            if '401' in str(e):
                self.token = None
            return None

    def get_measurement_record_list(self, filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/measurement-record-list"
            params = filters or {}
            if 'excludeStatuses' not in params:
                params['excludeStatuses'] = ['CANCELED']
            
            response = self.session.post(url, json=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取HRV检测记录列表失败: {e}")
            if '401' in str(e):
                self.token = None
            return None

    def get_measurement_parameters(self, case_no: str, exam_type: str = 'HRV健康评估') -> Optional[Dict[str, Any]]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/parameters"
            data = {
                'caseNo': case_no,
                'examType': exam_type
            }
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取HRV检测结果失败: {e}")
            if '401' in str(e):
                self.token = None
            return None

    def get_report_bytes(self, case_no: str, report_type: str = 'PDF') -> Optional[bytes]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/report-bytes"
            data = {
                'caseNo': case_no,
                'reportType': report_type
            }
            response = self.session.post(url, json=data, timeout=self.timeout * 2)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"获取HRV报告字节流失败: {e}")
            if '401' in str(e):
                self.token = None
            return None

    def get_report_base64(self, case_no: str, report_type: str = 'PDF', split_report: bool = False) -> Optional[Dict[str, Any]]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/report-base64"
            data = {
                'caseNo': case_no,
                'reportType': report_type,
                'splitReport': split_report
            }
            response = self.session.post(url, json=data, timeout=self.timeout * 2)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取HRV报告Base64失败: {e}")
            if '401' in str(e):
                self.token = None
            return None

    def delete_patient(self, case_no: str) -> Optional[Dict[str, Any]]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/delete-patient"
            data = {'caseNo': case_no}
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"删除HRV患者失败: {e}")
            if '401' in str(e):
                self.token = None
            return None

    def get_patient_list(self, filters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/patient-list"
            response = self.session.post(url, json=filters or {}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取HRV患者列表失败: {e}")
            if '401' in str(e):
                self.token = None
            return None

    def get_department_list(self) -> Optional[Dict[str, Any]]:
        try:
            if not self.ensure_token():
                return None
            
            url = f"{self.base_url}/services/reporting/api/third-party/subscribe/department-list"
            response = self.session.post(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取HRV科室列表失败: {e}")
            if '401' in str(e):
                self.token = None
            return None
