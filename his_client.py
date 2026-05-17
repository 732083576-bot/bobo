import requests
import json
from typing import Dict, Any, Optional


class HISClient:
    def __init__(self, config: Dict[str, Any]):
        self.api_url = config.get('api_url', '')
        self.api_key = config.get('api_key', '')
        self.timeout = config.get('timeout', 30)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })

    def get_patients(self) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.api_url}/patients"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"HIS 获取患者数据失败: {e}")
            return None

    def get_exams(self, patient_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.api_url}/exams"
            params = {}
            if patient_id:
                params['patient_id'] = patient_id
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"HIS 获取检查数据失败: {e}")
            return None

    def fetch_data(self, data_type: str = 'exams') -> Optional[Dict[str, Any]]:
        if data_type == 'patients':
            return self.get_patients()
        elif data_type == 'exams':
            return self.get_exams()
        else:
            print(f"未知的数据类型: {data_type}")
            return None
