using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Web.Script.Serialization;

namespace HRVMiddleware.Services
{
    public class HISDatabaseService
    {
        private readonly string _connectionString;
        private readonly LogService _logger;
        private readonly JavaScriptSerializer _serializer;

        public HISDatabaseService(string connectionString, LogService logger)
        {
            _connectionString = connectionString;
            _logger = logger;
            _serializer = new JavaScriptSerializer();
        }

        public List<Models.Patient> GetPatients()
        {
            List<Models.Patient> patients = new List<Models.Patient>();

            try
            {
                using (SqlConnection conn = new SqlConnection(_connectionString))
                {
                    conn.Open();
                    
                    // TODO: 根据实际的HIS数据库表结构修改这个SQL语句
                    string sql = @"
                        SELECT 
                            身份证号 as caseNo,
                            姓名,
                            性别,
                            出生日期,
                            身高,
                            体重,
                            运动等级
                        FROM 你的患者表
                        WHERE 身份证号 IS NOT NULL 
                          AND 姓名 IS NOT NULL
                        ORDER BY 创建时间 DESC";

                    using (SqlCommand cmd = new SqlCommand(sql, conn))
                    using (SqlDataReader reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            Models.Patient patient = new Models.Patient();
                            patient.caseNo = reader["caseNo"].ToString();
                            patient.姓名 = reader["姓名"].ToString();
                            patient.性别 = reader["性别"].ToString();
                            patient.出生日期 = reader["出生日期"].ToString();
                            patient.身高 = Convert.ToInt32(reader["身高"] ?? 0);
                            patient.体重 = Convert.ToInt32(reader["体重"] ?? 0);
                            patient.运动等级 = Convert.ToInt32(reader["运动等级"] ?? 1);
                            
                            patients.Add(patient);
                        }
                    }
                }

                _logger.Info(string.Format("从HIS获取到 {0} 个患者", patients.Count));
            }
            catch (Exception ex)
            {
                _logger.Error("从HIS数据库获取患者失败", ex);
            }

            return patients;
        }

        public bool MarkPatientAsSynced(string caseNo)
        {
            try
            {
                using (SqlConnection conn = new SqlConnection(_connectionString))
                {
                    conn.Open();
                    
                    // TODO: 如果需要标记已同步的患者，可以在HIS数据库创建一个同步记录表
                    // 或者在这里实现相应的逻辑
                    // 暂时先不实现，因为可能没有权限修改HIS数据库
                }
                return true;
            }
            catch (Exception ex)
            {
                _logger.Error("标记患者同步状态失败", ex);
                return false;
            }
        }
    }
}
