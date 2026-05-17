using System;
using System.IO;

namespace HRVMiddleware.Services
{
    public class LogService
    {
        private readonly string _logFilePath;
        private readonly object _lock = new object();

        public LogService(string logFilePath)
        {
            _logFilePath = logFilePath;
            EnsureDirectoryExists();
        }

        private void EnsureDirectoryExists()
        {
            string directory = Path.GetDirectoryName(_logFilePath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }
        }

        public void Info(string message)
        {
            WriteLog("INFO", message);
        }

        public void Warning(string message)
        {
            WriteLog("WARNING", message);
        }

        public void Error(string message, Exception ex = null)
        {
            string fullMessage = message;
            if (ex != null)
            {
                fullMessage += " - " + ex.ToString();
            }
            WriteLog("ERROR", fullMessage);
        }

        private void WriteLog(string level, string message)
        {
            lock (_lock)
            {
                try
                {
                    string logEntry = string.Format("{0:yyyy-MM-dd HH:mm:ss} [{1}] {2}", 
                        DateTime.Now, level, message);
                    
                    Console.WriteLine(logEntry);
                    
                    using (StreamWriter writer = new StreamWriter(_logFilePath, true))
                    {
                        writer.WriteLine(logEntry);
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine("日志写入失败: " + ex.Message);
                }
            }
        }
    }
}
