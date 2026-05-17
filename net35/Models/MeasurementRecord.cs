using System;

namespace HRVMiddleware.Models
{
    public class MeasurementRecord
    {
        public string caseNo { get; set; }
        public string patientName { get; set; }
        public DateTime measurementTime { get; set; }
        public string status { get; set; }
    }
}
