using System;
using System.Collections.Generic;
using System.Configuration;
using System.Threading;
using System.Web.Script.Serialization;

namespace HRVMiddleware
{
    class Program
    {
        private static LogService _logger;
        private static HRVService _hrvService;
        private static HISDatabaseService _hisService;
        private static FileService _fileService;
        private static string _reportFormat;
        private static int _syncInterval;
        private static JavaScriptSerializer _serializer;

        static void Main(string[] args)
        {
            Console.WriteLine("========================================");
            Console.WriteLine("  HRV中间件程序 - .NET 3.5");
            Console.WriteLine("========================================");
            Console.WriteLine();

            InitializeServices();

            Console.WriteLine("按任意键开始定时同步...");
            Console.ReadKey();

            Console.WriteLine();
            _logger.Info("HRV中间件服务已启动，定时同步中...");
            Console.WriteLine("按 Ctrl+C 停止服务");
            Console.WriteLine();

            try
            {
                while (true)
                {
                    RunSyncCycle();
                    Thread.Sleep(_syncInterval * 1000);
                }
            }
            catch (Exception ex)
            {
                _logger.Error("程序异常退出", ex);
            }
        }

        private static void InitializeServices()
        {
            try
            {
                string logFilePath = ConfigurationManager.AppSettings["LogFilePath"];
                _logger = new LogService(logFilePath);

                string hrvBaseUrl = ConfigurationManager.AppSettings["HRVBaseUrl"];
                string hrvUsername = ConfigurationManager.AppSettings["HRVUsername"];
                string hrvPassword = ConfigurationManager.AppSettings["HRVPassword"];
                string hrvAuthMode = ConfigurationManager.AppSettings["HRVAuthMode"];
                _hrvService = new HRVService(hrvBaseUrl, hrvUsername, hrvPassword, hrvAuthMode, _logger);

                string connectionString = ConfigurationManager.ConnectionStrings["HISDatabase"].ConnectionString;
                _hisService = new HISDatabaseService(connectionString, _logger);

                string reportSavePath = ConfigurationManager.AppSettings["ReportSavePath"];
                _fileService = new FileService(reportSavePath, _logger);

                _reportFormat = ConfigurationManager.AppSettings["ReportFormat"];
                _syncInterval = int.Parse(ConfigurationManager.AppSettings["SyncIntervalSeconds"]);
                _serializer = new JavaScriptSerializer();

                _logger.Info("服务初始化完成");
            }
            catch (Exception ex)
            {
                Console.WriteLine("初始化服务失败: " + ex.Message);
                Console.WriteLine("请检查 App.config 配置文件是否正确");
                Console.ReadKey();
                Environment.Exit(1);
            }
        }

        private static void RunSyncCycle()
        {
            _logger.Info("=== 开始同步周期 ===");

            try
            {
                SyncPatients();
                Thread.Sleep(2000);
                FetchHRVResults();
            }
            catch (Exception ex)
            {
                _logger.Error("同步周期异常", ex);
            }

            _logger.Info("=== 同步周期完成 ===");
            Console.WriteLine();
        }

        private static void SyncPatients()
        {
            _logger.Info("开始同步患者到HRV系统...");

            List<Models.Patient> patients = _hisService.GetPatients();
            if (patients.Count == 0)
            {
                _logger.Warning("没有获取到患者数据");
                return;
            }

            int successCount = 0;
            foreach (Models.Patient patient in patients)
            {
                if (string.IsNullOrEmpty(patient.caseNo))
                {
                    _logger.Warning("患者缺少caseNo，跳过");
                    continue;
                }

                bool success = _hrvService.CreatePatient(patient);
                if (success)
                {
                    successCount++;
                }
            }

            _logger.Info(string.Format("患者同步完成，成功: {0}/{1}", successCount, patients.Count));
        }

        private static void FetchHRVResults()
        {
            _logger.Info("开始获取HRV检测结果...");

            string recordsJson = _hrvService.GetMeasurementRecordList();
            if (string.IsNullOrEmpty(recordsJson))
            {
                _logger.Warning("没有获取到检测记录");
                return;
            }

            try
            {
                dynamic recordsData = _serializer.DeserializeObject(recordsJson);
                List<dynamic> items = new List<dynamic>();

                if (recordsData is Dictionary<string, object>)
                {
                    var dict = (Dictionary<string, object>)recordsData;
                    if (dict.ContainsKey("items"))
                    {
                        items = (List<dynamic>)dict["items"];
                    }
                    else
                    {
                        items.Add(recordsData);
                    }
                }
                else if (recordsData is List<object>)
                {
                    items = (List<dynamic>)recordsData;
                }

                if (items.Count == 0)
                {
                    _logger.Warning("没有检测记录");
                    return;
                }

                int successCount = 0;
                foreach (var item in items)
                {
                    string caseNo = null;
                    if (item is Dictionary<string, object>)
                    {
                        var itemDict = (Dictionary<string, object>)item;
                        if (itemDict.ContainsKey("caseNo"))
                        {
                            caseNo = itemDict["caseNo"].ToString();
                        }
                    }

                    if (string.IsNullOrEmpty(caseNo))
                    {
                        continue;
                    }

                    string parameters = _hrvService.GetMeasurementParameters(caseNo);
                    if (!string.IsNullOrEmpty(parameters))
                    {
                        _fileService.SaveParameters(caseNo, parameters);
                    }

                    byte[] report = _hrvService.GetReportBytes(caseNo, _reportFormat);
                    if (report != null && report.Length > 0)
                    {
                        _fileService.SaveReportBytes(caseNo, report, _reportFormat);
                        successCount++;
                    }
                }

                _logger.Info(string.Format("检测结果获取完成，成功: {0}", successCount));
            }
            catch (Exception ex)
            {
                _logger.Error("处理检测记录失败", ex);
            }
        }
    }
}
