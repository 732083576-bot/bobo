import requests
import pyodbc
from typing import Dict, Any, Optional, List


class HISClient:
    def __init__(self, config: Dict[str, Any]):
        self.use_database = config.get('use_database', False)
        self.api_url = config.get('api_url', '')
        self.api_key = config.get('api_key', '')
        self.timeout = config.get('timeout', 30)
        self.database_config = config.get('database', {})
        
        if self.use_database:
            self.connection = None
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            })

    def _get_db_connection(self) -> Optional[pyodbc.Connection]:
        try:
            conn_str = (
                f"DRIVER={{{self.database_config.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
                f"SERVER={self.database_config.get('server', '')};"
                f"DATABASE={self.database_config.get('database', '')};"
                f"UID={self.database_config.get('username', '')};"
                f"PWD={self.database_config.get('password', '')};"
            )
            return pyodbc.connect(conn_str)
        except Exception as e:
            print(f"连接 SQL Server 数据库失败: {e}")
            return None

    def _execute_query(self, query: str, params: tuple = ()) -> Optional[List[Dict[str, Any]]]:
        try:
            conn = self._get_db_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            conn.close()
            return results
        except Exception as e:
            print(f"执行 SQL 查询失败: {e}")
            return None

    def get_patients_from_db(self) -> Optional[Dict[str, Any]]:
        try:
            query = "SELECT * FROM Patients WHERE IsSynced = 0 OR IsSynced IS NULL"
            results = self._execute_query(query)
            if results is not None:
                return {"items": results}
            return None
        except Exception as e:
            print(f"从数据库获取患者数据失败: {e}")
            return None

    def get_exams_from_db(self, patient_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            if patient_id:
                query = "SELECT * FROM Exams WHERE PatientID = ? AND (IsSynced = 0 OR IsSynced IS NULL)"
                results = self._execute_query(query, (patient_id,))
            else:
                query = "SELECT * FROM Exams WHERE IsSynced = 0 OR IsSynced IS NULL"
                results = self._execute_query(query)
            
            if results is not None:
                return {"items": results}
            return None
        except Exception as e:
            print(f"从数据库获取检查数据失败: {e}")
            return None

    def mark_as_synced(self, table: str, record_id: int) -> bool:
        try:
            query = f"UPDATE {table} SET IsSynced = 1 WHERE ID = ?"
            conn = self._get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute(query, (record_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"标记已同步失败: {e}")
            return False

    def get_patients(self) -> Optional[Dict[str, Any]]:
        if self.use_database:
            return self.get_patients_from_db()
        try:
            url = f"{self.api_url}/patients"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"HIS 获取患者数据失败: {e}")
            return None

    def get_exams(self, patient_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if self.use_database:
            return self.get_exams_from_db(patient_id)
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
