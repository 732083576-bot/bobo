using System;
using System.IO;
using System.Text;

namespace HRVMiddleware.Services
{
    public class FileService
    {
        private readonly string _reportSavePath;
        private readonly LogService _logger;

        public FileService(string reportSavePath, LogService logger)
        {
            _reportSavePath = reportSavePath;
            _logger = logger;
            EnsureDirectoryExists();
        }

        private void EnsureDirectoryExists()
        {
            if (!Directory.Exists(_reportSavePath))
            {
                Directory.CreateDirectory(_reportSavePath);
                _logger.Info("创建报告保存目录: " + _reportSavePath);
            }
        }

        public string SaveReportBytes(string caseNo, byte[] reportData, string format)
        {
            try
            {
                string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string extension = format.ToLower();
                if (extension == "jpg") extension = "zip";
                
                string fileName = string.Format("{0}_{1}.{2}", caseNo, timestamp, extension);
                string filePath = Path.Combine(_reportSavePath, fileName);
                
                File.WriteAllBytes(filePath, reportData);
                _logger.Info("报告已保存: " + filePath);
                return filePath;
            }
            catch (Exception ex)
            {
                _logger.Error("保存报告失败", ex);
                return null;
            }
        }

        public string SaveParameters(string caseNo, string parametersJson)
        {
            try
            {
                string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string fileName = string.Format("{0}_{1}_parameters.json", caseNo, timestamp);
                string filePath = Path.Combine(_reportSavePath, fileName);
                
                File.WriteAllText(filePath, parametersJson, Encoding.UTF8);
                _logger.Info("检测参数已保存: " + filePath);
                return filePath;
            }
            catch (Exception ex)
            {
                _logger.Error("保存检测参数失败", ex);
                return null;
            }
        }
    }
}
