import json
import time
import logging
from typing import Dict, Any
from his_client import HISClient
from pax_client import PAXClient


class Middleware:
    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.his_client = HISClient(self.config.get('his', {}))
        self.pax_client = PAXClient(self.config.get('pax', {}))
        self.max_retries = self.config.get('sync', {}).get('max_retries', 3)
        self.retry_delay = self.config.get('sync', {}).get('retry_delay', 5)
        self.interval = self.config.get('sync', {}).get('interval_seconds', 60)

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
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

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

    def sync_data(self, data_type: str = 'exams'):
        self.logger.info(f"开始同步 {data_type} 数据...")
        
        his_data = self._retry_on_failure(self.his_client.fetch_data, data_type)
        if not his_data:
            self.logger.error(f"从 HIS 系统获取 {data_type} 数据失败")
            return False
        
        self.logger.info(f"从 HIS 成功获取数据: {his_data}")
        
        success = self._process_and_send(his_data, data_type)
        
        if success:
            self.logger.info(f"{data_type} 数据同步完成")
        else:
            self.logger.error(f"{data_type} 数据同步失败")
        
        return success

    def _process_and_send(self, data: Dict[str, Any], data_type: str) -> bool:
        items = data.get('items', [data]) if isinstance(data, dict) else data
        
        all_success = True
        for item in items:
            result = self._retry_on_failure(self.pax_client.send_data, item, data_type)
            if result:
                self.logger.info(f"成功发送数据到 PAX: {result}")
            else:
                self.logger.error(f"发送数据到 PAX 失败: {item}")
                all_success = False
        
        return all_success

    def run_continuous(self):
        self.logger.info("中间件服务已启动，持续同步中...")
        try:
            while True:
                self.sync_data('exams')
                self.sync_data('patients')
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.logger.info("中间件服务已停止")


if __name__ == "__main__":
    middleware = Middleware()
    middleware.run_continuous()
