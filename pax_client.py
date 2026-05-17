import requests
import json
from typing import Dict, Any, Optional


class PAXClient:
    def __init__(self, config: Dict[str, Any]):
        self.api_url = config.get('api_url', '')
        self.api_key = config.get('api_key', '')
        self.timeout = config.get('timeout', 30)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })

    def send_patient(self, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.api_url}/patients"
            response = self.session.post(url, json=patient_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PAX 发送患者数据失败: {e}")
            return None

    def send_exam(self, exam_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.api_url}/exams"
            response = self.session.post(url, json=exam_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PAX 发送检查数据失败: {e}")
            return None

    def send_data(self, data: Dict[str, Any], data_type: str = 'exams') -> Optional[Dict[str, Any]]:
        if data_type == 'patients':
            return self.send_patient(data)
        elif data_type == 'exams':
            return self.send_exam(data)
        else:
            print(f"未知的数据类型: {data_type}")
            return None
