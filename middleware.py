import json
import time
import logging
import os
import base64
from typing import Dict, Any
from datetime import datetime
from his_client import HISClient
from hrv_client import HRVClient


class Middleware:
    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_report_path()
        self.his_client = HISClient(self.config.get('his', {}))
        self.hrv_client = HRVClient(self.config.get('hrv', {}))
        self.max_retries = self.config.get('sync', {}).get('max_retries', 3)
        self.retry_delay = self.config.get('sync', {}).get('retry_delay', 5)
        self.interval = self.config.get('sync', {}).get('interval_seconds', 60)
        self.report_save_path = self.config.get('sync', {}).get('report_save_path', './reports')
        self.report_format = self.config.get('sync', {}).get('report_format', 'PDF')

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}

    def _setup_logging(self):
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'app.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _setup_report_path(self):
        if not os.path.exists(self.report_save_path):
            os.makedirs(self.report_save_path)
            self.logger.info(f"创建报告保存目录: {self.report_save_path}")

    def _retry_on_failure(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                self.logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        return None

    def convert_his_patient_to_hrv(self, his_patient: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'caseNo': his_patient.get('caseNo', his_patient.get('身份证号', '')),
            '姓名': his_patient.get('姓名', his_patient.get('name', '')),
            '性别': his_patient.get('性别', his_patient.get('gender', '')),
            '出生日期': his_patient.get('出生日期', his_patient.get('birthDate', '')),
            '身高': his_patient.get('身高', his_patient.get('height', 0)),
            '体重': his_patient.get('体重', his_patient.get('weight', 0)),
            '运动等级': his_patient.get('运动等级', his_patient.get('sportLevel', 1))
        }

    def sync_patients_to_hrv(self) -> bool:
        self.logger.info("开始同步患者到HRV系统...")
        
        his_patients = self._retry_on_failure(self.his_client.get_patients_from_db)
        if not his_patients:
            self.logger.warning("未从HIS获取到患者数据")
            return True
        
        patients = his_patients.get('items', [his_patients]) if isinstance(his_patients, dict) else his_patients
        success_count = 0
        
        for patient in patients:
            hrv_patient = self.convert_his_patient_to_hrv(patient)
            if not hrv_patient.get('caseNo'):
                self.logger.warning(f"患者缺少caseNo，跳过: {patient}")
                continue
            
            result = self._retry_on_failure(self.hrv_client.create_patient, hrv_patient)
            if result:
                self.logger.info(f"成功同步患者到HRV: {hrv_patient.get('caseNo')}")
                success_count += 1
            else:
                self.logger.error(f"同步患者到HRV失败: {hrv_patient.get('caseNo')}")
        
        self.logger.info(f"患者同步完成，成功: {success_count}/{len(patients)}")
        return True

    def fetch_and_save_hrv_results(self) -> bool:
        self.logger.info("开始获取HRV检测结果...")
        
        records = self._retry_on_failure(self.hrv_client.get_measurement_record_list)
        if not records:
            self.logger.warning("未获取到HRV检测记录")
            return True
        
        self.logger.info(f"获取到HRV检测记录: {records}")
        
        items = records.get('items', [records]) if isinstance(records, dict) else records
        success_count = 0
        
        for item in items:
            case_no = item.get('caseNo')
            if not case_no:
                continue
            
            parameters = self._retry_on_failure(self.hrv_client.get_measurement_parameters, case_no)
            if parameters:
                self.logger.info(f"获取到检测结果: {case_no}")
                self._save_parameters(case_no, parameters)
            
            report_bytes = self._retry_on_failure(self.hrv_client.get_report_bytes, case_no, self.report_format)
            if report_bytes:
                self.logger.info(f"获取到报告: {case_no}")
                self._save_report(case_no, report_bytes)
                success_count += 1
        
        self.logger.info(f"检测结果获取完成，成功: {success_count}")
        return True

    def _save_parameters(self, case_no: str, parameters: Dict[str, Any]):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.report_save_path, f"{case_no}_{timestamp}_parameters.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(parameters, f, ensure_ascii=False, indent=2)
            self.logger.info(f"检测参数已保存: {file_path}")
        except Exception as e:
            self.logger.error(f"保存检测参数失败: {e}")

    def _save_report(self, case_no: str, report_bytes: bytes):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = self.report_format.lower()
            if ext == 'jpg':
                ext = 'zip'
            file_path = os.path.join(self.report_save_path, f"{case_no}_{timestamp}.{ext}")
            with open(file_path, 'wb') as f:
                f.write(report_bytes)
            self.logger.info(f"报告已保存: {file_path}")
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")

    def run_sync_cycle(self):
        self.logger.info("=== 开始同步周期 ===")
        
        try:
            self.sync_patients_to_hrv()
            time.sleep(2)
            self.fetch_and_save_hrv_results()
            self.logger.info("=== 同步周期完成 ===")
        except Exception as e:
            self.logger.error(f"同步周期异常: {e}")

    def run_continuous(self):
        self.logger.info("HRV中间件服务已启动，持续同步中...")
        try:
            while True:
                self.run_sync_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.logger.info("HRV中间件服务已停止")


if __name__ == "__main__":
    middleware = Middleware()
    middleware.run_continuous()
