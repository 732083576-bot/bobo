using System;
using System.IO;
using System.Net;
using System.Text;
using System.Web.Script.Serialization;

namespace HRVMiddleware.Services
{
    public class HRVService
    {
        private readonly string _baseUrl;
        private readonly string _username;
        private readonly string _password;
        private readonly string _authMode;
        private readonly LogService _logger;
        private string _token;
        private readonly JavaScriptSerializer _serializer;

        public HRVService(string baseUrl, string username, string password, string authMode, LogService logger)
        {
            _baseUrl = baseUrl;
            _username = username;
            _password = password;
            _authMode = authMode;
            _logger = logger;
            _serializer = new JavaScriptSerializer();
        }

        public bool GetAccessToken()
        {
            try
            {
                string url = _baseUrl + "/api/public/access-token";
                string paramString;

                if (_authMode == "password")
                {
                    paramString = string.Format("username={0}&password={1}", 
                        Uri.EscapeDataString(_username), 
                        Uri.EscapeDataString(_password));
                }
                else
                {
                    paramString = string.Format("client_id={0}&client_secret={1}", 
                        Uri.EscapeDataString(_username), 
                        Uri.EscapeDataString(_password));
                }

                url += "?" + paramString;

                HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
                request.Method = "GET";
                request.Timeout = 30000;

                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                {
                    _token = reader.ReadToEnd().Trim();
                    _logger.Info("获取HRV Access Token成功");
                    return true;
                }
            }
            catch (Exception ex)
            {
                _logger.Error("获取HRV Access Token失败", ex);
                _token = null;
                return false;
            }
        }

        private bool EnsureToken()
        {
            if (string.IsNullOrEmpty(_token))
            {
                return GetAccessToken();
            }
            return true;
        }

        public bool CreatePatient(Models.Patient patient)
        {
            for (int i = 0; i < 3; i++)
            {
                try
                {
                    if (!EnsureToken()) return false;

                    string url = _baseUrl + "/services/reporting/api/third-party/subscribe/sync-patients";
                    string json = _serializer.Serialize(patient);

                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
                    request.Method = "POST";
                    request.ContentType = "application/json";
                    request.Headers["Authorization"] = "Bearer " + _token;
                    request.Timeout = 30000;

                    byte[] data = Encoding.UTF8.GetBytes(json);
                    request.ContentLength = data.Length;

                    using (Stream stream = request.GetRequestStream())
                    {
                        stream.Write(data, 0, data.Length);
                    }

                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                    {
                        string result = reader.ReadToEnd();
                        _logger.Info("同步患者成功: " + patient.caseNo);
                        return true;
                    }
                }
                catch (WebException ex)
                {
                    if (ex.Response != null)
                    {
                        HttpWebResponse response = (HttpWebResponse)ex.Response;
                        if (response.StatusCode == HttpStatusCode.Unauthorized)
                        {
                            _logger.Warning("Token失效，重新获取");
                            _token = null;
                            continue;
                        }
                    }
                    _logger.Error("同步患者失败: " + patient.caseNo, ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
                catch (Exception ex)
                {
                    _logger.Error("同步患者失败: " + patient.caseNo, ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
            }
            return false;
        }

        public string GetMeasurementRecordList()
        {
            for (int i = 0; i < 3; i++)
            {
                try
                {
                    if (!EnsureToken()) return null;

                    string url = _baseUrl + "/services/reporting/api/third-party/subscribe/measurement-record-list";
                    string json = "{\"excludeStatuses\":[\"CANCELED\"]}";

                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
                    request.Method = "POST";
                    request.ContentType = "application/json";
                    request.Headers["Authorization"] = "Bearer " + _token;
                    request.Timeout = 30000;

                    byte[] data = Encoding.UTF8.GetBytes(json);
                    request.ContentLength = data.Length;

                    using (Stream stream = request.GetRequestStream())
                    {
                        stream.Write(data, 0, data.Length);
                    }

                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                    {
                        string result = reader.ReadToEnd();
                        _logger.Info("获取检测记录列表成功");
                        return result;
                    }
                }
                catch (WebException ex)
                {
                    if (ex.Response != null)
                    {
                        HttpWebResponse response = (HttpWebResponse)ex.Response;
                        if (response.StatusCode == HttpStatusCode.Unauthorized)
                        {
                            _logger.Warning("Token失效，重新获取");
                            _token = null;
                            continue;
                        }
                    }
                    _logger.Error("获取检测记录列表失败", ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
                catch (Exception ex)
                {
                    _logger.Error("获取检测记录列表失败", ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
            }
            return null;
        }

        public string GetMeasurementParameters(string caseNo, string examType = "HRV健康评估")
        {
            for (int i = 0; i < 3; i++)
            {
                try
                {
                    if (!EnsureToken()) return null;

                    string url = _baseUrl + "/services/reporting/api/third-party/subscribe/parameters";
                    var requestData = new { caseNo = caseNo, examType = examType };
                    string json = _serializer.Serialize(requestData);

                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
                    request.Method = "POST";
                    request.ContentType = "application/json";
                    request.Headers["Authorization"] = "Bearer " + _token;
                    request.Timeout = 30000;

                    byte[] data = Encoding.UTF8.GetBytes(json);
                    request.ContentLength = data.Length;

                    using (Stream stream = request.GetRequestStream())
                    {
                        stream.Write(data, 0, data.Length);
                    }

                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    using (StreamReader reader = new StreamReader(response.GetResponseStream()))
                    {
                        string result = reader.ReadToEnd();
                        _logger.Info("获取检测参数成功: " + caseNo);
                        return result;
                    }
                }
                catch (WebException ex)
                {
                    if (ex.Response != null)
                    {
                        HttpWebResponse response = (HttpWebResponse)ex.Response;
                        if (response.StatusCode == HttpStatusCode.Unauthorized)
                        {
                            _logger.Warning("Token失效，重新获取");
                            _token = null;
                            continue;
                        }
                    }
                    _logger.Error("获取检测参数失败: " + caseNo, ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
                catch (Exception ex)
                {
                    _logger.Error("获取检测参数失败: " + caseNo, ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
            }
            return null;
        }

        public byte[] GetReportBytes(string caseNo, string reportFormat = "PDF")
        {
            for (int i = 0; i < 3; i++)
            {
                try
                {
                    if (!EnsureToken()) return null;

                    string url = _baseUrl + "/services/reporting/api/third-party/subscribe/report-bytes";
                    var requestData = new { caseNo = caseNo, reportType = reportFormat };
                    string json = _serializer.Serialize(requestData);

                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
                    request.Method = "POST";
                    request.ContentType = "application/json";
                    request.Headers["Authorization"] = "Bearer " + _token;
                    request.Timeout = 60000;

                    byte[] data = Encoding.UTF8.GetBytes(json);
                    request.ContentLength = data.Length;

                    using (Stream stream = request.GetRequestStream())
                    {
                        stream.Write(data, 0, data.Length);
                    }

                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    using (Stream responseStream = response.GetResponseStream())
                    using (MemoryStream ms = new MemoryStream())
                    {
                        byte[] buffer = new byte[4096];
                        int bytesRead;
                        while ((bytesRead = responseStream.Read(buffer, 0, buffer.Length)) > 0)
                        {
                            ms.Write(buffer, 0, bytesRead);
                        }
                        _logger.Info("获取报告成功: " + caseNo);
                        return ms.ToArray();
                    }
                }
                catch (WebException ex)
                {
                    if (ex.Response != null)
                    {
                        HttpWebResponse response = (HttpWebResponse)ex.Response;
                        if (response.StatusCode == HttpStatusCode.Unauthorized)
                        {
                            _logger.Warning("Token失效，重新获取");
                            _token = null;
                            continue;
                        }
                    }
                    _logger.Error("获取报告失败: " + caseNo, ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
                catch (Exception ex)
                {
                    _logger.Error("获取报告失败: " + caseNo, ex);
                    if (i < 2) System.Threading.Thread.Sleep(5000);
                }
            }
            return null;
        }
    }
}
